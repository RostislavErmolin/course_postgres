from dataclasses import dataclass

from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter
from psycopg.rows import class_row
from rich.panel import Panel
from rich.table import Table

from auth import ROLE_CATALOG_MANAGER, ROLE_SALES_MANAGER
from console import console, render_error
from db import get_conn
from validators import ChoiceValidator, NonEmptyValidator, YesNoValidator
from commands import command, CATEGORY_WAREHOUSES

_ALL_ROLES = [ROLE_CATALOG_MANAGER, ROLE_SALES_MANAGER]
_CATALOG_ONLY = [ROLE_CATALOG_MANAGER]

cities = [
    "Москва",
    "Санкт-Петербург",
    "Новосибирск",
    "Екатеринбург",
    "Казань",
    "Нижний Новгород",
    "Челябинск",
    "Самара",
    "Омск",
    "Ростов-на-Дону",
    "Уфа",
    "Красноярск",
    "Воронеж",
    "Пермь",
    "Волгоград",
]

city_completer = WordCompleter(cities, ignore_case=True, sentence=True)
city_validator = ChoiceValidator(
    cities, message="Город должен быть из списка. Используйте Tab для автодополнения."
)


@dataclass
class Warehouse:
    id: int
    city: str
    address: str
    label: str | None
    is_central: bool


def _render_warehouse(warehouse: Warehouse) -> None:
    table = Table(show_header=False, box=None, padding=(0, 2))

    table.add_column("Поле", style="bold cyan", width=15)
    table.add_column("Значение", style="white")

    table.add_row("ID", str(warehouse.id))
    table.add_row("Город", warehouse.city)
    table.add_row("Адрес", warehouse.address)
    table.add_row("Метка", warehouse.label or "")
    table.add_row("Центральный", "[bold yellow]Да[/bold yellow]" if warehouse.is_central else "Нет")

    panel = Panel(
        table,
        expand=False,
        title=f"[bold green]Склад #{warehouse.id}[/bold green]",
        border_style="green",
    )

    console.print(panel)


def _warehouse_count(conn) -> int:
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM catalog.warehouses")
        return cur.fetchone()[0]


def _set_central(conn, warehouse_id: int) -> None:
    conn.execute("UPDATE catalog.warehouses SET is_central = FALSE WHERE is_central = TRUE")
    conn.execute("UPDATE catalog.warehouses SET is_central = TRUE WHERE id = %s", (warehouse_id,))


@command("list warehouses", "список всех складов", CATEGORY_WAREHOUSES, _ALL_ROLES)
def list_warehouses() -> None:
    conn = get_conn()
    table = Table(title="Склады", show_header=True, header_style="bold cyan")

    table.add_column("ID", style="dim", width=6, justify="right")
    table.add_column("Город", style="green", min_width=20)
    table.add_column("Адрес", style="yellow", min_width=30)
    table.add_column("Метка", style="magenta", min_width=15)
    table.add_column("Центральный", style="bold yellow", min_width=12, justify="center")

    with conn.cursor(row_factory=class_row(Warehouse)) as cur:
        cur.execute("SELECT * FROM catalog.warehouses")
        warehouses: list[Warehouse] = cur.fetchall()

    for warehouse in warehouses:
        table.add_row(
            str(warehouse.id),
            warehouse.city,
            warehouse.address,
            warehouse.label or "",
            "★" if warehouse.is_central else "",
        )
    console.print(table)


@command("show warehouse", "информация о складе", CATEGORY_WAREHOUSES, _ALL_ROLES)
def show_warehouse(_id: str) -> None:
    conn = get_conn()
    with conn.cursor(row_factory=class_row(Warehouse)) as cur:
        cur.execute("SELECT * FROM catalog.warehouses WHERE id = %s", (_id,))
        warehouse: Warehouse | None = cur.fetchone()

    if warehouse is None:
        render_error(f"Склад с ID {_id} не найден")
        return

    _render_warehouse(warehouse)


