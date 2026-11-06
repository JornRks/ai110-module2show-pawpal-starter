from datetime import date, time
from pawpal_system import Owner, Pet, Task, Scheduler


def print_tasks(heading, pairs):
    """Print a list of (pet, task) pairs under a heading."""
    print(f"\n{heading}")
    print("-" * 60)
    if not pairs:
        print("  (none)")
    for pet, task in pairs:
        when = task.preferred_time.strftime("%H:%M") if task.preferred_time else "--:--"
        status = "done" if task.is_completed else "todo"
        print(
            f"  {when} | {pet.name}: {task.title} "
            f"({task.priority}, {task.recurrence}, due {task.due_date}, {status})"
        )


def main():
    today = date.today()

    # Create an owner and two pets.
    owner = Owner(name="Jorn", available_minutes=120)

    dog = Pet(name="Mochi", species="dog")
    cat = Pet(name="Luna", species="cat")

    owner.add_pet(dog)
    owner.add_pet(cat)

    # Add tasks deliberately OUT of time order to test sorting.
    evening_walk = Task("Evening walk", 30, "high", preferred_time=time(18, 30),
                        due_date=today, recurrence="daily")
    feed_luna = Task("Feed Luna", 10, "high", preferred_time=time(9, 0),
                     due_date=today, recurrence="daily")
    brush_mochi = Task("Brush Mochi", 15, "medium", preferred_time=time(13, 5),
                       due_date=today, recurrence="weekly")
    litter = Task("Clean litter box", 10, "medium", due_date=today)  # once, no time
    morning_walk = Task("Morning walk", 30, "high", preferred_time=time(8, 0),
                        due_date=today, recurrence="daily")

    # Two tasks at the SAME time to test conflict detection:
    # one for a different pet (overlaps Feed Luna), one for the same pet (overlaps Evening walk).
    give_meds = Task("Give Mochi meds", 5, "high", preferred_time=time(9, 0), due_date=today)
    play_fetch = Task("Play fetch", 20, "low", preferred_time=time(18, 45), due_date=today)

    dog.add_task(evening_walk)
    cat.add_task(feed_luna)
    dog.add_task(brush_mochi)
    cat.add_task(litter)
    dog.add_task(morning_walk)
    dog.add_task(give_meds)
    dog.add_task(play_fetch)

    scheduler = Scheduler(owner=owner, day_start=time(8, 0))

    print_tasks("All tasks (in the order they were added)", owner.get_all_tasks())
    print_tasks("Sorted by preferred time", scheduler.sort_by_time(owner.get_all_tasks()))

    # --- Conflict detection: warn, don't crash ------------------------------------
    print(f"\nConflict check — {today}")
    print("-" * 60)
    warnings = scheduler.conflict_warnings(today)
    for w in warnings:
        print(f"  {w}")
    if not warnings:
        print("  No conflicts.")

    # --- Recurring tasks: completing one creates the next occurrence ------------
    print("\nCompleting tasks")
    print("-" * 60)
    for pet, task in [(dog, morning_walk), (cat, feed_luna), (dog, brush_mochi), (cat, litter)]:
        next_task = scheduler.mark_task_complete(pet, task, today)
        if next_task:
            print(f"  {task.title} ({task.recurrence}) done -> next one due {next_task.due_date}")
        else:
            print(f"  {task.title} ({task.recurrence}) done -> no repeat")

    # Completing the same task twice must not create a second copy.
    again = scheduler.mark_task_complete(dog, morning_walk, today)
    print(f"  Morning walk completed again -> new task created? {again is not None}")

    print_tasks("Only Mochi's tasks", scheduler.filter_tasks(pet_name="mochi"))
    print_tasks("Completed today", scheduler.filter_tasks(completed=True, on_date=today))
    print_tasks(
        "Not completed yet, incl. upcoming occurrences (sorted by time)",
        scheduler.sort_by_time(scheduler.filter_tasks(completed=False, on_date=today)),
    )
    print_tasks("Still due today (sorted by time)",
                scheduler.sort_by_time(scheduler.get_due_tasks(today)))

    # Generate and display the schedule for what's still due today.
    scheduler.generate_schedule(today)
    print(f"\nToday's Schedule — {today}")
    print("-" * 60)
    print(scheduler.explain_schedule())


if __name__ == "__main__":
    main()
