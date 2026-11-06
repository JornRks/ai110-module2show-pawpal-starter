"""PawPal+ core classes.

Skeleton generated from diagrams/uml.mmd. Method bodies are stubs to be
implemented later.

Scheduler entry shapes (plain dicts, so the design stays at four classes):

    scheduled entry: {
        "pet": Pet,
        "task": Task,
        "start": datetime,
        "end": datetime,
        "reason": str,   # why the task was placed at this time
    }

    skipped entry: {
        "pet": Pet,
        "task": Task,
        "reason": str,   # why the task was left out
    }
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, time
from typing import Optional


@dataclass
class Task:
    """A single pet care activity."""

    title: str
    duration_minutes: int
    priority: str = "medium"  # "low", "medium", or "high"
    preferred_time: Optional[time] = None
    due_date: Optional[date] = None
    recurrence: str = "once"  # "once", "daily", or "weekly"
    completed_dates: set[date] = field(default_factory=set)

    def update_details(self, **changes) -> None:
        """Update one or more of the task's fields."""
        pass

    def mark_complete(self, on_date: date) -> None:
        """Record the task as completed on the given date."""
        pass

    def is_due(self, on_date: date) -> bool:
        """Return True if the task is due on the given date."""
        pass


@dataclass
class Pet:
    """A pet and its care tasks."""

    name: str
    species: str
    preferences: dict = field(default_factory=dict)  # food, toy, activity
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Add a care task to this pet's list."""
        pass

    def remove_task(self, task: Task) -> None:
        """Remove a care task from this pet's list."""
        pass

    def update_info(
        self,
        name: Optional[str] = None,
        species: Optional[str] = None,
        preferences: Optional[dict] = None,
    ) -> None:
        """Update the pet's information and preferences."""
        pass


@dataclass
class Owner:
    """A pet owner, their pets, and their daily availability."""

    name: str
    available_minutes: int = 0
    preferences: dict = field(default_factory=dict)
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to the owner's list."""
        pass

    def update_preferences(self, preferences: dict) -> None:
        """Update the owner's pet care preferences."""
        pass

    def update_available_time(self, minutes: int) -> None:
        """Change how many minutes the owner has for pet care today."""
        pass


class Scheduler:
    """Builds a daily care plan for an owner's pets."""

    def __init__(self, owner: Owner, day_start: time = time(8, 0)) -> None:
        self.owner = owner
        self.day_start = day_start
        self.scheduled: list[dict] = []  # scheduled entries (see module docstring)
        self.skipped: list[dict] = []  # skipped entries (see module docstring)

    def get_due_tasks(self, on_date: date) -> list[tuple[Pet, Task]]:
        """Collect (pet, task) pairs for every task due on the date."""
        pass

    def sort_tasks(
        self, tasks: list[tuple[Pet, Task]]
    ) -> list[tuple[Pet, Task]]:
        """Return the (pet, task) pairs sorted by task priority."""
        pass

    def detect_conflicts(self, schedule: list[dict]) -> list[tuple[dict, dict]]:
        """Return pairs of scheduled entries whose start/end times overlap."""
        pass

    def generate_schedule(self, on_date: date) -> list[dict]:
        """Fill self.scheduled and self.skipped for the date.

        Returns the scheduled entries.
        """
        pass

    def explain_schedule(self) -> str:
        """Explain why tasks were included or skipped, using
        self.scheduled and self.skipped."""
        pass
