# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.
1. A user should be able to add/update personal information in the app as well and their pet's information
2. A user should be able to create and track their pet care tasks (walking, grooming, feeding, etc.) and the duratiion/priority of said tasks.
3. Users should be able to generate a pet care schedule, day by day, which incldues times, tasks, task priority, and prefrences.
- What classes did you include, and what responsibilities did you assign to each?
My 4 main classes are gonna be owner, pet, task, and scheduler. Owner stores the owner’s name, available time, preferences, and list of pets.
Pet stores each pet’s name, species, preferences, and care tasks. 
Task represents an activity like walking, feeding, or grooming and stores its duration, priority, preferred time, due date, recurrence, and completion status. 
Scheduler uses the owner’s information and their pets’ tasks to generate a daily care plan, prioritize tasks, check for scheduling conflicts, and explain scheduling decisions.


#### Owner
Attributes:
- name: the owner's name
- available_minutes: how much time the owner has for pet care that day
- preferences: the owner's pet care preferences
- pets: a list of the owner's Pet objects

Methods:
- add_pet(): adds a pet to the owner's list
- update_preferences(): updates the owner's preferences
- update_available_time(): changes the time available for pet care

#### Pet
Attributes:
- name: the pet's name
- species: the type of animal
- preferences: food, toy, and activity preferences
- tasks: a list of the pet's Task objects

Methods:
- add_task(): adds a care task to the pet's list
- remove_task(): removes a care task
- update_info(): updates the pet's information and preferences

#### Task
Attributes:
- title: the name of the care activity
- duration_minutes: how long the task takes
- priority: low, medium, or high importance
- preferred_time: the preferred start time, if any
- due_date: the date the task is due
- recurrence: whether the task happens once, daily, or weekly
- completed: whether the task has been completed

Methods:
- update_details(): updates the task's information
- mark_complete(): marks the task as completed
- is_due(): checks whether the task is due on a given date

#### Scheduler
Attributes:
- owner: the Owner object containing the pets, preferences, and available time
- day_start: the starting time for the daily schedule

Methods:
- get_due_tasks(): collects tasks due on the requested date
- sort_tasks(): sorts tasks by priority
- detect_conflicts(): checks whether scheduled task times overlap
- generate_schedule(): selects and schedules tasks using available time and preferences
- explain_schedule(): explains why tasks were included or skipped
---

**b. Design changes**

- Did your design change during implementation?
Yes it did, my coding agent recognized a few logic/relationships errors that needed fixing.
- If yes, describe at least one change and why you made it.
One change I made was implementing a (pet,task) tuple, which allows pets to stay with their respective tasks. Previoulsy when multiple tasks got merged, it was not possible to tell which tasks went with what pets.

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
