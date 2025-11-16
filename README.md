🚀 *SmartToDo – Personal AI To-Do Assistant* 🚀

A simple multi-agent system that turns natural language into organized tasks, daily plans, and reflections.

🌟 *Overview*

SmartToDo is a lightweight personal productivity agent built using Gemini and a multi-agent architecture.
Users can type tasks in natural language, and the agent system will:

✔ Extract tasks

✔ Save & organize them

✔ Create a daily plan

✔ Track completion

✔ Generate an end-of-day reflection

This project was created for the Google x Kaggle AI Agents Capstone (2025) under the Concierge Agents Track.

🌟 *Features*

1. Multi-Agent System
Task Intake Agent – extracts tasks from messy input

Planner Agent – creates daily structured plan

Reflection Agent – analyzes completed vs pending tasks

2. Tools
Custom TaskStore tool (add/list/update tasks)

JSON persistence (tasks.json)

3. Memory
Long-term memory saved as memory.json

Stores daily reflections and performance

4. Observability
Simple print-based logging:

[IntakeAgent] Created 3 tasks
[PlannerAgent] Plan generated
[ReflectionAgent] Reflection saved

5. Gemini Usage
All 3 agents use Gemini 2.5 Flash (fast + cost-efficient).

🌟 *Project Structure*
SmartToDo/
│ app.py
│ tasks.json
│ memory.json
│ requirements.txt
└ README.md

🌟 *Installation*
1. Install dependencies
pip install -U google-genai

2. Set your Gemini API key

PowerShell

$env:GEMINI_API_KEY="YOUR_KEY_HERE"


To persist permanently:

setx GEMINI_API_KEY "YOUR_KEY_HERE"

🌟 *Running the Agent*
python app.py


You will see a simple menu:

1) Add tasks from text
2) Show all tasks
3) Mark task as done
4) Generate today's plan
5) Generate reflection
6) Exit

🌟 *How It Works*
> Agent 1 – Task Intake Agent

Turns natural language into clean JSON tasks using Gemini.

> Agent 2 – Planner Agent

Sorts tasks into:

Must do today

Good to do

Can do later

> Agent 3 – Reflection Agent

Analyzes completion and stores a memory entry.

🌟 *Limitations*

Only supports single user (session-based)

No web UI (CLI only)

Memory simple (JSON-based)

🌟 *Future Improvements*

Add reminders

Add calendar API

Add Gradio/Streamlit UI

Add categories & tags

Deploy using Agent Engine on Cloud Run

*License*


MIT License.

