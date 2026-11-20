from datetime import datetime, timedelta
import threading
import time
import winsound
import json
import os
BASE_DIR=os.path.dirname(os.path.abspath(__file__))
TASKS_FILE=os.path.join(BASE_DIR,"tasks.json")
print("TASK STORAGE LOCATION:",TASKS_FILE)
# =================================
# JSON STORAGE SYSTEM
# =================================

def load_tasks():

    if not os.path.exists(TASKS_FILE):
        return []

    with open(TASKS_FILE, "r") as file:
        saved_tasks = json.load(file)

    for task in saved_tasks:

        task["reminder"] = datetime.fromisoformat(
            task["reminder"]
        )

        task["alarm_stop"] = threading.Event()

    return saved_tasks


def save_tasks():
    print("Saving Function Called")

    saved_tasks = []

    for task in tasks:

        saved_tasks.append({

            "name": task["name"],
            "status": task["status"],
            "reminder": task["reminder"].isoformat(),
            "reminded": task["reminded"],
            "reminder_type": task["reminder_type"],
            "duration_minutes": task.get("duration_minutes", None)

        })

    try:
        with open(TASKS_FILE, "w") as file:
            json.dump(saved_tasks, file, indent=4)
            print("Tasks saved succesfully!")
            return True
    except (OSError, TypeError, KeyError) as error:
        print("ERROR:Could not save tasks to file:", error)
        return False

tasks = load_tasks()
tasks_lock = threading.Lock()

ALARM_DURATION_SECONDS = 2*60*60

# =================================
# ALARM SYSTEM
# =================================

def play_alarm(task):

    stop_signal = task["alarm_stop"]
    start_time=time.monotonic()
    
    

    while time.monotonic() - start_time < ALARM_DURATION_SECONDS:

        # Check whether the user completed the task
        if stop_signal.is_set():
            break

        # First beep
        winsound.Beep(1000, 300)

        if stop_signal.is_set():
            break

        # Short pause
        if stop_signal.wait(0.3):
            break

        # Second beep
        winsound.Beep(1000, 300)

        if stop_signal.is_set():
            break

        # Longer pause
        if stop_signal.wait(0.7):
            break


# =================================
# BACKGROUND REMINDER SYSTEM
# =================================

def check_reminders():

    while True:

        due_tasks = []
        current_time = datetime.now()

        with tasks_lock:

            for task in tasks:

                if (task["status"] == "PENDING" and
                        not task["reminded"] and
                        current_time >= task["reminder"]):

                    task["reminded"] = True
                    due_tasks.append(task)
                    if due_tasks:
                        save_tasks()

        # Start a separate alarm thread for each due task
        for task in due_tasks:

            print("\n==============================", flush=True)
            print("       TASKPILOT REMINDER!", flush=True)
            print("Your Task:", task["name"], flush=True)
            print("Time to get it done!", flush=True)
            print("==============================", flush=True)

            alarm_thread = threading.Thread(
                target=play_alarm,
                args=(task,),
                daemon=True
            )

            alarm_thread.start()

        time.sleep(1)


# =================================
# START BACKGROUND THREAD
# =================================

reminder_thread = threading.Thread(
    target=check_reminders,
    daemon=True
)

reminder_thread.start()


# =================================
# MAIN PROGRAM
# =================================

