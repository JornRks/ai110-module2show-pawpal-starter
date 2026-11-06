"""PawPal+ core classes: Task, Pet, Owner, and Scheduler.

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

from dataclasses import dataclass, field, replace
from datetime import date, datetime, time, timedelta
from typing import Optional

# Lower number = more important. Used for sorting.
PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}
VALID_RECURRENCES = ("once", "daily", "weekly")


@dataclass
class Task:
    """A single pet care activity.

    due_date meaning depends on recurrence:
      - "once":   the task is due from this date on until it is completed
                  (None = due right away).
      - "daily":  the first day the task is due (None = every day).
      - "weekly": the first occurrence; the task repeats every 7 days
                  after it. Required for weekly tasks.
    """

    title: str
    duration_minutes: int
    priority: str = "medium"  # "low", "medium", or "high"
    preferred_time: Optional[time] = None
    due_date: Optional[date] = None
    recurrence: str = "once"  # "once", "daily", or "weekly"
    completed_dates: set[date] = field(default_factory=set)

    def __post_init__(self) -> None:
        """Reject values that would silently break sorting or due checks."""
        if not self.title.strip():
            raise ValueError("Task title cannot be empty.")
        if self.duration_minutes <= 0:
            raise ValueError("duration_minutes must be greater than 0.")
        if self.priority not in PRIORITY_ORDER:
            raise ValueError(
                f"priority must be one of {list(PRIORITY_ORDER)}, got {self.priority!r}."
            )
        if self.recurrence not in VALID_RECURRENCES:
            raise ValueError(
                f"recurrence must be one of {list(VALID_RECURRENCES)}, got {self.recurrence!r}."
            )
        if self.recurrence == "weekly" and self.due_date is None:
            raise ValueError("Weekly tasks need a due_date to anchor the weekday.")

    def update_details(self, **changes) -> None:
        """Update the given fields, leaving the task unchanged if any value is invalid."""
        updated = replace(self, **changes)  # runs __post_init__ on the new values
        for name in changes:
            setattr(self, name, getattr(updated, name))

    def mark_complete(self, on_date: date) -> None:
        """Record the task as completed on the given date."""
        self.completed_dates.add(on_date)

    def is_due(self, on_date: date) -> bool:
        """Return True if the task still needs doing on the given date."""
        if on_date in self.completed_dates:
            return False
        if self.due_date is not None and on_date < self.due_date:
            return False

        if self.recurrence == "once":
            # A one-off task is finished once it has been completed on any day.
            return not self.completed_dates
        if self.recurrence == "daily":
            return True
        # weekly: same weekday as the anchor date
        return (on_date - self.due_date).days % 7 == 0


@dataclass
class Pet:
    """A pet and its care tasks."""

    name: str
    species: str
    preferences: dict = field(default_factory=dict)  # food, toy, activity
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Add a care task to this pet's list (ignored if already added)."""
        if not any(t is task for t in self.tasks):
            self.tasks.append(task)

    def remove_task(self, task: Task) -> None:
        """Remove this exact task object (matched by identity) from the pet's list."""
        for i, t in enumerate(self.tasks):
            if t is task:
                del self.tasks[i]
                return
        raise ValueError(f"{self.name} has no task {task.title!r}.")

    def update_info(
        self,
        name: Optional[str] = None,
        species: Optional[str] = None,
        preferences: Optional[dict] = None,
    ) -> None:
        """Update the pet's information. Preferences are merged, not replaced."""
        if name is not None:
            self.name = name
        if species is not None:
            self.species = species
        if preferences is not None:
            self.preferences.update(preferences)


@dataclass
class Owner:
    """A pet owner, their pets, and their daily availability."""

    name: str
    available_minutes: int = 0
    preferences: dict = field(default_factory=dict)
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to the owner's list (ignored if already added)."""
        if not any(p is pet for p in self.pets):
            self.pets.append(pet)

    def update_preferences(self, preferences: dict) -> None:
        """Merge new pet care preferences into the existing ones."""
        self.preferences.update(preferences)

    def update_available_time(self, minutes: int) -> None:
        """Change how many minutes the owner has for pet care today."""
        if minutes < 0:
            raise ValueError("available_minutes cannot be negative.")
        self.available_minutes = minutes

    def get_all_tasks(self) -> list[tuple[Pet, Task]]:
        """Return every task across all pets, paired with its pet."""
        return [(pet, task) for pet in self.pets for task in pet.tasks]


