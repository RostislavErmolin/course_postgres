from dataclasses import dataclass
from decimal import Decimal
from datetime import datetime

from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.shortcuts import radiolist_dialog
from psycopg.rows import class_row
from rich.panel import Panel
from rich.table import Table

from auth import ROLE_SALES_MANAGER, auth_user
from console import console, render_error
from db import get_conn
from validators import NonEmptyValidator, YesNoValidator, ChoiceValidator
from commands import command, CATEGORY_ORDERS

_SALES_ONLY = [ROLE_SALES_MANAGER]


@dataclass
class Order:
    id: int
    status: str
    total_amount: Decimal
    created_at: datetime
    warehouse_id: int
    created_by: int


@dataclass
class OrderItem:
    id: int
    order_id: int
    product_id: int
    price: Decimal
    quantity: int


STATUS_LABELS = {
    "unpublished": "Черновик",
    "new": "Новый",
    "processing": "В обработке",
    "pending": "Ожидает",
    "packing": "Комплектация",
    "shipped": "Отгружен",
}


def _is_editable(order: Order) -> bool:
    return order.status == "unpublished"


def _recalculate_total(conn, order_id: int) -> None:
    conn.execute(
        """UPDATE sales.orders
        SET total_amount = COALESCE(
            (SELECT SUM(price * quantity) FROM sales.order_items WHERE order_id = %s), 0
        )
        WHERE id = %s""",
        (order_id, order_id),
    )


def _get_order(conn, order_id: str) -> Order | None:
    with conn.cursor(row_factory=class_row(Order)) as cur:
        cur.execute("SELECT * FROM sales.orders WHERE id = %s", (order_id,))
        return cur.fetchone()


def _get_username(conn, user_id: int) -> str:
    with conn.cursor() as cur:
        cur.execute("SELECT username FROM auth.users WHERE id = %s", (user_id,))
        row = cur.fetchone()
        return row[0] if row else str(user_id)


def _get_warehouse_label(conn, warehouse_id: int) -> str:
    with conn.cursor() as cur:
        cur.execute("SELECT city, label FROM catalog.warehouses WHERE id = %s", (warehouse_id,))
        row = cur.fetchone()
        if row:
            return f"{row[0]}{f' ({row[1]})' if row[1] else ''}"
        return str(warehouse_id)


def _pick_warehouse(default_id: int | None = None) -> int | None:
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, city, label FROM catalog.warehouses ORDER BY is_central DESC, city"
        )
        warehouses = cur.fetchall()

    if not warehouses:
        render_error("Нет складов. Сначала добавьте склад через 'add warehouse'.")
        return None

    values = [
        (row[0], f"{row[1]}{f' ({row[2]})' if row[2] else ''}") for row in warehouses
    ]
    default_value = default_id if default_id is not None else values[0][0]

    return radiolist_dialog(
        title="Выбор склада",
        text="Выберите склад отгрузки (стрелки + Enter):",
        values=values,
        default=default_value,
    ).run()


def _pick_product(excluded_ids: list[int]) -> tuple | None:
    conn = get_conn()
    with conn.cursor() as cur:
        if excluded_ids:
            cur.execute(
                "SELECT id, sku, name, price FROM catalog.products"
                " WHERE id != ALL(%s) ORDER BY name",
                (excluded_ids,),
            )
        else:
            cur.execute(
                "SELECT id, sku, name, price FROM catalog.products ORDER BY name"
            )
        products = cur.fetchall()

    if not products:
        render_error("Нет доступных товаров для добавления.")
        return None

    product_map = {f"{p[1]} — {p[2]}": p for p in products}
    completer = WordCompleter(list(product_map.keys()), ignore_case=True, sentence=True)
    validator = ChoiceValidator(list(product_map.keys()))

    choice = prompt(
        "Товар (SKU — Название, Tab для автодополнения): ",
        completer=completer,
        validator=validator,
    ).strip()

    return product_map[choice]


