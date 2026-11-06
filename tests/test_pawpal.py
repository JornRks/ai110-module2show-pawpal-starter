from datetime import date

from pawpal_system import Pet, Task


def test_mark_complete_changes_task_status():
    task = Task("Morning walk", 30, "high", recurrence="daily")
    today = date(2026, 11, 6)
    assert task.is_due(today)

    task.mark_complete(today)

    assert today in task.completed_dates
    assert not task.is_due(today)


def test_add_task_increases_pet_task_count():
    pet = Pet("Mochi", "dog")
    assert len(pet.tasks) == 0

    pet.add_task(Task("Feed breakfast", 10))

    assert len(pet.tasks) == 1


def _owner_with_tasks():
    from datetime import time
    from pawpal_system import Owner

    owner = Owner("Jorn", available_minutes=120)
    dog, cat = Pet("Mochi", "dog"), Pet("Luna", "cat")
    owner.add_pet(dog)
    owner.add_pet(cat)
    dog.add_task(Task("Evening walk", 30, preferred_time=time(18, 30)))
    cat.add_task(Task("Litter box", 10))  # no preferred time
    dog.add_task(Task("Morning walk", 30, preferred_time=time(8, 0)))
    cat.add_task(Task("Feed Luna", 10, preferred_time=time(13, 5)))
    return owner


def test_sort_by_time_orders_earliest_first_and_untimed_last():
    from pawpal_system import Scheduler

    owner = _owner_with_tasks()
    scheduler = Scheduler(owner)

    titles = [t.title for _, t in scheduler.sort_by_time(owner.get_all_tasks())]

    assert titles == ["Morning walk", "Feed Luna", "Evening walk", "Litter box"]


def test_filter_tasks_by_pet_name_and_completion():
    from pawpal_system import Scheduler

    owner = _owner_with_tasks()
    scheduler = Scheduler(owner)
    today = date(2026, 11, 6)
    owner.pets[0].tasks[0].mark_complete(today)  # Evening walk

    mochi = [t.title for _, t in scheduler.filter_tasks(pet_name="MOCHI")]
    done = [t.title for _, t in scheduler.filter_tasks(completed=True, on_date=today)]
    todo = scheduler.filter_tasks(pet_name="Mochi", completed=False, on_date=today)

    assert mochi == ["Evening walk", "Morning walk"]
    assert done == ["Evening walk"]
    assert [t.title for _, t in todo] == ["Morning walk"]


def test_completing_daily_task_creates_next_day_occurrence():
    from pawpal_system import Owner, Scheduler

    owner = Owner("Jorn")
    pet = Pet("Mochi", "dog")
    owner.add_pet(pet)
    today = date(2026, 11, 6)
    walk = Task("Walk", 30, recurrence="daily", due_date=today)
    pet.add_task(walk)

    nxt = Scheduler(owner).mark_task_complete(pet, walk, today)

    assert nxt is not None and nxt is not walk
    assert nxt.due_date == date(2026, 11, 7)
    assert not nxt.is_completed and walk.is_completed
    assert len(pet.tasks) == 2
    assert not walk.is_due(date(2026, 11, 7)) and nxt.is_due(date(2026, 11, 7))
    # Completing again must not add another copy.
    assert Scheduler(owner).mark_task_complete(pet, walk, today) is None
    assert len(pet.tasks) == 2


def test_weekly_next_occurrence_keeps_weekday_and_once_does_not_repeat():
    monday = date(2026, 11, 2)
    weekly = Task("Bath", 20, recurrence="weekly", due_date=monday)
    # Completed late (Wednesday) -> next one is still the following Monday.
    assert weekly.mark_complete(date(2026, 11, 4)).due_date == date(2026, 11, 9)
    assert Task("Vet visit", 60).mark_complete(monday) is None


def test_conflict_warnings_flag_same_time_tasks():
    from datetime import time
    from pawpal_system import Owner, Scheduler

    owner = Owner("Jorn", available_minutes=60)
    dog, cat = Pet("Mochi", "dog"), Pet("Luna", "cat")
    owner.add_pet(dog)
    owner.add_pet(cat)
    dog.add_task(Task("Meds", 5, preferred_time=time(9, 0)))
    cat.add_task(Task("Feed", 10, preferred_time=time(9, 0)))
    dog.add_task(Task("Walk", 30, preferred_time=time(9, 10)))  # touches Feed's end: no conflict

    warnings = Scheduler(owner).conflict_warnings(date(2026, 11, 6))

    assert len(warnings) == 1
    assert "Meds" in warnings[0] and "Feed" in warnings[0]
    assert Scheduler(Owner("Empty")).conflict_warnings(date(2026, 11, 6)) == []


