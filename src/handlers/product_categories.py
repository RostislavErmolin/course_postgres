from dataclasses import dataclass

from prompt_toolkit import prompt
from psycopg.rows import class_row
from rich.panel import Panel
from rich.table import Table

from console import console, render_error
from db import get_conn
from validators import NonEmptyValidator, YesNoValidator
from commands import command, CATEGORY_PRODUCTS


@dataclass
class ProductCategory:
    id: int
    name: str


def _render_category(category: ProductCategory) -> None:
    table = Table(show_header=False, box=None, padding=(0, 2))

    table.add_column("Поле", style="bold cyan", width=15)
    table.add_column("Значение", style="white")

    table.add_row("ID", str(category.id))
    table.add_row("Название", category.name)

    panel = Panel(
        table,
        expand=False,
        title=f"[bold green]Категория #{category.id}[/bold green]",
        border_style="green",
    )

    console.print(panel)


@command("list product_categories", "список всех категорий товаров", CATEGORY_PRODUCTS)
def list_product_categories() -> None:
    conn = get_conn()
    table = Table(title="Категории товаров", show_header=True, header_style="bold cyan")

    table.add_column("ID", style="dim", width=6, justify="right")
    table.add_column("Название", style="green", min_width=30)

    with conn.cursor(row_factory=class_row(ProductCategory)) as cur:
        cur.execute("SELECT * FROM catalog.product_categories ORDER BY id")
        categories: list[ProductCategory] = cur.fetchall()

    for category in categories:
        table.add_row(str(category.id), category.name)

    console.print(table)


@command("show product_category", "информация о категории", CATEGORY_PRODUCTS)
def show_product_category(_id: str) -> None:
    conn = get_conn()
    with conn.cursor(row_factory=class_row(ProductCategory)) as cur:
        cur.execute("SELECT * FROM catalog.product_categories WHERE id = %s", (_id,))
        category: ProductCategory | None = cur.fetchone()

    if category is None:
        render_error(f"Категория с ID {_id} не найдена")
        return

    _render_category(category)


@command("add product_category", "добавить категорию товаров", CATEGORY_PRODUCTS)
def add_product_category() -> None:
    conn = get_conn()
    name = prompt("Название: ", validator=NonEmptyValidator()).strip()
    conn.execute(
        "INSERT INTO catalog.product_categories (name) VALUES (%s)",
        (name,),
    )
    console.print(f"[green]Категория «{name}» добавлена[/green]")


@command("edit product_category", "редактировать категорию", CATEGORY_PRODUCTS)
def edit_product_category(_id: str) -> None:
    conn = get_conn()
    with conn.cursor(row_factory=class_row(ProductCategory)) as cur:
        cur.execute("SELECT * FROM catalog.product_categories WHERE id = %s", (_id,))
        category: ProductCategory | None = cur.fetchone()

    if category is None:
        render_error(f"Категория с ID {_id} не найдена")
        return

    name = prompt(
        "Название: ", default=category.name, validator=NonEmptyValidator()
    ).strip()
    conn.execute(
        "UPDATE catalog.product_categories SET name = %s WHERE id = %s",
        (name, _id),
    )
    console.print(f"[green]Категория обновлена: «{name}»[/green]")


@command("delete product_category", "удалить категорию", CATEGORY_PRODUCTS)
def delete_product_category(_id: str) -> None:
    conn = get_conn()
    with conn.cursor(row_factory=class_row(ProductCategory)) as cur:
        cur.execute("SELECT * FROM catalog.product_categories WHERE id = %s", (_id,))
        category: ProductCategory | None = cur.fetchone()

    if category is None:
        render_error(f"Категория с ID {_id} не найдена")
        return

    # Запрещаем удаление, если в категории есть товары
    with conn.cursor() as cur:
        cur.execute(
            "SELECT COUNT(*) FROM catalog.products WHERE category_id = %s", (_id,)
        )
        count = cur.fetchone()[0]

    if count > 0:
        render_error(
            f"Нельзя удалить категорию «{category.name}»: в ней {count} товар(ов). "
            "Сначала удалите или переместите товары."
        )
        return

    _render_category(category)
    answer = prompt("Вы уверены? (y/n, д/н): ", validator=YesNoValidator())

    if YesNoValidator.is_yes(answer):
        conn.execute(
            "DELETE FROM catalog.product_categories WHERE id = %s", (_id,)
        )
        console.print(f"[green]Категория «{category.name}» удалена[/green]")
