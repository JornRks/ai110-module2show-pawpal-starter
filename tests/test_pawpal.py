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
