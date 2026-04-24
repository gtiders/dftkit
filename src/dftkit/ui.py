from __future__ import annotations

from rich.table import Table


def plain_table(title: str, *, show_header: bool = True) -> Table:
    return Table(
        title=title,
        box=None,
        show_edge=False,
        show_header=show_header,
        show_lines=False,
        pad_edge=False,
    )
