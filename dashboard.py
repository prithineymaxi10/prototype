from flask import Flask, render_template, send_from_directory
import os
import subprocess
import psutil  # To check if process is already running
from datetime import datetime

app = Flask(__name__)

# Base directory for reports
BASE_DIR = os.path.join(os.path.expanduser("~"), "Downloads", "Screentime")

# Ensure the directory exists
if not os.path.exists(BASE_DIR):
    os.makedirs(BASE_DIR)

# Function to check if a process is already running
def is_process_running(script_name):
    for process in psutil.process_iter(['pid', 'name', 'cmdline']):
        cmdline = process.info['cmdline']
        if cmdline and script_name in " ".join(cmdline):
            return True  # Process found
    return False

# Run scripts only if not already running
if not is_process_running("ScreenTime.py"):
    subprocess.Popen(["python", os.path.join(BASE_DIR, "ScreenTime.py")])

if not is_process_running("Distrator.py"):
    subprocess.Popen(["python", os.path.join(BASE_DIR, "Distrator.py")])

@app.route("/")
def home():
    today = datetime.today().strftime("%Y-%m-%d")
    screen_time_path = os.path.join(BASE_DIR, today)

    screen_time_images = []
    if os.path.exists(screen_time_path):
        screen_time_images = [f for f in os.listdir(screen_time_path) if f.endswith((".png", ".jpg", ".jpeg"))]

    distrator_images = [f for f in os.listdir(BASE_DIR) if f.endswith((".png", ".jpg", ".jpeg"))]

    return render_template(
        "dashboard.html",
        screen_time_images=screen_time_images,
        distrator_images=distrator_images,
        screen_time_path=today
    )

@app.route("/images/<path:folder>/<filename>")
def serve_image(folder, filename):
    return send_from_directory(os.path.join(BASE_DIR, folder), filename)

@app.route("/distractor_images/<filename>")
def serve_distractor_image(filename):
    return send_from_directory(BASE_DIR, filename)

if __name__ == "__main__":
    app.run(debug=True)




