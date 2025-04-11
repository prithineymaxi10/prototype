from flask import Flask, render_template, request, redirect, url_for, jsonify
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from plyer import notification
import pyttsx3
import json
import os
import speech_recognition as sr

app = Flask(__name__)
DATA_FILE = "health_logs.json"
CURRENT_TASK_FILE = "current_task.json"
engine = pyttsx3.init()

default_tasks = [
    {"title": "Wake Up", "time": "07:00"},
    {"title": "Drink Water", "time": "07:15"},
    {"title": "Morning Stretch", "time": "07:30"},
    {"title": "Breakfast", "time": "08:00"},
    {"title": "Eye Exercise", "time": "09:30"},
    {"title": "Drink Water", "time": "10:00"},
    {"title": "Posture Check", "time": "11:00"},
    {"title": "Mental Check-in", "time": "11:30"},
    {"title": "Lunch", "time": "13:00"},
    {"title": "Drink Water", "time": "13:15"},
    {"title": "Drink Water", "time": "13:31"},
    {"title": "Drink Water", "time": "14:17"},
    {"title": "Stretch", "time": "15:00"},
    {"title": "Breathing Exercise", "time": "15:30"},
    {"title": "Posture Check", "time": "16:00"},
    {"title": "Drink Water", "time": "17:30"},
    {"title": "Dinner", "time": "19:00"},
    {"title": "Mood Check", "time": "20:00"},
    {"title": "Night Meditation", "time": "21:30"},
    {"title": "Plan Tomorrow", "time": "22:00"},
    {"title": "Bedtime", "time": "22:30"},
]
tasks = default_tasks.copy()

def ensure_data_file():
    if not os.path.exists(DATA_FILE):
        data = {
            "hydration": [], "meals": [], "eye_care": [], "mental_check": [],
            "stretching": [], "posture": [], "meditation": [], "missed": [], "completed": []
        }
        with open(DATA_FILE, "w") as f:
            json.dump(data, f, indent=4)
    if not os.path.exists(CURRENT_TASK_FILE):
        with open(CURRENT_TASK_FILE, "w") as f:
            json.dump({"current_task": None}, f)

def update_wellness_category(data, today, category):
    for entry in data[category]:
        if entry["date"] == today:
            entry["count"] += 1
            return
    data[category].append({"date": today, "count": 1})

def log_task_completion(task_title):
    today = datetime.now().strftime('%Y-%m-%d')
    ensure_data_file()
    with open(DATA_FILE, "r") as f:
        data = json.load(f)

    categories = {
        "Drink Water": "hydration", "Breakfast": "meals", "Lunch": "meals", "Dinner": "meals",
        "Eye Exercise": "eye_care", "Mental Check-in": "mental_check", "Stretch": "stretching",
        "Morning Stretch": "stretching", "Posture Check": "posture", "Night Meditation": "meditation"
    }

    for key_phrase, category in categories.items():
        if key_phrase in task_title:
            update_wellness_category(data, today, category)

    for entry in data["completed"]:
        if entry["date"] == today:
            entry["count"] += 1
            break
    else:
        data["completed"].append({"date": today, "count": 1})

    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

def track_missed_tasks():
    today = datetime.now().strftime('%Y-%m-%d')
    ensure_data_file()
    with open(DATA_FILE, "r") as f:
        data = json.load(f)

    if not any(entry["date"] == today for entry in data["missed"]):
        completed = next((entry["count"] for entry in data["completed"] if entry["date"] == today), 0)
        missed = len(tasks) - completed
        data["missed"].append({"date": today, "count": missed})

        with open(DATA_FILE, "w") as f:
            json.dump(data, f, indent=4)

def show_alert(task):
    ensure_data_file()
    engine.say(f"Time to {task['title']}")  # Updated voice message
    engine.runAndWait()
    notification.notify(title="Health Reminder", message=task["title"], timeout=5)
    with open(CURRENT_TASK_FILE, "w") as f:
        json.dump({"current_task": task["title"]}, f)

scheduler = BackgroundScheduler()
scheduler.start()

for task in tasks:
    hour, minute = map(int, task['time'].split(":"))
    scheduler.add_job(show_alert, 'cron', hour=hour, minute=minute, args=[task])

scheduler.add_job(track_missed_tasks, 'cron', hour=23, minute=59)

@app.route("/")
def dashboard():
    return render_template("dashboard3.html", tasks=tasks)

