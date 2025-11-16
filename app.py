"""
SmartToDo – Simple Personal To-Do Multi-Agent

Agents:
  1) Task Intake Agent      – turns user text into structured tasks
  2) Planner Agent          – makes a daily plan from tasks
  3) Reflection Agent       – short end-of-day reflection

Tools:
  - TaskStore (in-memory + JSON persistence)
Memory:
  - session_id (single user demo)
  - memory.json keeps daily reflections (long-term memory)

Run:
  python app.py
"""

import json
import os
from datetime import date
from typing import List, Dict, Any

from google import genai
from google.genai import types as genai_types


# =========  LLM CLIENT SETUP  =========

def get_client() -> genai.Client:
    """
    Create a Gemini client. It automatically uses GEMINI_API_KEY env var.
    """
    # If you want to force a specific API version:
    http_options = genai_types.HttpOptions(api_version="v1")
    client = genai.Client(http_options=http_options)
    return client


CLIENT = get_client()
MODEL_NAME = "gemini-2.5-flash"  # fast + cheap, good for this use case


def call_llm(prompt: str) -> str:
    """
    Helper to call Gemini once with text prompt and get plain text back.
    """
    response = CLIENT.models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
    )
    return response.text


# =========  SIMPLE TASK STORE (TOOL)  =========

class TaskStore:
    """
    Very simple "database" for tasks.
    Stores in memory and also saves to disk in tasks.json for persistence.
    """

    def __init__(self, path: str = "tasks.json"):
        self.path = path
        self._tasks: List[Dict[str, Any]] = []
        self._next_id = 1
        self.load()

    def load(self) -> None:
        if os.path.exists(self.path):
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._tasks = data.get("tasks", [])
                    self._next_id = data.get("next_id", 1)
            except Exception:
                # If file corrupted, start fresh
                self._tasks = []
                self._next_id = 1

    def save(self) -> None:
        data = {
            "tasks": self._tasks,
            "next_id": self._next_id,
        }
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    # ----- tool methods -----

    def add_task(self, title: str, due: str, priority: str, category: str) -> Dict[str, Any]:
        task = {
            "id": self._next_id,
            "title": title,
            "due": due,
            "priority": priority,
            "category": category,
            "status": "pending",
            "created_date": str(date.today()),
        }
        self._tasks.append(task)
        self._next_id += 1
        self.save()
        return task

    def list_tasks(self, status: str | None = None) -> List[Dict[str, Any]]:
        if status is None:
            return list(self._tasks)
        return [t for t in self._tasks if t.get("status") == status]

    def update_task_status(self, task_id: int, status: str) -> Dict[str, Any] | None:
        for t in self._tasks:
            if t["id"] == task_id:
                t["status"] = status
                self.save()
                return t
        return None


TASK_STORE = TaskStore()


# =========  AGENT 1: TASK INTAKE AGENT  =========

def task_intake_agent(user_message: str) -> List[Dict[str, Any]]:
    """
    Takes messy user text and turns it into structured tasks.

    Returns list of created tasks (with IDs).
    """
    print("\n[IntakeAgent] Received:", user_message)

    prompt = f"""
You are a task extraction agent for a personal to-do app.

USER MESSAGE:
\"\"\"{user_message}\"\"\"

Extract the tasks and return ONLY valid JSON in this format:
[
  {{
    "title": "...",
    "due": "today | tomorrow | this week | specific date or 'unspecified'",
    "priority": "high | medium | low",
    "category": "study | work | personal | health | other"
  }},
  ...
]

Rules:
- If no due date is mentioned, use "unspecified".
- If the message is not about tasks, return an empty list [].
- Do NOT include any extra text, only JSON.
"""
    raw = call_llm(prompt)

    # Try to parse JSON
    try:
        # Some models wrap JSON in markdown code fence, so strip it
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.strip("`")
            # remove potential "json" language tag
            cleaned = cleaned.replace("json", "", 1).strip()
        data = json.loads(cleaned)
        assert isinstance(data, list)
    except Exception as e:
        print("[IntakeAgent] ERROR parsing JSON from model:", e)
        print("[IntakeAgent] Raw response was:")
        print(raw)
        return []

    created = []
    for t in data:
        title = t.get("title") or "Untitled task"
        due = t.get("due") or "unspecified"
        priority = t.get("priority") or "medium"
        category = t.get("category") or "other"
        created_task = TASK_STORE.add_task(title, due, priority, category)
        created.append(created_task)

    print(f"[IntakeAgent] Created {len(created)} tasks")
    return created


