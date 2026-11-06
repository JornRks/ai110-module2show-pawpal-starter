from datetime import date, time
from pawpal_system import Owner, Pet, Task, Scheduler


def main():
    today = date.today()

    # Create an owner and two pets.
    owner = Owner(name="Jorn", available_minutes=90)

    dog = Pet(name="Mochi", species="dog")
    cat = Pet(name="Luna", species="cat")

    owner.add_pet(dog)
    owner.add_pet(cat)

    # Create three tasks with different preferred times.
    walk = Task(
        title="Morning walk",
        duration_minutes=30,
        priority="high",
        preferred_time=time(8, 0),
        due_date=today,
    )

    feeding = Task(
        title="Feed Luna",
        duration_minutes=10,
        priority="high",
        preferred_time=time(9, 0),
        due_date=today,
    )

    grooming = Task(
        title="Brush Mochi",
        duration_minutes=15,
        priority="medium",
        preferred_time=time(10, 0),
        due_date=today,
    )

    dog.add_task(walk)
    cat.add_task(feeding)
    dog.add_task(grooming)

    # Generate and display the schedule.
    scheduler = Scheduler(owner=owner, day_start=time(8, 0))
    schedule = scheduler.generate_schedule(today)

    print(f"Today's Schedule — {today}")
    print("-" * 50)

    for entry in schedule:
        start = entry["start"].strftime("%H:%M")
        end = entry["end"].strftime("%H:%M")
        pet = entry["pet"]
        task = entry["task"]

        print(
            f"{start}–{end} | {pet.name}: {task.title} "
            f"({task.duration_minutes} min, {task.priority} priority)"
        )


if __name__ == "__main__":
    main()
