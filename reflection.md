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
The constraints my scheduler follows are: owners available time, task duration, priority, due date, completion status, and perferred start time. It prioritizes high priority tasks and moves overlapping tasks to a available times. Tasks that cannot be fit in the owners available time slot are skipped but explained in the app.
- How did you decide which constraints mattered most?
I chose that available time and task priority are what matter most, as the planner was created to aim busy pet owners, and it had to be realistic. This meant the most important tasks needed to be prioritized and start times needed to be flexable to fit an owners available time slot. 

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?
I kept the a orginal 'more complex' sorting method, which converts preferred times into zero-padded "HH:MM" strings. AI suggested comparing time objects directly to avoid conversion, but I chose the string version to match Phase 4, step 2s format. This requires extra conversion and ignores seconds, but the performance difference is negligible for a small number of pet care tasks, and minute-level precision is sufficient for planning walks, feeding, and grooming.
---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
I utalized Claude in VS Code to brainstrom during my design process, and then eventually turn these ideas into a Mermaid UML design. Claude also helped me generate my class skeletons, come up with and implement more efficent scheduling logic, review my relationships between my proposed/developed classes, and generate my automated pytests. 
I would say the most useful/effective features were my agents ability to creat effective and comprehensive pytests for my testing phase. 
Having seperate chats also allowed me to stay very organized as my core implementation, algorithmic planning, and testing phases were all in seperate chats. This ensured my agent never got 'confused' and interacted with other files when it shouldnt have.
- What kinds of prompts or questions were most helpful?
The most helpful prompts were ones that explained what the agent was doing, along with why it was doing it. For example, when I asked Claude to review my algorthmic methods, it explained what changes should be made, and in doing so, provided explanations as to why these improved algorthims were better and what they were doing for the program. This allowed me to actually learn from the agent. 

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
One of these moments was when Claude suggested I change my "HH:MM" string-based sorting method. It was suggested to compare time-objects directly. While this slightly imrpoved efficency and visibilty (of code/what its doing) I chose to keep the orginal as it was mentioned in Phase 4, part 2.
- How did you evaluate or verify what the AI suggested?
I evaluated the suggestion by comparing both versions and reviewing Claudes explanation of  behavior. The alternative avoids string conversion and considers seconds, but minute-level precision is good enough for the app. I also checked the sorting test results to verify that the original method returned tasks in chronological order.

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?
I tested whether tasks are sorted chronologically, completing a daily task creates a new task for the following day, and tasks scheduled at the same time trigger a conflict warning. These tests were important because incorrect ordering, missing recurring tasks, or unnoticed conflicts could make the daily plan unreliable.

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?
I would rate confidence level a 4 out of 5 because all tests in my suite passed. However, passing tests does not guarantee that every situation is covered. With more time, I would expand testing around tasks near midnight, recurring tasks across month and year boundaries, and repeated button clicks in Streamlit to check for accidental duplicates.

---

## 5. Reflection

**a. What went well**

- The part of this projected that went well, and what im pleased with is how smoothly I was able to trasnfer from an idea/very small baseline to pawpal_system logic layer. Giving Claude my ideas and classes, then generating a Mermaid UML, and then a class skeleton was very simple. This also allowed me to learn how proper program development should look using an agent and will be carried with me in the future.

**b. What you would improve**

- One thing I would improve is schedule reccomendations that could be made by the scheduler. Rather than flat out skipping/excluding tasks that dont fit in the schedule, the scheduler could reccomend shortening other tasks marginally to fit in the skipped task.

**c. Key takeaway**

- My key takeaway from this project is the proper workflow when designing, building, and integrating a program while using an AI agent. Like mentioned in the 'What went well' section, this project allowed me to apply a coding agent and also learn from it during the building process. I also learned that I am responsible for guiding the design, reviewing AI suggestions, and verifying that the final program meets the requirements. This will enable me to produce more impressive programs from scratch in the future using these skills. 