class Scheduler:
    """Builds a daily care plan for an owner's pets.

    The Scheduler never reaches into pets directly; it asks the Owner for
    (pet, task) pairs via Owner.get_all_tasks().
    """

    def __init__(self, owner: Owner, day_start: time = time(8, 0)) -> None:
        """Create a scheduler for the owner whose days begin at day_start."""
        self.owner = owner
        self.day_start = day_start
        self.scheduled: list[dict] = []  # scheduled entries (see module docstring)
        self.skipped: list[dict] = []  # skipped entries (see module docstring)

    def get_due_tasks(self, on_date: date) -> list[tuple[Pet, Task]]:
        """Collect (pet, task) pairs for every task due on the date."""
        return [
            (pet, task)
            for pet, task in self.owner.get_all_tasks()
            if task.is_due(on_date)
        ]

    def sort_tasks(
        self, tasks: list[tuple[Pet, Task]]
    ) -> list[tuple[Pet, Task]]:
        """Return the (pet, task) pairs sorted by priority, then preferred time, then duration."""

        def key(pair: tuple[Pet, Task]):
            """Build the sort key for one (pet, task) pair."""
            task = pair[1]
            return (
                PRIORITY_ORDER[task.priority],
                task.preferred_time is None,
                task.preferred_time or time.max,
                task.duration_minutes,
            )

        return sorted(tasks, key=key)

    def detect_conflicts(self, schedule: list[dict]) -> list[tuple[dict, dict]]:
        """Return pairs of scheduled entries whose times overlap (touching is not a conflict)."""
        ordered = sorted(schedule, key=lambda e: e["start"])
        conflicts = []
        for i, first in enumerate(ordered):
            for second in ordered[i + 1:]:
                if second["start"] >= first["end"]:
                    break  # sorted by start, so nothing later can overlap first
                conflicts.append((first, second))
        return conflicts

    def generate_schedule(self, on_date: date) -> list[dict]:
        """Place due tasks by priority into free slots within the owner's available time."""
        self.scheduled = []
        self.skipped = []
        minutes_left = self.owner.available_minutes
        day_start = datetime.combine(on_date, self.day_start)

        for pet, task in self.sort_tasks(self.get_due_tasks(on_date)):
            label = f"{task.priority} priority"

            if task.duration_minutes > minutes_left:
                self.skipped.append({
                    "pet": pet,
                    "task": task,
                    "reason": (
                        f"{label}, needs {task.duration_minutes} min but only "
                        f"{minutes_left} min of available time left"
                    ),
                })
                continue

            if task.preferred_time is not None:
                wanted = max(datetime.combine(on_date, task.preferred_time), day_start)
            else:
                wanted = day_start
            start = self._first_free_start(wanted, task.duration_minutes)
            end = start + timedelta(minutes=task.duration_minutes)

            if end.date() != on_date:
                self.skipped.append({
                    "pet": pet,
                    "task": task,
                    "reason": f"{label}, no free slot left before midnight",
                })
                continue

            self.scheduled.append({
                "pet": pet,
                "task": task,
                "start": start,
                "end": end,
                "reason": self._placement_reason(task, label, start),
            })
            minutes_left -= task.duration_minutes

        self.scheduled.sort(key=lambda e: e["start"])
        return self.scheduled

    def explain_schedule(self) -> str:
        """Explain why each task was scheduled or skipped in the last generated plan."""
        if not self.scheduled and not self.skipped:
            return "No tasks scheduled. Generate a schedule first, or add tasks that are due."

        lines = []
        if self.scheduled:
            lines.append("Scheduled:")
            for e in self.scheduled:
                lines.append(
                    f"  {e['start']:%H:%M}-{e['end']:%H:%M}  "
                    f"{e['pet'].name}: {e['task'].title} ({e['reason']})"
                )
        if self.skipped:
            lines.append("Skipped:")
            for e in self.skipped:
                lines.append(f"  {e['pet'].name}: {e['task'].title} ({e['reason']})")

        used = sum(e["task"].duration_minutes for e in self.scheduled)
        lines.append(
            f"Total: {used} of {self.owner.available_minutes} available minutes used."
        )
        return "\n".join(lines)

    # --- helpers -----------------------------------------------------------

    def _first_free_start(self, wanted: datetime, duration_minutes: int) -> datetime:
        """Return the earliest non-overlapping start time at or after `wanted`."""
        start = wanted
        length = timedelta(minutes=duration_minutes)
        for e in sorted(self.scheduled, key=lambda e: e["start"]):
            if e["end"] <= start:
                continue  # entirely before our slot
            if start + length <= e["start"]:
                break  # fits in the gap before this entry
            start = e["end"]  # overlaps, so try right after this entry
        return start

    def _placement_reason(self, task: Task, label: str, start: datetime) -> str:
        """Describe why the task landed at this start time."""
        if task.preferred_time is None:
            return f"{label}, placed in the earliest free slot"
        if start.time() == task.preferred_time:
            return f"{label}, at its preferred time"
        if task.preferred_time < self.day_start:
            return (
                f"{label}, preferred {task.preferred_time:%H:%M} is before the "
                f"day starts, so moved to the first free slot"
            )
        return (
            f"{label}, preferred {task.preferred_time:%H:%M} was taken, "
            f"so moved to the next free slot"
        )
