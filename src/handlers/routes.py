from dataclasses import dataclass
from datetime import timedelta

from prompt_toolkit import prompt
from prompt_toolkit.shortcuts import radiolist_dialog
from psycopg.rows import class_row
from rich.panel import Panel
from rich.table import Table

from auth import ROLE_INVENTORY_MANAGER, ROLE_WORKER
from console import console, render_error
from db import get_conn
from validators import NonEmptyValidator
from commands import command, CATEGORY_ROUTES

_INVENTORY_AND_WORKER = [ROLE_INVENTORY_MANAGER, ROLE_WORKER]
_INVENTORY_ONLY = [ROLE_INVENTORY_MANAGER]


@dataclass
class Route:
    from_city_id: int
    to_city_id: int
    from_city: str
    to_city: str
    duration: timedelta
    total_threshold: float


@dataclass
class City:
    id: int
    name: str


def _get_all_cities() -> list[City]:
    conn = get_conn()
    with conn.cursor(row_factory=class_row(City)) as cur:
        cur.execute("SELECT id, name FROM catalog.cities ORDER BY name")
        return cur.fetchall()


def _get_routes() -> list[Route]:
    conn = get_conn()
    with conn.cursor(row_factory=class_row(Route)) as cur:
        cur.execute("""
            SELECT r.from_city_id, r.to_city_id,
                   cf.name AS from_city, ct.name AS to_city,
                   r.duration, r.total_threshold
            FROM inventory.routes r
            JOIN catalog.cities cf ON cf.id = r.from_city_id
            JOIN catalog.cities ct ON ct.id = r.to_city_id
            ORDER BY cf.name, ct.name
        """)
        return cur.fetchall()


def _pick_existing_route(prompt_text: str = "Выберите маршрут:") -> Route | None:
    routes = _get_routes()
    if not routes:
        render_error("Нет доступных маршрутов")
        return None
    values = [(r, f"{r.from_city} → {r.to_city}") for r in routes]
    return radiolist_dialog(
        title="Выбор маршрута",
        text=prompt_text,
        values=values,
        default=values[0][0],
    ).run()


def _pick_city(cities: list[City], title: str, text: str) -> City | None:
    if not cities:
        render_error("Нет доступных городов")
        return None
    values = [(c, c.name) for c in cities]
    return radiolist_dialog(title=title, text=text, values=values, default=values[0][0]).run()