def _add_order_item_interactive(order_id: int, excluded_ids: list[int]) -> int | None:
    """Добавляет одну позицию в заказ. Возвращает product_id при успехе."""
    conn = get_conn()

    product = _pick_product(excluded_ids)
    if product is None:
        return None

    product_id, _sku, name, price = product

    quantity_str = prompt(
        f"Количество ({name}): ",
        validator=NonEmptyValidator("Введите количество"),
    ).strip()

    try:
        quantity = int(quantity_str)
        if quantity <= 0:
            render_error("Количество должно быть больше 0")
            return None
    except ValueError:
        render_error("Введите целое число")
        return None

    conn.execute(
        "INSERT INTO sales.order_items (order_id, product_id, price, quantity)"
        " VALUES (%s, %s, %s, %s)",
        (order_id, product_id, price, quantity),
    )
    _recalculate_total(conn, order_id)
    console.print(f"[green]Добавлено: {name} × {quantity} по {price:.2f} ₽[/green]")
    return product_id


def _render_order_items(order_id: int) -> None:
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute(
            """SELECT p.sku, p.name, oi.price, oi.quantity, oi.price * oi.quantity
            FROM sales.order_items oi
            JOIN catalog.products p ON p.id = oi.product_id
            WHERE oi.order_id = %s
            ORDER BY oi.id""",
            (order_id,),
        )
        items = cur.fetchall()

    if not items:
        console.print("[dim]  Нет позиций[/dim]")
        return

    table = Table(show_header=True, header_style="bold cyan", padding=(0, 2))
    table.add_column("SKU", style="green", min_width=12)
    table.add_column("Название", style="yellow", min_width=20)
    table.add_column("Цена", style="cyan", min_width=10, justify="right")
    table.add_column("Кол-во", style="white", min_width=8, justify="right")
    table.add_column("Сумма", style="bold", min_width=12, justify="right")

    for item in items:
        table.add_row(item[0], item[1], f"{item[2]:.2f} ₽", str(item[3]), f"{item[4]:.2f} ₽")

    console.print(table)


def _render_order(order: Order) -> None:
    conn = get_conn()
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Поле", style="bold cyan", width=15)
    table.add_column("Значение", style="white")

    table.add_row("ID", str(order.id))
    table.add_row("Статус", STATUS_LABELS.get(order.status, order.status))
    table.add_row("Сумма", f"{order.total_amount:.2f} ₽")
    table.add_row("Создан", order.created_at.strftime("%d.%m.%Y %H:%M"))
    table.add_row("Склад", _get_warehouse_label(conn, order.warehouse_id))
    table.add_row("Автор", _get_username(conn, order.created_by))

    panel = Panel(
        table,
        expand=False,
        title=f"[bold green]Заказ #{order.id}[/bold green]",
        border_style="green",
    )
    console.print(panel)
    _render_order_items(order.id)


@command("list orders", "список всех заказов", CATEGORY_ORDERS, _SALES_ONLY)
def list_orders() -> None:
    conn = get_conn()
    table = Table(title="Заказы", show_header=True, header_style="bold cyan")
    table.add_column("ID", style="dim", width=6, justify="right")
    table.add_column("Статус", style="green", min_width=15)
    table.add_column("Сумма", style="cyan", min_width=12, justify="right")
    table.add_column("Создан", style="yellow", min_width=18)
    table.add_column("Склад", style="magenta", min_width=20)

    with conn.cursor() as cur:
        cur.execute(
            """SELECT o.id, o.status, o.total_amount, o.created_at, w.city, w.label
            FROM sales.orders o
            JOIN catalog.warehouses w ON w.id = o.warehouse_id
            ORDER BY o.id DESC"""
        )
        rows = cur.fetchall()

    for row in rows:
        warehouse = f"{row[4]}{f' ({row[5]})' if row[5] else ''}"
        table.add_row(
            str(row[0]),
            STATUS_LABELS.get(row[1], row[1]),
            f"{row[2]:.2f} ₽",
            row[3].strftime("%d.%m.%Y %H:%M"),
            warehouse,
        )
    console.print(table)


