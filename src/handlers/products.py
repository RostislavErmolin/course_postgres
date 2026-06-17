from dataclasses import dataclass
from decimal import Decimal

from prompt_toolkit import prompt
from prompt_toolkit.shortcuts import radiolist_dialog
from psycopg.rows import class_row
from rich.panel import Panel
from rich.table import Table

from auth import ROLE_CATALOG_MANAGER, ROLE_SALES_MANAGER
from console import console, render_error
from db import get_conn
from validators import NonEmptyValidator, PriceValidator, YesNoValidator
from commands import command, CATEGORY_PRODUCTS
from handlers.product_categories import ProductCategory

_ALL_ROLES = [ROLE_CATALOG_MANAGER, ROLE_SALES_MANAGER]
_CATALOG_ONLY = [ROLE_CATALOG_MANAGER]


@dataclass
class Product:
    id: int
    sku: str
    name: str
    price: Decimal
    category_id: int


def _get_categories() -> list[ProductCategory]:
    conn = get_conn()
    with conn.cursor(row_factory=class_row(ProductCategory)) as cur:
        cur.execute("SELECT * FROM catalog.product_categories ORDER BY name")
        return cur.fetchall()


def _pick_category(default_id: int | None = None) -> int | None:
    categories = _get_categories()

    if not categories:
        render_error("Нет ни одной категории. Сначала добавьте категорию через 'add product_category'.")
        return None

    default_value = default_id if default_id is not None else categories[0].id

    result = radiolist_dialog(
        title="Выбор категории",
        text="Выберите категорию товара (стрелки + Enter):",
        values=[(cat.id, cat.name) for cat in categories],
        default=default_value,
    ).run()

    return result


def _get_category_name(category_id: int) -> str:
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute(
            "SELECT name FROM catalog.product_categories WHERE id = %s", (category_id,)
        )
        row = cur.fetchone()
        return row[0] if row else str(category_id)


def _render_product(product: Product) -> None:
    table = Table(show_header=False, box=None, padding=(0, 2))

    table.add_column("Поле", style="bold cyan", width=15)
    table.add_column("Значение", style="white")

    table.add_row("ID", str(product.id))
    table.add_row("SKU", product.sku)
    table.add_row("Название", product.name)
    table.add_row("Цена", f"{product.price:.2f} ₽")
    table.add_row("Категория", _get_category_name(product.category_id))

    panel = Panel(
        table,
        expand=False,
        title=f"[bold green]Товар #{product.id}[/bold green]",
        border_style="green",
    )

    console.print(panel)


@command("list products", "список всех товаров", CATEGORY_PRODUCTS, _ALL_ROLES)
def list_products() -> None:
    conn = get_conn()
    table = Table(title="Товары", show_header=True, header_style="bold cyan")

    table.add_column("ID", style="dim", width=6, justify="right")
    table.add_column("SKU", style="green", min_width=15)
    table.add_column("Название", style="yellow", min_width=25)
    table.add_column("Цена", style="cyan", min_width=12, justify="right")
    table.add_column("Категория", style="magenta", min_width=20)

    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT p.id, p.sku, p.name, p.price, COALESCE(c.name, '—')
            FROM catalog.products p
            LEFT JOIN catalog.product_categories c ON c.id = p.category_id
            ORDER BY p.id
            """
        )
        rows = cur.fetchall()

    for row in rows:
        table.add_row(str(row[0]), row[1], row[2], f"{row[3]:.2f} ₽", row[4])

    console.print(table)


@command("show product", "информация о товаре", CATEGORY_PRODUCTS, _ALL_ROLES)
def show_product(_id: str) -> None:
    conn = get_conn()
    with conn.cursor(row_factory=class_row(Product)) as cur:
        cur.execute("SELECT * FROM catalog.products WHERE id = %s", (_id,))
        product: Product | None = cur.fetchone()

    if product is None:
        render_error(f"Товар с ID {_id} не найден")
        return

    _render_product(product)


@command("add product", "добавить товар (интерактивно)", CATEGORY_PRODUCTS, _CATALOG_ONLY)
def add_product() -> None:
    conn = get_conn()

    category_id = _pick_category()
    if category_id is None:
        return

    sku = prompt("SKU (до 30 символов): ", validator=NonEmptyValidator()).strip()
    name = prompt("Название: ", validator=NonEmptyValidator()).strip()
    price_str = prompt("Цена: ", validator=PriceValidator()).strip()

    conn.execute(
        "INSERT INTO catalog.products (sku, name, price, category_id) VALUES (%s, %s, %s, %s)",
        (sku, name, Decimal(price_str), category_id),
    )
    console.print(f"[green]Товар «{name}» (SKU: {sku}) добавлен[/green]")


@command("edit product", "редактировать товар", CATEGORY_PRODUCTS, _CATALOG_ONLY)
def edit_product(_id: str) -> None:
    conn = get_conn()
    with conn.cursor(row_factory=class_row(Product)) as cur:
        cur.execute("SELECT * FROM catalog.products WHERE id = %s", (_id,))
        product: Product | None = cur.fetchone()

    if product is None:
        render_error(f"Товар с ID {_id} не найден")
        return

    category_id = _pick_category(default_id=product.category_id)
    if category_id is None:
        return

    sku = prompt(
        "SKU (до 30 символов): ", default=product.sku, validator=NonEmptyValidator()
    ).strip()
    name = prompt(
        "Название: ", default=product.name, validator=NonEmptyValidator()
    ).strip()
    price_str = prompt(
        "Цена: ", default=str(product.price), validator=PriceValidator()
    ).strip()

    conn.execute(
        """UPDATE catalog.products
        SET sku = %s, name = %s, price = %s, category_id = %s
        WHERE id = %s""",
        (sku, name, Decimal(price_str), category_id, _id),
    )
    console.print(f"[green]Товар «{name}» (SKU: {sku}) обновлен[/green]")


@command("delete product", "удалить товар", CATEGORY_PRODUCTS, _CATALOG_ONLY)
def delete_product(_id: str) -> None:
    conn = get_conn()
    with conn.cursor(row_factory=class_row(Product)) as cur:
        cur.execute("SELECT * FROM catalog.products WHERE id = %s", (_id,))
        product: Product | None = cur.fetchone()

    if product is None:
        render_error(f"Товар с ID {_id} не найден")
        return

    _render_product(product)
    answer = prompt("Вы уверены? (y/n, д/н): ", validator=YesNoValidator())

    if YesNoValidator.is_yes(answer):
        conn.execute("DELETE FROM catalog.products WHERE id = %s", (_id,))
        console.print(f"[green]Товар «{product.name}» (SKU: {product.sku}) удален[/green]")