# --- Phase 5: edge cases ---------------------------------------------------

import pytest
from datetime import time

from pawpal_system import Owner, Scheduler

DAY = date(2026, 11, 6)


def make_owner(minutes=120, **pet_tasks):
    """Build an owner with one pet per keyword, e.g. make_owner(Mochi=[task, ...])."""
    owner = Owner("Jorn", available_minutes=minutes)
    for name, tasks in pet_tasks.items():
        pet = Pet(name, "dog")
        for task in tasks:
            pet.add_task(task)
        owner.add_pet(pet)
    return owner


# Sorting

def test_sort_by_time_keeps_original_order_for_ties_and_handles_empty():
    pet = Pet("Mochi", "dog")
    a = Task("A", 10, preferred_time=time(9, 0))
    b = Task("B", 10, preferred_time=time(9, 0))
    scheduler = Scheduler(make_owner())
    pairs = [(pet, a), (pet, b)]

    assert [t.title for _, t in scheduler.sort_by_time(pairs)] == ["A", "B"]
    assert [t.title for _, t in scheduler.sort_by_time(pairs[::-1])] == ["B", "A"]
    assert pairs == [(pet, a), (pet, b)]  # input not modified
    assert scheduler.sort_by_time([]) == []


def test_sort_tasks_orders_by_priority_before_time():
    owner = make_owner(Mochi=[
        Task("Low early", 10, "low", preferred_time=time(8, 0)),
        Task("High untimed", 10, "high"),
        Task("Medium", 10, "medium", preferred_time=time(9, 0)),
        Task("High late", 10, "high", preferred_time=time(18, 0)),
    ])

    titles = [t.title for _, t in Scheduler(owner).sort_tasks(owner.get_all_tasks())]

    assert titles == ["High late", "High untimed", "Medium", "Low early"]


# Recurrence

def test_weekly_completed_on_due_day_is_next_due_in_seven_days():
    monday = date(2026, 11, 2)
    nxt = Task("Bath", 20, recurrence="weekly", due_date=monday).mark_complete(monday)
    assert nxt.due_date == date(2026, 11, 9)


def test_weekly_completed_over_a_week_late_skips_to_next_matching_weekday():
    monday = date(2026, 11, 2)
    late = Task("Bath", 20, recurrence="weekly", due_date=monday)
    assert late.mark_complete(date(2026, 11, 12)).due_date == date(2026, 11, 16)

    on_next_monday = Task("Bath", 20, recurrence="weekly", due_date=monday)
    assert on_next_monday.mark_complete(date(2026, 11, 9)).due_date == date(2026, 11, 16)


def test_daily_next_occurrence_crosses_year_end_and_copies_fields():
    task = Task("Meds", 5, "high", preferred_time=time(7, 30),
                due_date=date(2026, 12, 31), recurrence="daily")

    nxt = task.mark_complete(date(2026, 12, 31))

    assert nxt.due_date == date(2027, 1, 1)
    assert (nxt.title, nxt.priority, nxt.preferred_time, nxt.duration_minutes,
            nxt.recurrence) == ("Meds", "high", time(7, 30), 5, "daily")
    assert nxt.completed_dates == set()
    assert nxt.completed_dates is not task.completed_dates


def test_completing_weekly_task_twice_creates_only_one_next_occurrence():
    task = Task("Bath", 20, recurrence="weekly", due_date=date(2026, 11, 2))
    owner = make_owner(Mochi=[task])
    pet = owner.pets[0]
    scheduler = Scheduler(owner)

    scheduler.mark_task_complete(pet, task, DAY)
    assert scheduler.mark_task_complete(pet, task, DAY) is None
    assert len(pet.tasks) == 2


def test_weekly_task_without_due_date_is_rejected():
    with pytest.raises(ValueError):
        Task("Bath", 20, recurrence="weekly")


# Conflicts

def test_conflict_warnings_catch_partial_overlap_and_containment():
    owner = make_owner(
        Mochi=[Task("Long walk", 60, preferred_time=time(9, 0)),
               Task("Meds", 5, preferred_time=time(9, 15))],  # inside the walk
        Luna=[Task("Play", 30, preferred_time=time(9, 45))],  # overlaps end of walk
    )

    warnings = Scheduler(owner).conflict_warnings(DAY)

    assert len(warnings) == 2
    assert "Long walk" in warnings[0] and "Meds" in warnings[0]
    assert "both for Mochi" in warnings[0]
    assert "Long walk" in warnings[1] and "Play" in warnings[1]
    assert "Mochi and Luna" in warnings[1]