@command("show order", "информация о заказе", CATEGORY_ORDERS, _SALES_ONLY)
def show_order(_id: str) -> None:
    conn = get_conn()
    order = _get_order(conn, _id)
    if order is None:
        render_error(f"Заказ с ID {_id} не найден")
        return
    _render_order(order)


@command("add order", "создать заказ (интерактивно)", CATEGORY_ORDERS, _SALES_ONLY)
def add_order() -> None:
    conn = get_conn()

    warehouse_id = _pick_warehouse()
    if warehouse_id is None:
        return

    user = auth_user()
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO sales.orders (warehouse_id, created_by) VALUES (%s, %s) RETURNING id",
            (warehouse_id, user.id),
        )
        row = cur.fetchone()
        assert row is not None
        order_id = row[0]

    console.print(f"[green]Заказ #{order_id} создан[/green]")

    excluded_ids: list[int] = []
    while True:
        answer = prompt("Добавить товар? (y/n, д/н): ", validator=YesNoValidator())
        if YesNoValidator.is_no(answer):
            break
        product_id = _add_order_item_interactive(order_id, excluded_ids)
        if product_id is not None:
            excluded_ids.append(product_id)


@command("edit order", "редактировать заказ", CATEGORY_ORDERS, _SALES_ONLY)
def edit_order(_id: str) -> None:
    conn = get_conn()
    order = _get_order(conn, _id)
    if order is None:
        render_error(f"Заказ с ID {_id} не найден")
        return

    if not _is_editable(order):
        render_error(f"Заказ #{_id} нельзя редактировать (статус: {order.status})")
        return

    warehouse_id = _pick_warehouse(default_id=order.warehouse_id)
    if warehouse_id is None:
        return

    conn.execute(
        "UPDATE sales.orders SET warehouse_id = %s WHERE id = %s",
        (warehouse_id, _id),
    )
    console.print(f"[green]Заказ #{_id} обновлён[/green]")


@command("delete order", "удалить заказ", CATEGORY_ORDERS, _SALES_ONLY)
def delete_order(_id: str) -> None:
    conn = get_conn()
    order = _get_order(conn, _id)
    if order is None:
        render_error(f"Заказ с ID {_id} не найден")
        return

    if not _is_editable(order):
        render_error(f"Заказ #{_id} нельзя удалить (статус: {order.status})")
        return

    _render_order(order)
    answer = prompt("Вы уверены? (y/n, д/н): ", validator=YesNoValidator())

    if YesNoValidator.is_yes(answer):
        conn.execute("DELETE FROM sales.order_items WHERE order_id = %s", (_id,))
        conn.execute("DELETE FROM sales.orders WHERE id = %s", (_id,))
        console.print(f"[green]Заказ #{_id} удалён[/green]")


@command("add order_item", "добавить товар в заказ", CATEGORY_ORDERS, _SALES_ONLY)
def add_order_item(_id: str) -> None:
    conn = get_conn()
    order = _get_order(conn, _id)
    if order is None:
        render_error(f"Заказ с ID {_id} не найден")
        return

    if not _is_editable(order):
        render_error(f"Заказ #{_id} нельзя редактировать (статус: {order.status})")
        return

    with conn.cursor() as cur:
        cur.execute(
            "SELECT product_id FROM sales.order_items WHERE order_id = %s", (_id,)
        )
        excluded_ids = [row[0] for row in cur.fetchall()]

    _add_order_item_interactive(int(_id), excluded_ids)