@command("add warehouse", "добавить склад (интерактивно)", CATEGORY_WAREHOUSES, _CATALOG_ONLY)
def add_warehouse() -> None:
    conn = get_conn()
    city = prompt("Город: ", validator=city_validator, completer=city_completer).strip()
    address = prompt("Адрес: ", validator=NonEmptyValidator()).strip()
    label = prompt("Метка (необязательно): ").strip() or None

    count = _warehouse_count(conn)

    if count == 0:
        # Первый склад автоматически становится центральным
        is_central = True
        console.print("[dim]Первый склад — автоматически назначен центральным.[/dim]")
    else:
        answer = prompt("Сделать центральным? (y/n, д/н): ", validator=YesNoValidator())
        is_central = YesNoValidator.is_yes(answer)

    if is_central:
        # Снимаем флаг у текущего центрального перед вставкой
        conn.execute("UPDATE catalog.warehouses SET is_central = FALSE WHERE is_central = TRUE")

    conn.execute(
        "INSERT INTO catalog.warehouses (city, address, label, is_central) VALUES (%s, %s, %s, %s)",
        (city, address, label, is_central),
    )
    suffix = f" ({label})" if label else ""
    console.print(f"[green]Склад в городе {city}{suffix} добавлен[/green]")


@command("edit warehouse", "редактировать склад", CATEGORY_WAREHOUSES, _CATALOG_ONLY)
def edit_warehouse(_id: str) -> None:
    conn = get_conn()
    with conn.cursor(row_factory=class_row(Warehouse)) as cur:
        cur.execute("SELECT * FROM catalog.warehouses WHERE id = %s", (_id,))
        warehouse: Warehouse | None = cur.fetchone()

    if warehouse is None:
        render_error(f"Склад с ID {_id} не найден")
        return

    city = prompt(
        "Город: ",
        default=warehouse.city,
        validator=city_validator,
        completer=city_completer,
    ).strip()
    address = prompt(
        "Адрес: ", default=warehouse.address, validator=NonEmptyValidator()
    ).strip()
    label = (
        prompt("Метка (необязательно): ", default=warehouse.label or "").strip() or None
    )

    if warehouse.is_central:
        # Центральный склад нельзя лишить статуса напрямую
        is_central = True
        console.print("[dim]Этот склад центральный — статус сохраняется.[/dim]")
    else:
        answer = prompt("Сделать центральным? (y/n, д/н): ", validator=YesNoValidator())
        is_central = YesNoValidator.is_yes(answer)
        if is_central:
            _set_central(conn, int(_id))

    conn.execute(
        """UPDATE catalog.warehouses SET city = %s, address = %s, label = %s, is_central = %s
        WHERE id = %s""",
        (city, address, label, is_central, _id),
    )
    suffix = f" ({label})" if label else ""
    console.print(f"[green]Склад в городе {city}{suffix} обновлен[/green]")


@command("delete warehouse", "удалить склад", CATEGORY_WAREHOUSES, _CATALOG_ONLY)
def delete_warehouse(_id: str) -> None:
    conn = get_conn()
    with conn.cursor(row_factory=class_row(Warehouse)) as cur:
        cur.execute("SELECT * FROM catalog.warehouses WHERE id = %s", (_id,))
        warehouse: Warehouse | None = cur.fetchone()

    if warehouse is None:
        render_error(f"Склад с ID {_id} не найден")
        return

    if warehouse.is_central:
        render_error(
            "Нельзя удалить центральный склад. Сначала назначьте другой склад центральным."
        )
        return

    _render_warehouse(warehouse)

    answer = prompt("Вы уверены? (y/n, д/н): ", validator=YesNoValidator())

    if YesNoValidator.is_yes(answer):
        conn.execute("DELETE FROM catalog.warehouses WHERE id = %s", (_id,))
        suffix = f" ({warehouse.label})" if warehouse.label else ""
        console.print(f"[green]Склад в городе {warehouse.city}{suffix} удален[/green]")
