# 📈 stockAgent

**stockAgent** is an AI-powered stock analysis backend application written in Python.  
It implements a **multi-agent workflow** that validates user input, performs stock market research, evaluates analysis quality, and produces a final, well-formatted HTML report.

The project showcases:
- agent-based architecture
- prompt engineering
- CI/CD automation
- Dockerized deployment

---

## 🧠 What Does the Agent Do?

The agent analyzes **1 to 5 publicly traded stocks** provided by the user and produces a **professional investment-style analysis** for each stock, including:

- Pros
- Cons
- Summary
- Sources used

If the input is invalid (too many stocks or unrelated to stocks), the agent stops early using a guardrail mechanism.

---

## 🔁 Agent Workflow (Graph)

![Architecture diagram](images/architecture.png)

## ⚙️ Installation (Local)

bash
git clone https://github.com/kamilwilnicki/stockAgent.git
cd stockAgent
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app/main.py