@command("edit order_item", "редактировать позицию заказа", CATEGORY_ORDERS, _SALES_ONLY)
def edit_order_item(_id: str) -> None:
    conn = get_conn()
    order = _get_order(conn, _id)
    if order is None:
        render_error(f"Заказ с ID {_id} не найден")
        return

    if not _is_editable(order):
        render_error(f"Заказ #{_id} нельзя редактировать (статус: {order.status})")
        return

    with conn.cursor() as cur:
        cur.execute(
            """SELECT oi.id, p.name, oi.quantity, oi.price
            FROM sales.order_items oi
            JOIN catalog.products p ON p.id = oi.product_id
            WHERE oi.order_id = %s
            ORDER BY oi.id""",
            (_id,),
        )
        items = cur.fetchall()

    if not items:
        render_error(f"В заказе #{_id} нет позиций")
        return

    values = [
        (item[0], f"{item[1]} × {item[2]} шт. по {item[3]:.2f} ₽") for item in items
    ]
    item_id = radiolist_dialog(
        title="Редактировать позицию",
        text="Выберите позицию:",
        values=values,
        default=values[0][0],
    ).run()

    if item_id is None:
        return

    selected = next(i for i in items if i[0] == item_id)
    quantity_str = prompt(
        f"Количество ({selected[1]}): ",
        default=str(selected[2]),
        validator=NonEmptyValidator("Введите количество"),
    ).strip()

    try:
        quantity = int(quantity_str)
        if quantity <= 0:
            render_error("Количество должно быть больше 0")
            return
    except ValueError:
        render_error("Введите целое число")
        return

    conn.execute(
        "UPDATE sales.order_items SET quantity = %s WHERE id = %s",
        (quantity, item_id),
    )
    _recalculate_total(conn, int(_id))
    console.print("[green]Позиция обновлена[/green]")


@command("delete order_item", "удалить позицию из заказа", CATEGORY_ORDERS, _SALES_ONLY)
def delete_order_item(_id: str) -> None:
    conn = get_conn()
    order = _get_order(conn, _id)
    if order is None:
        render_error(f"Заказ с ID {_id} не найден")
        return

    if not _is_editable(order):
        render_error(f"Заказ #{_id} нельзя редактировать (статус: {order.status})")
        return

    with conn.cursor() as cur:
        cur.execute(
            """SELECT oi.id, p.name, oi.quantity, oi.price
            FROM sales.order_items oi
            JOIN catalog.products p ON p.id = oi.product_id
            WHERE oi.order_id = %s
            ORDER BY oi.id""",
            (_id,),
        )
        items = cur.fetchall()

    if not items:
        render_error(f"В заказе #{_id} нет позиций")
        return

    values = [
        (item[0], f"{item[1]} × {item[2]} шт. по {item[3]:.2f} ₽") for item in items
    ]
    item_id = radiolist_dialog(
        title="Удалить позицию",
        text="Выберите позицию для удаления:",
        values=values,
        default=values[0][0],
    ).run()

    if item_id is None:
        return

    answer = prompt("Вы уверены? (y/n, д/н): ", validator=YesNoValidator())
    if YesNoValidator.is_yes(answer):
        conn.execute("DELETE FROM sales.order_items WHERE id = %s", (item_id,))
        _recalculate_total(conn, int(_id))
        console.print("[green]Позиция удалена[/green]")


@command("publish order", "опубликовать заказ (unpublished → new)", CATEGORY_ORDERS, _SALES_ONLY)
def publish_order(_id: str) -> None:
    conn = get_conn()
    order = _get_order(conn, _id)
    if order is None:
        render_error(f"Заказ с ID {_id} не найден")
        return

    if order.status != "unpublished":
        render_error(f"Заказ #{_id} уже опубликован (статус: {order.status})")
        return

    with conn.cursor() as cur:
        cur.execute(
            "SELECT COUNT(*) FROM sales.order_items WHERE order_id = %s", (_id,)
        )
        count_row = cur.fetchone()
        assert count_row is not None
        count = count_row[0]

    if count == 0:
        render_error("Нельзя опубликовать пустой заказ. Сначала добавьте товары.")
        return

    conn.execute(
        "UPDATE sales.orders SET status = 'new' WHERE id = %s", (_id,)
    )
    console.print(f"[bold green]Заказ #{_id} опубликован — статус изменён на 'new'[/bold green]")
