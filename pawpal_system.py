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

    Each Task object is ONE occurrence. It is due from due_date on
    (None = due right away) until it is completed. For "daily" and "weekly"
    tasks, completing the occurrence creates a new Task for the next one
    (see next_occurrence), so the to-do list always holds the upcoming
    instance and the finished ones stay as history.
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

    @property
    def is_completed(self) -> bool:
        """Whether this occurrence has been completed.

        Returns:
            True if the task has been marked complete on any date, else False.
            Each Task is a single occurrence, so one completion finishes it.
        """
        return bool(self.completed_dates)

    def mark_complete(self, on_date: date) -> Optional[Task]:
        """Complete this occurrence and return the next one, if the task repeats.

        This only builds the next Task; it does not add it to a pet. Use
        Scheduler.mark_task_complete() to complete a task and store its
        next occurrence in one step.

        Args:
            on_date: The day the task was completed.

        Returns:
            A new Task for the next occurrence (see next_occurrence) for
            "daily" and "weekly" tasks. None for "once" tasks, and None if
            this task was already completed, so completing twice never
            creates duplicate occurrences.
        """
        if self.is_completed:
            return None
        self.completed_dates.add(on_date)
        return self.next_occurrence(on_date)

    def next_occurrence(self, completed_on: date) -> Optional[Task]:
        """Build a fresh, not-yet-completed copy due on the next occurrence date.

        Dates are calculated with timedelta, so month ends, year ends and
        leap days are handled correctly (Dec 31 + 1 day = Jan 1).

        - daily:  completed_on + timedelta(days=1).
        - weekly: due_date + timedelta(weeks=1), stepped forward a week at a
          time until it is after completed_on. This keeps the weekday, so a
          Monday task done late on Wednesday is next due the following Monday.

        Args:
            completed_on: The day this occurrence was completed.

        Returns:
            A copy of this task with the new due_date and no completion
            history, or None if the task's recurrence is "once".
        """
        if self.recurrence == "daily":
            next_due = completed_on + timedelta(days=1)
        elif self.recurrence == "weekly":
            next_due = self.due_date + timedelta(weeks=1)
            while next_due <= completed_on:
                next_due += timedelta(weeks=1)
        else:
            return None
        return replace(self, due_date=next_due, completed_dates=set())

    def is_due(self, on_date: date) -> bool:
        """Check whether this occurrence still needs doing on the given date.

        An uncompleted occurrence stays due after its due date, so missed
        tasks carry over as overdue instead of silently disappearing.

        Args:
            on_date: The day to check.

        Returns:
            False if the task is completed or its due_date is after on_date;
            True otherwise (a task with no due_date is due right away).
        """
        if self.is_completed:
            return False
        return self.due_date is None or on_date >= self.due_date


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

    def sort_by_time(
        self, tasks: list[tuple[Pet, Task]]
    ) -> list[tuple[Pet, Task]]:
        """Sort (pet, task) pairs by preferred time, earliest first.

        Uses sorted() with a lambda key that turns each preferred_time into
        an "HH:MM" string. Because hours and minutes are zero-padded,
        comparing the strings alphabetically gives the same order as
        comparing the times ("08:30" < "13:05"). Tasks with no preferred
        time get "24:00", which sorts after any real time, so they land at
        the end. sorted() is stable, so tasks with the same time keep their
        original order. Runs in O(n log n).

        Args:
            tasks: (pet, task) pairs, e.g. from Owner.get_all_tasks() or
                filter_tasks(). The input list is not modified.

        Returns:
            A new list of the same pairs, ordered by preferred time.

        Example:
            >>> [t.title for _, t in scheduler.sort_by_time(owner.get_all_tasks())]
            ['Morning walk', 'Feed Titus', 'Evening walk', 'Clean litter box']
        """
        return sorted(
            tasks,
            key=lambda pair: (
                pair[1].preferred_time.strftime("%H:%M")
                if pair[1].preferred_time is not None
                else "24:00"
            ),
        )

    def filter_tasks(
        self,
        pet_name: Optional[str] = None,
        completed: Optional[bool] = None,
        on_date: Optional[date] = None,
    ) -> list[tuple[Pet, Task]]:
        """Return the owner's (pet, task) pairs that match every given filter.

        Filters are optional and combine with AND, so
        filter_tasks(pet_name="Lucy", completed=False) gives Lucy's
        unfinished tasks. With no filters, every task is returned.

        Args:
            pet_name: Keep only this pet's tasks (case-insensitive).
                None means all pets.
            completed: True keeps only tasks completed on on_date; False
                keeps only tasks not completed on on_date (this includes
                upcoming occurrences of recurring tasks). None skips the
                status filter.
            on_date: The day completion is checked against. Defaults to today.

        Returns:
            A new list of matching (pet, task) pairs, in pet then task order.
        """
        on_date = on_date or date.today()
        results = []
        for pet, task in self.owner.get_all_tasks():
            if pet_name is not None and pet.name.lower() != pet_name.lower():
                continue
            if completed is not None and (on_date in task.completed_dates) != completed:
                continue
            results.append((pet, task))
        return results

    def mark_task_complete(
        self, pet: Pet, task: Task, on_date: Optional[date] = None
    ) -> Optional[Task]:
        """Complete a task and, if it repeats, add its next occurrence to the pet.

        Calls Task.mark_complete(), then stores the returned next occurrence
        on the pet with Pet.add_task(). Completing an already-completed task
        does nothing, so no duplicates are created.

        Args:
            pet: The pet that owns the task.
            task: The task to complete.
            on_date: The day it was completed. Defaults to today.

        Returns:
            The newly created next-occurrence Task (due tomorrow for "daily",
            next week on the same weekday for "weekly"), or None if nothing
            new was created.
        """
        next_task = task.mark_complete(on_date or date.today())
        if next_task is not None:
            pet.add_task(next_task)
        return next_task

    def conflict_warnings(self, on_date: date) -> list[str]:
        """Return warning messages for due tasks whose preferred times overlap.

        Lightweight check: each due task with a preferred_time becomes a
        window from preferred_time to preferred_time + duration, and
        detect_conflicts() finds overlapping windows. It works for tasks of
        the same pet and of different pets. Windows that only touch (one
        ends exactly when the next starts) are not conflicts. Tasks with no
        preferred time are ignored.

        It never raises and never changes any data, so callers can just
        print the messages. generate_schedule() will still move one of the
        clashing tasks to the next free slot.

        Args:
            on_date: The day whose due tasks are checked.

        Returns:
            One "WARNING: ..." string per overlapping pair, naming both tasks,
            their times, and the pet(s) involved. An empty list means no
            conflicts.
        """
        windows = []
        for pet, task in self.get_due_tasks(on_date):
            if task.preferred_time is None:
                continue
            start = datetime.combine(on_date, task.preferred_time)
            end = start + timedelta(minutes=task.duration_minutes)
            windows.append({"pet": pet, "task": task, "start": start, "end": end})

        warnings = []
        for a, b in self.detect_conflicts(windows):
            who = (
                f"both for {a['pet'].name}"
                if a["pet"] is b["pet"]
                else f"{a['pet'].name} and {b['pet'].name}"
            )
            warnings.append(
                f"WARNING: '{a['task'].title}' ({a['start']:%H:%M}-{a['end']:%H:%M}) "
                f"overlaps '{b['task'].title}' ({b['start']:%H:%M}-{b['end']:%H:%M}), "
                f"{who}."
            )
        return warnings

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