@app.route("/add", methods=["GET", "POST"])
def add_task():
    if request.method == "POST":
        title = request.form["title"]
        time = request.form["time"]
        tasks.append({"title": title, "time": time})
        return redirect(url_for("dashboard"))
    return render_template("add_task.html")

@app.route("/analytics")
def analytics():
    ensure_data_file()
    with open(DATA_FILE) as f:
        logs = json.load(f)
    return render_template("analytics.html", logs=logs)

@app.route("/mark_done", methods=["POST"])
def mark_done():
    title = request.json.get("title")
    if title:
        log_task_completion(title)
        return jsonify({"status": "success", "message": f"{title} marked as done."})
    return jsonify({"status": "error", "message": "No title received."}), 400

@app.route("/get_current_task")
def get_current_task():
    ensure_data_file()
    with open(CURRENT_TASK_FILE) as f:
        data = json.load(f)
    return jsonify(data)

@app.route("/voice_detect", methods=["POST"])
def voice_detect():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening for task confirmation...")
        audio = recognizer.listen(source, timeout=5, phrase_time_limit=4)
    try:
        transcript = recognizer.recognize_google(audio).lower()
        keywords_map = {
            "drink": "Drink Water", "done": None,
            "breakfast": "Breakfast", "lunch": "Lunch", "dinner": "Dinner",
            "stretch": "Stretch", "meditate": "Night Meditation",
            "eye": "Eye Exercise", "posture": "Posture Check", "mental": "Mental Check-in"
        }
        for key, task in keywords_map.items():
            if key in transcript:
                if task:
                    log_task_completion(task)
                return jsonify({"status": "success", "task": task, "transcript": transcript})
        return jsonify({"status": "no_match", "transcript": transcript})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route("/api/chart-data")
def chart_data():
    ensure_data_file()
    with open(DATA_FILE) as f:
        data = json.load(f)

    today = datetime.now()
    categories = ["hydration", "meals", "eye_care", "mental_check", "stretching", "posture", "meditation", "missed", "completed"]
    chart_data = {cat: [] for cat in categories}

    for i in range(6, -1, -1):
        date = (today - timedelta(days=i)).strftime('%Y-%m-%d')
        short_date = date[-5:]
        for cat in categories:
            count = next((entry["count"] for entry in data.get(cat, []) if entry["date"] == date), 0)
            chart_data[cat].append({"date": short_date, "count": count})

    return jsonify(chart_data)

@app.route("/api/live-data")
def live_data():
    today = datetime.now().strftime('%Y-%m-%d')
    ensure_data_file()

    with open(DATA_FILE) as f:
        data = json.load(f)

    total_tasks = len(tasks)
    completed = next((entry["count"] for entry in data["completed"] if entry["date"] == today), 0)
    missed = next((entry["count"] for entry in data["missed"] if entry["date"] == today), total_tasks - completed)

    hydration = next((entry["count"] for entry in data["hydration"] if entry["date"] == today), 0)
    meals = next((entry["count"] for entry in data["meals"] if entry["date"] == today), 0)
    mental = next((entry["count"] for entry in data["mental_check"] if entry["date"] == today), 0)
    stretch = next((entry["count"] for entry in data["stretching"] if entry["date"] == today), 0)

    percent_complete = round((completed / total_tasks) * 100, 2) if total_tasks else 0
    hydration_score = round((hydration / 4) * 100, 2)
    meal_score = round((meals / 3) * 100, 2)
    mental_score = round((mental / 1) * 100, 2)
    stretch_score = round((stretch / 2) * 100, 2)

    wellness_score = round(
        (0.25 * hydration_score) + (0.25 * meal_score) +
        (0.15 * mental_score) + (0.15 * stretch_score) +
        (0.20 * percent_complete), 2)

    productivity = "Excellent" if wellness_score >= 85 else \
                   "Good" if wellness_score >= 70 else \
                   "Average" if wellness_score >= 50 else "Needs Improvement"

    return jsonify({
        "completed": completed,
        "missed": missed,
        "hydration": hydration,
        "meals": meals,
        "mental_check": mental,
        "stretching": stretch,
        "completion_rate": percent_complete,
        "wellness_score": wellness_score,
        "productivity_rating": productivity
    })

if __name__ == "__main__":
    ensure_data_file()
    if not scheduler.running:
        scheduler.start()
    app.run(debug=True, use_reloader=False)