# =========  AGENT 2: PLANNER AGENT  =========

def planner_agent() -> str:
    """
    Reads all tasks and creates a short daily plan.
    """
    all_tasks = TASK_STORE.list_tasks()
    today_str = str(date.today())

    prompt = f"""
You are a friendly planning assistant.

TODAY'S DATE: {today_str}

These are the user's tasks (JSON):
{json.dumps(all_tasks, indent=2)}

Create a clear plan for today with sections:

1) Must do today
2) Good to do
3) Can do later

Guidelines:
- Consider priority (high first), then due date.
- Keep the whole plan under 200 words.
- Use simple English.
"""
    plan = call_llm(prompt)
    print("[PlannerAgent] Plan generated.")
    return plan


# =========  LONG-TERM MEMORY (REFLECTION LOG)  =========

MEMORY_FILE = "memory.json"


def append_memory(entry: Dict[str, Any]) -> None:
    memory: List[Dict[str, Any]] = []
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                memory = json.load(f)
        except Exception:
            memory = []
    memory.append(entry)
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(memory, f, indent=2)


# =========  AGENT 3: REFLECTION AGENT  =========

def reflection_agent() -> str:
    """
    Generates a short reflection based on completed vs pending tasks.
    Saves reflection into memory.json as "long term memory".
    """
    today_str = str(date.today())
    completed = [t for t in TASK_STORE.list_tasks() if t["status"] == "done"]
    pending = [t for t in TASK_STORE.list_tasks() if t["status"] == "pending"]

    prompt = f"""
You are a gentle reflection coach.

Today's date: {today_str}

Completed tasks:
{json.dumps(completed, indent=2)}

Pending tasks:
{json.dumps(pending, indent=2)}

Write a short reflection (3–5 sentences) for the user:
- Say what they did well.
- Mention one thing to improve tomorrow.
- Give one small suggestion for tomorrow's focus.
Use very simple English.
"""
    reflection = call_llm(prompt)
    print("[ReflectionAgent] Reflection generated.")

    # Save to long-term memory
    memory_entry = {
        "date": today_str,
        "completed_count": len(completed),
        "pending_count": len(pending),
        "reflection": reflection,
    }
    append_memory(memory_entry)

    return reflection


# =========  SIMPLE CLI APP (for demo)  =========

def print_tasks(tasks: List[Dict[str, Any]]) -> None:
    if not tasks:
        print("No tasks.")
        return
    for t in tasks:
        print(
            f"[{t['id']}] ({t['status']}) "
            f"[prio: {t['priority']}, due: {t['due']}, cat: {t['category']}] "
            f"- {t['title']}"
        )


def main_menu():
    while True:
        print("\n===== SmartToDo – Personal To-Do Agent =====")
        print("1) Add tasks from text (Task Intake Agent)")
        print("2) Show all tasks")
        print("3) Mark task as done")
        print("4) Generate today's plan (Planner Agent)")
        print("5) Generate reflection (Reflection Agent)")
        print("6) Exit")
        choice = input("Choose an option: ").strip()

        if choice == "1":
            user_message = input("\nType your tasks in natural language:\n> ")
            created = task_intake_agent(user_message)
            print("\nCreated tasks:")
            print_tasks(created)

        elif choice == "2":
            print("\nAll tasks:")
            print_tasks(TASK_STORE.list_tasks())

        elif choice == "3":
            try:
                tid = int(input("Enter task ID to mark as done: "))
            except ValueError:
                print("Invalid ID.")
                continue
            updated = TASK_STORE.update_task_status(tid, "done")
            if updated:
                print("Updated task:")
                print_tasks([updated])
            else:
                print("Task not found.")

        elif choice == "4":
            plan = planner_agent()
            print("\n===== PLAN FOR TODAY =====")
            print(plan)

        elif choice == "5":
            reflection = reflection_agent()
            print("\n===== DAILY REFLECTION =====")
            print(reflection)

        elif choice == "6":
            print("Bye! 👋")
            break

        else:
            print("Invalid choice, try again.")


if __name__ == "__main__":
    main_menu()
