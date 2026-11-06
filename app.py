from datetime import date, time

import streamlit as st

from pawpal_system import Owner, Pet, Scheduler, Task

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

with st.expander("Scenario", expanded=False):
    st.markdown(
        """
**PawPal+** is a pet care planning assistant. It helps a pet owner plan care tasks
for their pet(s) based on constraints like time, priority, and preferences.
"""
    )

# --- Session "vault" ---------------------------------------------------------
# Streamlit reruns this script on every interaction, so the Owner is created
# once per browser session and reused on every later run.
if "owner" not in st.session_state:
    st.session_state.owner = Owner("Jordan", available_minutes=60)
if "scheduler" not in st.session_state:
    st.session_state.scheduler = None  # last generated schedule, if any

owner: Owner = st.session_state.owner

# --- Owner -------------------------------------------------------------------
st.subheader("Owner")
col1, col2, col3 = st.columns(3)
with col1:
    owner.name = st.text_input("Owner name", value=owner.name)
with col2:
    owner.update_available_time(
        int(st.number_input("Available minutes today", min_value=0, max_value=1440,
                            value=owner.available_minutes, step=5))
    )
with col3:
    day_start = st.time_input("Day starts at", value=time(8, 0))

# --- Pets --------------------------------------------------------------------
st.subheader("Pets")
with st.form("add_pet", clear_on_submit=True):
    col1, col2 = st.columns(2)
    with col1:
        pet_name = st.text_input("Pet name", value="Lucy")
    with col2:
        species = st.selectbox("Species", ["dog", "cat", "other"])
    if st.form_submit_button("Add pet"):
        name = pet_name.strip()
        if not name:
            st.error("Pet name cannot be empty.")
        elif any(p.name.lower() == name.lower() for p in owner.pets):
            st.error(f"You already have a pet named {name}.")
        else:
            owner.add_pet(Pet(name, species))
            st.success(f"Added {name}.")

if not owner.pets:
    st.info("No pets yet. Add one above.")
    st.stop()  # nothing below works without a pet

# --- Tasks -------------------------------------------------------------------
st.subheader("Tasks")
with st.form("add_task", clear_on_submit=True):
    pet_choice = st.selectbox("For pet", [p.name for p in owner.pets])
    col1, col2, col3 = st.columns(3)
    with col1:
        task_title = st.text_input("Task title", value="Morning walk")
    with col2:
        duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
    with col3:
        priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)

    col1, col2, col3 = st.columns(3)
    with col1:
        recurrence = st.selectbox("Repeats", ["once", "daily", "weekly"])
    with col2:
        due = st.date_input("Due / starts on", value=date.today())
    with col3:
        use_time = st.checkbox("Has preferred time")
        preferred = st.time_input("Preferred time", value=time(8, 0))

    if st.form_submit_button("Add task"):
        pet = next(p for p in owner.pets if p.name == pet_choice)
        try:
            pet.add_task(Task(
                title=task_title,
                duration_minutes=int(duration),
                priority=priority,
                preferred_time=preferred if use_time else None,
                due_date=due,
                recurrence=recurrence,
            ))
            st.success(f"Added '{task_title}' for {pet.name}.")
        except ValueError as e:
            st.error(str(e))

# A throwaway Scheduler gives the task list access to sorting and filtering.
viewer = Scheduler(owner, day_start=day_start)
today = date.today()


def task_status(task: Task) -> str:
    """Short, human-readable state of one task occurrence."""
    if task.is_completed:
        return "✅ Done"
    if task.due_date is None or task.due_date == today:
        return "Due today"
    return "⚠️ Overdue" if task.due_date < today else "Upcoming"


st.markdown("**All tasks**")
col1, col2, col3 = st.columns(3)
with col1:
    pet_filter = st.selectbox("Show pet", ["All pets"] + [p.name for p in owner.pets])
with col2:
    status_filter = st.selectbox("Status", ["To do", "Done", "All"])
with col3:
    sort_mode = st.radio("Sort by", ["Time of day", "Priority"], horizontal=True)

pairs = viewer.filter_tasks(pet_name=None if pet_filter == "All pets" else pet_filter)
if status_filter != "All":
    pairs = [(p, t) for p, t in pairs if t.is_completed == (status_filter == "Done")]
