# 📊 Teams Training Analytics

A tool I built at Future Connect Training & Recruitment to turn the trainers' Microsoft Teams check-in chat into daily activity reports. Trainers post short updates like "started", "finished", "break", "login" or "logout" in a shared Teams chat. The scraper reads that chat with Playwright, turns the messages into sessions, breaks, and tasks with durations per trainer, saves them as CSV files, and a Streamlit dashboard charts the results.

![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white)
![Playwright](https://img.shields.io/badge/Playwright-2EAD33?style=flat-square&logo=playwright&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=flat-square&logo=streamlit&logoColor=white)
![Plotly](https://img.shields.io/badge/Plotly-3F4F75?style=flat-square&logo=plotly&logoColor=white)
![pandas](https://img.shields.io/badge/pandas-150458?style=flat-square&logo=pandas&logoColor=white)
![Microsoft Teams](https://img.shields.io/badge/Microsoft_Teams-6264A7?style=flat-square&logo=microsoftteams&logoColor=white)

<!-- Add screenshots: ![Dashboard](screenshots/dashboard.png) -->

## ✨ Features
- 🔐 One-time Teams login in a real browser window, saved as a Playwright session so later runs skip the login
- 📜 Scrolls the selected chat back to the beginning to capture the full message history
- 🧮 Keyword-based parsing of each message into:
  - **Sessions** (start and finish times, duration)
  - **Breaks**, including prayer breaks
  - **Tasks**, with login and logout tracked as task start and end
- 💾 Saves `teams_sessions_*.csv`, `teams_breaks_*.csv`, and `teams_tasks_*.csv` with timestamps
- 📈 Streamlit dashboard that loads the latest CSVs and shows KPIs and charts: break duration, task count, total sessions, and task duration by trainer, plus a summary table

## 🚀 Run locally

```bash
git clone https://github.com/ziauldin/teams-training-analytics.git
cd teams-training-analytics
pip install -r requirements.txt
python -m playwright install chromium

python scraper.py              # first run: log in to Teams, then open the chat to scrape
streamlit run dashboard.py     # open http://localhost:8501
```

On Windows, `setup.bat` installs everything, runs the scraper, and opens the dashboard.

The login session (`teams_storage_state.json`) and the scraped CSVs stay on your machine. They are listed in `.gitignore` because they contain session cookies and people's names.

## 🛠️ Tech stack
Python · Playwright · pandas · Streamlit · Plotly · Matplotlib · Seaborn · Tkinter
