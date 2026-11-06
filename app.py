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
        pet_name = st.text_input("Pet name", value="Mochi")
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

for pet in owner.pets:
    st.markdown(f"**{pet.name}** ({pet.species})")
    if pet.tasks:
        st.table([
            {
                "Task": t.title,
                "Minutes": t.duration_minutes,
                "Priority": t.priority,
                "Preferred time": t.preferred_time.strftime("%H:%M") if t.preferred_time else "—",
                "Repeats": t.recurrence,
                "Due / starts": t.due_date.isoformat() if t.due_date else "—",
            }
            for t in pet.tasks
        ])
    else:
        st.caption("No tasks yet.")

st.divider()

# --- Schedule ----------------------------------------------------------------
st.subheader("Build Schedule")
plan_date = st.date_input("Plan for", value=date.today())

if st.button("Generate schedule", type="primary"):
    scheduler = Scheduler(owner, day_start=day_start)
    scheduler.generate_schedule(plan_date)
    st.session_state.scheduler = scheduler

scheduler = st.session_state.scheduler
if scheduler is not None:
    if scheduler.scheduled:
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
        st.markdown("**Skipped**")
        st.table([
            {"Pet": e["pet"].name, "Task": e["task"].title, "Why": e["reason"]}
            for e in scheduler.skipped
        ])

    conflicts = scheduler.detect_conflicts(scheduler.scheduled)
    if conflicts:
        for a, b in conflicts:
            st.warning(f"Overlap: {a['task'].title} and {b['task'].title}")

    with st.expander("Plain-text explanation"):
        st.text(scheduler.explain_schedule())
