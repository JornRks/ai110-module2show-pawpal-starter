# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## 🖥️ Sample Output


```
Today's Schedule — 2026-11-06
--------------------------------------------------
08:00–08:30 | Lucy: Morning walk (30 min, high priority)
09:00–09:10 | Titus: Feed Titus (10 min, high priority)
10:00–10:15 | Lucy: Brush Lucy (15 min, medium priority)

```

## 🧪 Testing PawPal+

```bash
# Run the full test suite:
python -m pytest

```
Test Descriptions: 
The tests verify chronological task sorting, creation of the next daily task after completion, and detection of tasks scheduled at the same time.


Sample test output:

```
====================================================================== test session starts =======================================================================
platform win32 -- Python 3.14.6, pytest-9.0.3, pluggy-1.6.0
rootdir: C:\Users\Jorn Rutkis\Documents\ai110-module2show-pawpal-starter
configfile: pytest.ini
testpaths: tests
plugins: anyio-4.12.1
collected 25 items                                                                                                                                                

tests\test_pawpal.py .........................                                                                                                              [100%]

======================================================================= 25 passed in 0.04s =======================================================================

```

Confidence:
Based on the pytests I ran, my confidence sits at 4/5. This is because they all sucsessfully passed, yet not all edge cases could be covered.

### Features

- **Priority-based planning:** `generate_schedule()` places due tasks in order of priority → preferred time → shortest duration, until the owner's available minutes run out. Tasks that don't fit are skipped with a reason.
- **Sorting by time:** `sort_by_time()` orders tasks by their "HH:MM" preferred time. Untimed tasks go last, and ties keep their original order.
- **Filtering:** `filter_tasks()` narrows the list by pet name (case-insensitive) and/or completion status. Filters combine with AND.
- **Conflict warnings:** `conflict_warnings()` turns each preferred time into a time window and reports every overlapping pair, for the same pet or for different pets. Back-to-back tasks are not flagged.
- **Conflict resolution:** while building the plan, a task whose slot is taken is moved to the next free gap (`_first_free_start()`). A task that would run past midnight is skipped.
- **Daily recurrence:** completing a daily task creates a new task due the next day. Dates use `timedelta`, so month and year ends are handled correctly.
- **Weekly recurrence:** completing a weekly task creates the next one on the same weekday, even if this one was completed late.
- **No duplicate occurrences:** completing a task twice never creates a second next occurrence.
- **Overdue carry-over:** an unfinished task stays due after its due date instead of disappearing.
- **Explained plans:** every scheduled or skipped task records why. `explain_schedule()` prints the plan and the total minutes used.
- **Input validation:** invalid tasks are rejected with a `ValueError`. Examples: an empty title, a duration of 0 or less, an unknown priority or recurrence, a weekly task without a due date.

## 📐 Smarter Scheduling

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Task sorting | `Scheduler.sort_by_time()`, `Scheduler.sort_tasks()` | By "HH:MM" preferred time (untimed tasks last); the planner sorts by priority, then time, then duration |
| Filtering | `Scheduler.filter_tasks()`, `Scheduler.get_due_tasks()` | By pet name and/or completion status; due-today tasks only |
| Conflict handling | `Scheduler.conflict_warnings()`, `Scheduler.detect_conflicts()` | Warns about overlapping time slots (same pet or different pets) without crashing |
| Recurring tasks | `Scheduler.mark_task_complete()`, `Task.mark_complete()`, `Task.next_occurrence()`, `Task.is_due()` | Completing a daily/weekly task creates its next occurrence |

## 📸 Demo Walkthrough


1. **Set up the owner.** Run `streamlit run app.py`. Enter the owner's name, how many minutes they have for pet care today, and when their day starts.
2. **Add a pet.** Enter a name (e.g. "Lucy") and a species, then click **Add pet**. Duplicate and empty names are rejected.
3. **Add tasks.** Choose the pet, then enter a title, a duration, a priority, how often it repeats (once / daily / weekly), a due date and an optional preferred time. Click **Add task**. Invalid input shows an error instead of crashing.
4. **Browse the task list.** All tasks appear in one table with a status for each (Due today, Upcoming, Overdue, Done). Use **Show pet** and **Status** to filter. Use **Sort by** to order by *Time of day* (`sort_by_time`, untimed tasks last) or by *Priority* (`sort_tasks`).
5. **Mark a task complete.** Choose a task under **Mark a task complete**. A repeating task gets its next occurrence right away, and a message says when it's due (e.g. "Next one added for Saturday, Nov 07").
6. **Check for conflicts.** Choose a date under **Build Schedule**. If two preferred times overlap, a yellow warning lists each pair and the pet(s) involved, and says the lower-priority task will be moved. If nothing overlaps, a green message confirms it.
7. **Generate the schedule.** Click **Generate schedule** to see:
   - a progress bar of minutes planned out of minutes available
   - a note for each task moved from its preferred time
   - a table of scheduled tasks, each with the reason for its placement
   - a warning listing any tasks that didn't fit
   - a plain-text explanation, under an expander

**Example workflow:** 
1. add Lucy 
2. add "Give meds" (high, 09:00, 20 min) and "Feed" (low, 09:00, 10 min)
3. conflict warning appears 
4. generate the schedule 
5. Meds stays at 09:00 
6. Feed moves to 09:20 with a note explaining why.

**Sample CLI output** 

```
Sorted by preferred time
------------------------------------------------------------
  08:00 | Lucy: Morning walk (high, daily, due 2026-11-06, todo)
  09:00 | Lucy: Give Lucy meds (high, once, due 2026-11-06, todo)
  09:00 | Titus: Feed Titus (high, daily, due 2026-11-06, todo)
  13:05 | Lucy: Brush Lucy (medium, weekly, due 2026-11-06, todo)
  18:30 | Lucy: Evening walk (high, daily, due 2026-11-06, todo)
  18:45 | Lucy: Play fetch (low, once, due 2026-11-06, todo)
  --:-- | Titus: Clean litter box (medium, once, due 2026-11-06, todo)

Conflict check — 2026-11-06
------------------------------------------------------------
  WARNING: 'Give Lucy meds' (09:00-09:05) overlaps 'Feed Titus' (09:00-09:10), Lucy and Titus.
  WARNING: 'Evening walk' (18:30-19:00) overlaps 'Play fetch' (18:45-19:05), both for Lucy.

Completing tasks
------------------------------------------------------------
  Morning walk (daily) done -> next one due 2026-11-07
  Feed Titus (daily) done -> next one due 2026-11-07
  Brush Lucy (weekly) done -> next one due 2026-11-13
  Clean litter box (once) done -> no repeat
  Morning walk completed again -> new task created? False

Today's Schedule — 2026-11-06
------------------------------------------------------------
Scheduled:
  09:00-09:05  Lucy: Give Lucy meds (high priority, at its preferred time)
  18:30-19:00  Lucy: Evening walk (high priority, at its preferred time)
  19:00-19:20  Lucy: Play fetch (low priority, preferred 18:45 was taken, so moved to the next free slot)
Total: 55 of 120 available minutes used.
```