def test_three_tasks_at_same_time_give_one_warning_per_pair():
    owner = make_owner(Mochi=[Task(n, 10, preferred_time=time(9, 0)) for n in "ABC"])
    assert len(Scheduler(owner).conflict_warnings(DAY)) == 3


def test_conflict_warnings_ignore_untimed_completed_and_future_tasks():
    done = Task("Done", 10, preferred_time=time(9, 0))
    done.mark_complete(DAY)
    owner = make_owner(Mochi=[
        Task("Walk", 10, preferred_time=time(9, 0)),
        done,
        Task("Tomorrow", 10, preferred_time=time(9, 0), due_date=date(2026, 11, 7)),
        Task("Untimed", 10),
    ])
    assert Scheduler(owner).conflict_warnings(DAY) == []


def test_generate_schedule_moves_clashing_task_to_next_free_slot():
    owner = make_owner(Mochi=[Task("Meds", 20, preferred_time=time(9, 0)),
                              Task("Feed", 10, preferred_time=time(9, 0))])
    scheduler = Scheduler(owner)

    plan = scheduler.generate_schedule(DAY)

    assert [(e["task"].title, e["start"].time()) for e in plan] == [
        ("Feed", time(9, 0)), ("Meds", time(9, 10))]
    assert scheduler.detect_conflicts(plan) == []
    assert "was taken" in plan[1]["reason"]


# Filtering

def test_filter_tasks_unknown_pet_is_empty_and_no_filters_returns_all():
    owner = _owner_with_tasks()
    scheduler = Scheduler(owner)
    assert scheduler.filter_tasks(pet_name="Rex") == []
    assert len(scheduler.filter_tasks()) == 4


def test_filter_completion_is_checked_against_on_date():
    task = Task("Vet visit", 60)
    owner = make_owner(Mochi=[task])
    task.mark_complete(date(2026, 11, 5))
    scheduler = Scheduler(owner)

    assert scheduler.filter_tasks(completed=True, on_date=date(2026, 11, 5)) != []
    assert scheduler.filter_tasks(completed=True, on_date=DAY) == []
    assert scheduler.filter_tasks(completed=False, on_date=DAY) != []


# Empty lists and available time

def test_generate_schedule_with_no_tasks_is_empty():
    for owner in (Owner("Empty", 60), make_owner(Mochi=[])):
        scheduler = Scheduler(owner)
        assert scheduler.generate_schedule(DAY) == []
        assert scheduler.skipped == []
        assert scheduler.explain_schedule().startswith("No tasks scheduled")


def test_zero_available_minutes_skips_everything_with_reason():
    owner = make_owner(0, Mochi=[Task("Walk", 30), Task("Feed", 10)])
    scheduler = Scheduler(owner)

    assert scheduler.generate_schedule(DAY) == []
    assert len(scheduler.skipped) == 2
    assert all("only 0 min" in e["reason"] for e in scheduler.skipped)


def test_time_limit_keeps_higher_priority_and_allows_exact_fit():
    owner = make_owner(30, Mochi=[Task("Low", 15, "low"),
                                  Task("High", 20, "high"),
                                  Task("Medium", 10, "medium")])  # fits exactly in the last 10
    scheduler = Scheduler(owner)

    plan = scheduler.generate_schedule(DAY)

    assert sorted(e["task"].title for e in plan) == ["High", "Medium"]
    assert [e["task"].title for e in scheduler.skipped] == ["Low"]
    assert sum(e["task"].duration_minutes for e in plan) <= owner.available_minutes


def test_generate_schedule_handles_early_future_and_late_tasks():
    owner = make_owner(240, Mochi=[
        Task("Early", 10, preferred_time=time(6, 0)),
        Task("Future", 10, due_date=date(2026, 11, 7)),
        Task("Late", 60, preferred_time=time(23, 30)),
    ])
    scheduler = Scheduler(owner)

    plan = scheduler.generate_schedule(DAY)

    assert [(e["task"].title, e["start"].time()) for e in plan] == [("Early", time(8, 0))]
    assert "before the day starts" in plan[0]["reason"]
    assert [e["task"].title for e in scheduler.skipped] == ["Late"]
    assert "midnight" in scheduler.skipped[0]["reason"]


def test_negative_available_time_is_rejected():
    with pytest.raises(ValueError):
        Owner("Jorn").update_available_time(-1)
