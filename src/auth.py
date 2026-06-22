from typing import Final, Sequence

from prompt_toolkit import prompt
from prompt_toolkit.shortcuts import radiolist_dialog

from console import console
from users import User, find_user_by_login_and_pass

ROLE_CATALOG_MANAGER: Final[str] = "catalog_manager"
ROLE_SALES_MANAGER: Final[str] = "sales_manager"
ROLE_INVENTORY_MANAGER: Final[str] = "inventory_manager"
ROLE_WORKER: Final[str] = "worker"

ALL_ROLES: Final[Sequence[str]] = (
    ROLE_CATALOG_MANAGER,
    ROLE_SALES_MANAGER,
    ROLE_INVENTORY_MANAGER,
    ROLE_WORKER,
)

# Учётные данные для быстрого входа в режиме разработки
_DEV_CREDENTIALS: Final[dict[str, str]] = {
    "cat_man": "catalog123",
    "sales_man": "sales123",
    "inv_man": "inventory123",
    "worker1": "worker123",
}

_USER: User | None = None


def _quick_login() -> User | None:
    """Показывает список пользователей для быстрого входа."""
    values = [
        (username, f"{username}  ({password})")
        for username, password in _DEV_CREDENTIALS.items()
    ]
    values.append((None, "Войти вручную"))  # type: ignore[arg-type]

    choice = radiolist_dialog(
        title="Быстрый вход",
        text="Выберите пользователя:",
        values=values,
        default=values[0][0],
    ).run()

    if choice is None:
        return None

    password = _DEV_CREDENTIALS[choice]
    return find_user_by_login_and_pass(choice, password)


def login(username: str | None = None, password: str | None = None) -> None:
    global _USER
    # Try CLI auth if both provided
    if username and password:
        user = find_user_by_login_and_pass(username, password)
        if user:
            if user.role not in ALL_ROLES:
                raise ValueError("Invalid user role")
            console.print(
                f"\n[green]✓ Вход выполнен как {user.username} ({user.role})[/green]\n"
            )
            _USER = user
            return

        console.print("\n[red]✗ Неверные учетные данные из CLI[/red]")
        console.print("[yellow]Попробуйте ввести вручную:[/yellow]\n")

    # Quick login via radiolist
    console.print("\n[bold cyan]═══════════════════════════════════════[/bold cyan]")
    console.print("[bold cyan]   Вход в систему[/bold cyan]")
    console.print("[bold cyan]═══════════════════════════════════════[/bold cyan]\n")

    user = _quick_login()
    if user:
        if user.role not in ALL_ROLES:
            raise ValueError("Invalid user role")
        console.print(
            f"\n[green]✓ Вход выполнен как {user.username} ({user.role})[/green]\n"
        )
        _USER = user
        return

    # Manual login fallback
    while True:
        username = prompt("Имя пользователя: ").strip()
        password = prompt("Пароль: ", is_password=True).strip()
        user = find_user_by_login_and_pass(username, password)

        if user:
            if user.role not in ALL_ROLES:
                raise ValueError("Invalid user role")
            console.print(
                f"\n[green]✓ Вход выполнен как {user.username} ({user.role})[/green]\n"
            )
            _USER = user
            return

        console.print("\n[red]✗ Неверное имя пользователя или пароль[/red]\n")


def auth_user() -> User:
    if _USER is None:
        raise RuntimeError("Not authenticated")
    return _USER
