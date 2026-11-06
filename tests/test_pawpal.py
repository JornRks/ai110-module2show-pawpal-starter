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