pairs = viewer.sort_by_time(pairs) if sort_mode == "Time of day" else viewer.sort_tasks(pairs)

if pairs:
    st.table([
        {
            "Time": t.preferred_time.strftime("%H:%M") if t.preferred_time else "Any time",
            "Pet": p.name,
            "Task": t.title,
            "Minutes": t.duration_minutes,
            "Priority": t.priority,
            "Repeats": t.recurrence,
            "Due": t.due_date.isoformat() if t.due_date else "—",
            "Status": task_status(t),
        }
        for p, t in pairs
    ])
else:
    st.caption("No tasks match these filters.")

open_tasks = [(p, t) for p, t in owner.get_all_tasks() if not t.is_completed]
if open_tasks:
    with st.form("complete_task"):
        choice = st.selectbox(
            "Mark a task complete",
            range(len(open_tasks)),
            format_func=lambda i: f"{open_tasks[i][0].name}: {open_tasks[i][1].title}"
            + (f" (due {open_tasks[i][1].due_date})" if open_tasks[i][1].due_date else ""),
        )
        if st.form_submit_button("Mark complete"):
            pet, task = open_tasks[choice]
            nxt = viewer.mark_task_complete(pet, task, today)
            msg = f"Marked '{task.title}' done for {pet.name}."
            if nxt is not None:
                msg += f" Next one added for {nxt.due_date:%A, %b %d}."
            st.session_state.flash = msg  # shown after the rerun refreshes the table
            st.rerun()

if "flash" in st.session_state:
    st.success(st.session_state.pop("flash"))

st.divider()

# --- Schedule ----------------------------------------------------------------
st.subheader("Build Schedule")
plan_date = st.date_input("Plan for", value=date.today())

# Live conflict check: shown before and after generating, so the owner can
# fix clashing preferred times at the source.
warnings = Scheduler(owner, day_start=day_start).conflict_warnings(plan_date)
if warnings:
    st.warning(
        f"**{len(warnings)} time clash{'es' if len(warnings) > 1 else ''} on "
        f"{plan_date:%A, %b %d}.** You can't do two things at once, so PawPal+ "
        "will move the lower-priority task to the next free slot. "
        "Edit a preferred time if you'd rather choose yourself."
    )
    for w in warnings:
        st.markdown(f"- {w.removeprefix('WARNING: ')}")
else:
    st.success("No time clashes between preferred times for this day.")

if st.button("Generate schedule", type="primary"):
    scheduler = Scheduler(owner, day_start=day_start)
    scheduler.generate_schedule(plan_date)
    st.session_state.scheduler = scheduler

scheduler = st.session_state.scheduler
if scheduler is not None:
    used = sum(e["task"].duration_minutes for e in scheduler.scheduled)
    budget = scheduler.owner.available_minutes
    st.progress(min(used / budget, 1.0) if budget else 0.0,
                text=f"{used} of {budget} available minutes planned")

    moved = [e for e in scheduler.scheduled
             if e["task"].preferred_time and e["start"].time() != e["task"].preferred_time]
    for e in moved:
        st.info(
            f"🕒 Moved **{e['pet'].name}: {e['task'].title}** from "
            f"{e['task'].preferred_time:%H:%M} to **{e['start']:%H:%M}** ({e['reason']})."
        )

    if scheduler.scheduled:
        st.success(f"Planned {len(scheduler.scheduled)} task(s).")
        st.markdown("**Scheduled**")
        st.table([
            {
                "Time": f"{e['start']:%H:%M}–{e['end']:%H:%M}",
                "Pet": e["pet"].name,
                "Task": e["task"].title,
                "Why": e["reason"],
            }
            for e in scheduler.scheduled
        ])
    else:
        st.info("Nothing was scheduled for this date.")

    if scheduler.skipped:
        st.warning(
            f"**{len(scheduler.skipped)} task(s) didn't fit.** Add more available "
            "minutes or lower the priority of something else to fit them in."
        )
        st.table([
            {"Pet": e["pet"].name, "Task": e["task"].title, "Why": e["reason"]}
            for e in scheduler.skipped
        ])

    with st.expander("Plain-text explanation"):
        st.text(scheduler.explain_schedule())
