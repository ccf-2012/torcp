# -*- coding: utf-8 -*-
"""
Progress bar utilities for torcp operations.
"""

import logging
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeRemainingColumn
from rich.console import Console
from rich.logging import RichHandler


class TorcpProgress:
    """Progress manager for torcp operations with multi-level progress tracking."""

    def __init__(self, console=None, disable=False):
        self.console = console or Console()
        self.disable = disable
        self.progress = None
        self.main_task = None
        self.sub_task = None
        self._started = False
        self._old_handlers = []

    def start(self, total_items, description="Processing"):
        """Start the main progress bar."""
        if self.disable:
            return
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TextColumn("[dim]{task.fields[status]}"),
            TimeRemainingColumn(),
            console=self.console,
            transient=False
        )
        self.progress.start()
        self.main_task = self.progress.add_task(description, total=total_items, status="")
        self._started = True

        # Replace logging handlers with RichHandler that uses progress console
        # This ensures logs appear above the progress bar
        root_logger = logging.getLogger()
        self._old_handlers = root_logger.handlers[:]
        root_logger.handlers.clear()
        rich_handler = RichHandler(
            console=self.progress.console,
            show_time=True,
            show_path=False,
            markup=False,
            rich_tracebacks=True
        )
        rich_handler.setFormatter(logging.Formatter("%(message)s"))
        root_logger.addHandler(rich_handler)

    def update(self, advance=0, description=None, status=None):
        """Update the main progress bar."""
        if self.disable or not self._started or not self.progress:
            return
        update_kwargs = {}
        if advance:
            update_kwargs['advance'] = advance
        if description is not None:
            update_kwargs['description'] = description
        if status is not None:
            update_kwargs['status'] = status
        if update_kwargs:
            self.progress.update(self.main_task, **update_kwargs)

    def set_status(self, status):
        """Set the current operation status (shown in dim text)."""
        if self.disable or not self._started or not self.progress:
            return
        self.progress.update(self.main_task, status=status)

    def log(self, message):
        """Print a message above the progress bar."""
        if self.disable or not self._started or not self.progress:
            return
        self.progress.console.print(f"  [dim]{message}[/dim]")

    def stop(self):
        """Stop the progress bar."""
        if self.disable or not self._started or not self.progress:
            return
        self.progress.stop()
        self._started = False

        # Restore original logging handlers
        root_logger = logging.getLogger()
        root_logger.handlers.clear()
        for handler in self._old_handlers:
            root_logger.addHandler(handler)
        self._old_handlers = []