def _format_duration(td: timedelta) -> str:
    total_minutes = int(td.total_seconds() // 60)
    hours, minutes = divmod(total_minutes, 60)
    if hours:
        return f"{hours} ч {minutes} мин"
    return f"{minutes} мин"


def _render_route(route: Route) -> None:
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Поле", style="bold cyan", width=20)
    table.add_column("Значение", style="white")

    table.add_row("Откуда", route.from_city)
    table.add_row("Куда", route.to_city)
    table.add_row("Время доставки", _format_duration(route.duration))
    table.add_row("Мин. сумма (₽)", f"{route.total_threshold:,.2f}")

    console.print(Panel(
        table,
        expand=False,
        title=f"[bold green]{route.from_city} → {route.to_city}[/bold green]",
        border_style="green",
    ))


def _prompt_duration(default_minutes: int | None = None) -> int | None:
    default_str = str(default_minutes) if default_minutes is not None else ""
    raw = prompt(
        "Время доставки (минуты): ",
        default=default_str,
        validator=NonEmptyValidator(),
    ).strip()
    try:
        minutes = int(raw)
        if minutes <= 0:
            raise ValueError
        return minutes
    except ValueError:
        render_error("Введите целое положительное число минут")
        return None


def _prompt_threshold(default: float | None = None) -> float | None:
    default_str = str(int(default)) if default is not None else ""
    raw = prompt(
        "Минимальная сумма для перемещения (₽): ",
        default=default_str,
        validator=NonEmptyValidator(),
    ).strip()
    try:
        value = float(raw)
        if value <= 0:
            raise ValueError
        return value
    except ValueError:
        render_error("Введите положительное число")
        return None


@command("list routes", "список маршрутов перемещения", CATEGORY_ROUTES, _INVENTORY_AND_WORKER)
def list_routes() -> None:
    routes = _get_routes()
    if not routes:
        console.print("[dim]Маршруты не заданы[/dim]")
        return

    table = Table(title="Маршруты перемещения", show_header=True, header_style="bold cyan")
    table.add_column("Откуда", style="green", min_width=20)
    table.add_column("Куда", style="yellow", min_width=20)
    table.add_column("Время", style="white", min_width=12)
    table.add_column("Мин. сумма (₽)", style="magenta", min_width=18, justify="right")

    for r in routes:
        table.add_row(
            r.from_city,
            r.to_city,
            _format_duration(r.duration),
            f"{r.total_threshold:,.2f}",
        )
    console.print(table)


@command("show route", "информация о маршруте", CATEGORY_ROUTES, _INVENTORY_AND_WORKER)
def show_route() -> None:
    route = _pick_existing_route()
    if route is None:
        return
    _render_route(route)


@command("add route", "добавить маршрут перемещения", CATEGORY_ROUTES, _INVENTORY_ONLY)
def add_route() -> None:
    conn = get_conn()
    all_cities = _get_all_cities()
    existing = {(r.from_city_id, r.to_city_id) for r in _get_routes()}

    from_city = _pick_city(all_cities, "Город отправления", "Откуда:")
    if from_city is None:
        return

    available_to = [
        c for c in all_cities
        if c.id != from_city.id and (from_city.id, c.id) not in existing
    ]
    if not available_to:
        render_error(f"Из города {from_city.name} все маршруты уже заданы")
        return

    to_city = _pick_city(available_to, "Город назначения", "Куда:")
    if to_city is None:
        return

    minutes = _prompt_duration()
    if minutes is None:
        return

    threshold = _prompt_threshold()
    if threshold is None:
        return

    conn.execute(
        """INSERT INTO inventory.routes (from_city_id, to_city_id, duration, total_threshold)
        VALUES (%s, %s, make_interval(mins => %s), %s)""",
        (from_city.id, to_city.id, minutes, threshold),
    )
    console.print(
        f"[green]Маршрут {from_city.name} → {to_city.name} добавлен[/green]"
    )


@command("edit route", "редактировать маршрут", CATEGORY_ROUTES, _INVENTORY_ONLY)
def edit_route() -> None:
    conn = get_conn()
    route = _pick_existing_route("Выберите маршрут для редактирования:")
    if route is None:
        return

    current_minutes = int(route.duration.total_seconds() // 60)
    minutes = _prompt_duration(default_minutes=current_minutes)
    if minutes is None:
        return

    threshold = _prompt_threshold(default=float(route.total_threshold))
    if threshold is None:
        return

    conn.execute(
        """UPDATE inventory.routes
        SET duration = make_interval(mins => %s), total_threshold = %s
        WHERE from_city_id = %s AND to_city_id = %s""",
        (minutes, threshold, route.from_city_id, route.to_city_id),
    )
    console.print(
        f"[green]Маршрут {route.from_city} → {route.to_city} обновлён[/green]"
    )


@command("delete route", "удалить маршрут", CATEGORY_ROUTES, _INVENTORY_ONLY)
def delete_route() -> None:
    conn = get_conn()
    route = _pick_existing_route("Выберите маршрут для удаления:")
    if route is None:
        return

    _render_route(route)

    confirm = prompt("Удалить маршрут? (y/n, д/н): ").strip().lower()
    if confirm not in ("y", "д", "yes", "да"):
        console.print("[dim]Отменено[/dim]")
        return

    conn.execute(
        "DELETE FROM inventory.routes WHERE from_city_id = %s AND to_city_id = %s",
        (route.from_city_id, route.to_city_id),
    )
    console.print(
        f"[green]Маршрут {route.from_city} → {route.to_city} удалён[/green]"
    )