while True:

    print("\n==============================")
    print("         TASKPILOT")
    print("   Your Daily Work Assistant")
    print("==============================")

    print("1. Add a Task")
    print("2. View Tasks")
    print("3. Complete a Task")
    print("4. Delete Task")
    print("5. Exit")

    choice = input("Enter your choice: ")


    # =================================
    # ADD TASK
    # =================================

    if choice == "1":

        task_name = input("Enter your task: ")

        if not task_name.strip():
            print("Task name cannot be empty!")
            continue

        print("\nChoose Reminder Type:")
        print("1. Remind me after a duration")
        print("2. Remind me at a specific time")

        reminder_choice = input("Enter your choice: ")

        try:

            # COUNTDOWN REMINDER

            if reminder_choice == "1":

                minutes = int(
                    input("Remind me in how many minutes? ")
                )

                if minutes <= 0:

                    print("Please enter a positive number!")
                    continue

                reminder_time = datetime.now() + timedelta(
                    minutes=minutes
                )

                reminder_type = "Countdown"
                duration_minutes=minutes


            # CLOCK-TIME REMINDER

            elif reminder_choice == "2":

                time_text = input(
                    "Enter reminder time (HH:MM, 24-hour format): "
                )

                selected_time = datetime.strptime(
                    time_text, "%H:%M"
                ).time()

                now = datetime.now()

                reminder_time = datetime.combine(
                    now.date(), selected_time
                )

                if reminder_time <= now:

                    reminder_time += timedelta(days=1)

                reminder_type = "Clock Time"
                duration_minutes=None


            else:

                print("Invalid reminder choice!")
                continue


            # SAVE TASK

            with tasks_lock:

                tasks.append({

                    "name": task_name,
                    "status": "PENDING",
                    "reminder": reminder_time,
                    "reminded": False,
                    "reminder_type": reminder_type,
                    "duration_minutes": duration_minutes,
                    "alarm_stop": threading.Event()

                })

            if save_tasks():
                print("\nTask added and saved successfully!")
            else:
                print("\nTask added to memory, but not saved to file!")

            print("\nTask added successfully!")
            print("Reminder Type:", reminder_type)

            print(
                "Reminder Set For:",
                reminder_time.strftime("%Y-%m-%d %I:%M %p")
            )


        except ValueError:

            print("Invalid input! Please try again.")


    # =================================
    # VIEW TASKS
    # =================================

    elif choice == "2":

        with tasks_lock:
            current_tasks = list(tasks)

        if not current_tasks:

            print("\nNo tasks available!")

        else:

            print("\nYOUR TASKS:")

            for number, task in enumerate(
                    current_tasks, start=1):

                print(
                    number,
                    ".",
                    task["name"],
                    "-",
                    task["status"],
                    "|",
                    task["reminder"].strftime("%Y-%m-%d %I:%M %p")
                )


    # =================================
    # COMPLETE TASK
    # =================================

    elif choice == "3":

        with tasks_lock:
            current_tasks = list(tasks)

        if not current_tasks:

            print("No tasks available!")

        else:

            print("\nYOUR TASKS:")

            for number, task in enumerate(
                    current_tasks, start=1):

                print(
                    number,
                    ".",
                    task["name"],
                    "-",
                    task["status"]
                )

            try:

                task_number = int(
                    input("Enter task number to complete: ")
                )

                with tasks_lock:

                    if 1 <= task_number <= len(tasks):

                        selected_task = tasks[task_number - 1]

                        if selected_task["status"] == "PENDING":

                            selected_task["status"] = "COMPLETED"
                            save_tasks()

                            # STOP THE ALARM
                            selected_task["alarm_stop"].set()

                            print("Task marked as completed!")
                            print("Alarm stopped!")

                        else:

                            print("This task is already completed!")

                    else:

                        print("Invalid task number!")

            except ValueError:

                print("Please enter a number!")


    # =================================
    # DELETE TASK
    # =================================

    elif choice == "4":

        with tasks_lock:
            current_tasks = list(tasks)

        if not current_tasks:

            print("No tasks available!")

        else:

            print("\nYOUR TASKS:")

            for number, task in enumerate(
                    current_tasks, start=1):

                print(
                    number,
                    ".",
                    task["name"],
                    "-",
                    task["status"]
                )

            try:

                task_number = int(
                    input("Enter task number to delete: ")
                )

                with tasks_lock:

                    if 1 <= task_number <= len(tasks):

                        selected_task = tasks.pop(task_number - 1)
                        save_tasks()

                        # STOP ALARM IF TASK IS DELETED
                        selected_task["alarm_stop"].set()

                        print("Task deleted successfully!")

                    else:

                        print("Invalid task number!")

            except ValueError:

                print("Please enter a number!")


    # =================================
    # EXIT
    # =================================

    elif choice == "5":

        print("Thank you for using TASKPILOT!")
        print("Goodbye!")

        break


    else:

        print("Invalid choice!")