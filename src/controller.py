from textual.binding import Binding


UP_KEYS = ("up", "k", "w", "l")
DOWN_KEYS = ("down", "j", "s", "a")

TABLE_NAVIGATION_BINDINGS = [
    *(Binding(key, "cursor_up", "Up", show=False) for key in UP_KEYS),
    *(Binding(key, "cursor_down", "Down", show=False) for key in DOWN_KEYS),
    Binding("enter", "launch", "Launch", show=False),
]
