import time
import psutil
import win32gui
import win32process
import sqlite3
import pandas as pd
import pygetwindow as gw
import re
import matplotlib.pyplot as plt
from plyer import notification
from plyer import notification
from fpdf import FPDF
import os
from datetime import datetime

# Initialize database
def init_db():
    conn = sqlite3.connect("screen_time.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            app_name TEXT,
            specific_activity TEXT,
            duration INTEGER,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

# Export data to Excel
def export_to_excel():
    conn = sqlite3.connect("screen_time.db")
    df = pd.read_sql_query("SELECT * FROM usage", conn)
    df.to_excel("screen_time_report.xlsx", index=False)
    conn.close()
    print("[INFO] Data exported to screen_time_report.xlsx")

def generate_visualization():
    conn = sqlite3.connect("screen_time.db")
    df = pd.read_sql_query(
        "SELECT app_name, specific_activity, SUM(duration) as total_duration FROM usage GROUP BY app_name, specific_activity", 
        conn
    )
    conn.close()

    if df.empty:
        print("[INFO] No data available for visualization.")
        return

    df["app_activity"] = df["app_name"] + " - " + df["specific_activity"]
    total_duration_sum = df["total_duration"].sum()
    df["percentage"] = (df["total_duration"] / total_duration_sum * 100).round(1)

    folder_name = datetime.now().strftime('%Y-%m-%d')
    os.makedirs(folder_name, exist_ok=True)
    
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", style='B', size=20)
    pdf.cell(200, 10, txt="Screen Time Usage Report", ln=True, align='C')
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Date: {datetime.now().strftime('%Y-%m-%d')}", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", style='B', size=14)
    pdf.cell(200, 10, txt="Executive Summary", ln=True)
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, "This report provides a comprehensive analysis of screen time usage across various applications and activities. It highlights the most frequently used apps and offers insights for better time management.")
    pdf.ln(10)
    
    # Adding Table of Contents
    pdf.set_font("Arial", style='B', size=14)
    pdf.cell(200, 10, txt="Table of Contents", ln=True)
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="1. Overview", ln=True)
    pdf.cell(200, 10, txt="2. Visual Analysis (Charts & Graphs)", ln=True)
    pdf.cell(200, 10, txt="3. Detailed Data Breakdown", ln=True)
    pdf.cell(200, 10, txt="4. Insights & Recommendations", ln=True)
    pdf.cell(200, 10, txt="5. Top Used Applications", ln=True)
    pdf.cell(200, 10, txt="6. Suggested Productivity Improvements", ln=True)
    pdf.add_page()
    
    # Insights and Recommendations
    pdf.set_font("Arial", style='B', size=14)
    pdf.cell(200, 10, txt="Insights & Recommendations", ln=True)
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, "- Identify apps consuming excessive screen time and set time limits.\n- Balance work and leisure activities for improved productivity.\n- Consider reducing non-essential app usage to enhance focus.\n- Optimize screen time by using focus-enhancing tools and scheduling breaks.")
    pdf.add_page()
    
    # Most Used Applications Section
    pdf.set_font("Arial", style='B', size=14)
    pdf.cell(200, 10, txt="Top Used Applications", ln=True)
    pdf.set_font("Arial", size=12)
    top_apps = df.groupby("app_name")["total_duration"].sum().sort_values(ascending=False).head(5)
    for app, duration in top_apps.items():
        pdf.cell(200, 10, txt=f"{app}: {round(duration/3600, 2)} hours", ln=True)
    pdf.add_page()

    # Bar Graph
    plt.figure(figsize=(12, 6))
    plt.bar(df["app_activity"], df["total_duration"], color='skyblue')
    plt.xlabel("Application & Activity")
    plt.ylabel("Usage Time (seconds)")
    plt.title("Screen Time Usage per App & Activity")
    plt.xticks(rotation=75, ha="right")
    plt.subplots_adjust(bottom=0.4)
    bar_chart_path = os.path.join(folder_name, "bar_chart.png")
    plt.savefig(bar_chart_path, bbox_inches='tight')
    plt.close()

    # Pie Chart
    plt.figure(figsize=(8, 8))
    plt.pie(df["total_duration"], labels=df["app_activity"], autopct='%1.1f%%', startangle=140)
    plt.axis('equal')
    plt.title("Screen Time Distribution")
    pie_chart_path = os.path.join(folder_name, "pie_chart.png")
    plt.savefig(pie_chart_path, bbox_inches='tight')
    plt.close()

    # Pie-Ray Chart (3D Visualization)
    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection='3d')
    theta = [i / len(df) * 2 * 3.14159 for i in range(len(df))]
    radii = df["total_duration"] / total_duration_sum * 10
    heights = df["total_duration"]
    ax.bar(theta, heights, zs=0, zdir='y', alpha=0.8)
    ax.set_xlabel('Apps')
    ax.set_ylabel('Angle')
    ax.set_zlabel('Usage Time (seconds)')
    ax.set_title("Screen Time Distribution (3D Pie-Ray Chart)")
    pie_ray_chart_path = os.path.join(folder_name, "pie_ray_chart.png")
    plt.savefig(pie_ray_chart_path, bbox_inches='tight')
    plt.close()

    # Add visuals to PDF
    pdf.image(bar_chart_path, x=10, y=30, w=180)
    pdf.add_page()
    pdf.image(pie_chart_path, x=10, y=30, w=180)
    pdf.add_page()
    pdf.image(pie_ray_chart_path, x=10, y=30, w=180)

    pdf.add_page()
    pdf.set_font("Arial", size=10)
    for index, row in df.iterrows():
        pdf.cell(200, 10, txt=f"{row['app_activity']}: {row['percentage']}%".encode('latin-1', 'ignore').decode('latin-1'), ln=True)

    # Generate specific graphs for major .exe files
    major_apps = df["app_name"].value_counts().head(5).index
    for app in major_apps:
        app_df = df[df["app_name"] == app]

        # Bar Graph for Specific App
        plt.figure(figsize=(12, 6))
        plt.bar(app_df["specific_activity"], app_df["total_duration"], color='lightcoral')
        plt.xlabel("Activity")
        plt.ylabel("Usage Time (seconds)")
        plt.title(f"Screen Time Usage for {app}")
        plt.xticks(rotation=75, ha="right")
        plt.subplots_adjust(bottom=0.4)
        app_bar_chart_path = os.path.join(folder_name, f"{app}_bar_chart.png")
        plt.savefig(app_bar_chart_path, bbox_inches='tight')
        plt.close()

        # Pie Chart for Specific App
        plt.figure(figsize=(10, 10))
        plt.pie(app_df["total_duration"], labels=app_df["specific_activity"], autopct='%1.1f%%', startangle=140)
        plt.axis('equal')
        plt.title(f"Screen Time Distribution for {app}")
        app_pie_chart_path = os.path.join(folder_name, f"{app}_pie_chart.png")
        plt.savefig(app_pie_chart_path, bbox_inches='tight')
        plt.close()

        # Pie-Ray Chart for Specific App
        fig = plt.figure(figsize=(10, 8))
        ax = fig.add_subplot(111, projection='3d')
        theta = [i / len(app_df) * 2 * 3.14159 for i in range(len(app_df))]
        radii = app_df["total_duration"] / app_df["total_duration"].sum() * 10
        heights = app_df["total_duration"]
        ax.bar(theta, heights, zs=0, zdir='y', alpha=0.8)
        ax.set_xlabel('Activities')
        ax.set_ylabel('Angle')
        ax.set_zlabel('Usage Time (seconds)')
        ax.set_title(f"Screen Time Distribution for {app} (3D Pie-Ray Chart)")
        app_pie_ray_chart_path = os.path.join(folder_name, f"{app}_pie_ray_chart.png")
        plt.savefig(app_pie_ray_chart_path, bbox_inches='tight')
        plt.close()

        # Add to PDF
        pdf.add_page()
       
        pdf.image(app_bar_chart_path, x=10, y=30, w=180)
        pdf.add_page()
        pdf.image(app_pie_chart_path, x=10, y=30, w=180)
        pdf.add_page()
        pdf.image(app_pie_ray_chart_path, x=10, y=30, w=180)

    pdf_path = os.path.join(folder_name, f"screen_time_report_{folder_name}.pdf")
    pdf.output(pdf_path)
    print(f"[INFO] PDF report generated: {pdf_path}")

# Get active window
def get_active_window():
    hwnd = win32gui.GetForegroundWindow()
    _, pid = win32process.GetWindowThreadProcessId(hwnd)
    
    for proc in psutil.process_iter(['pid', 'name']):
        if proc.info['pid'] == pid:
            window_title = gw.getActiveWindow().title if gw.getActiveWindow() else "Unknown"
            app_name = proc.info['name']
            
            # Extract specific activity from browsers
            specific_activity = window_title  
            if app_name in ["chrome.exe", "msedge.exe", "firefox.exe"]:
                specific_activity = extract_activity(window_title)
            
            return app_name, specific_activity
    
    return "Unknown", ""

# Extract activity details from browser window title
def extract_activity(window_title):
    youtube_match = re.search(r'^(.*) - YouTube$', window_title)
    youtube_search_match = re.search(r'Search results for (.*?) - YouTube$', window_title)
    google_search_match = re.search(r'(.*?) - Google Search$', window_title)
    generic_search_match = re.search(r'(.*?) - (Google Chrome|Mozilla Firefox|Microsoft Edge)$', window_title)
    
    if youtube_search_match:
        return "Website - YouTube: " + youtube_search_match.group(1)
    elif youtube_match:
        return "Website - YouTube: " + youtube_match.group(1)
    elif google_search_match:
        return "Website - Search: " + google_search_match.group(1)
    elif generic_search_match:
        return "Website - " + generic_search_match.group(1)
    
    return "Unknown"

# Store usage
def log_usage(app_name, specific_activity, duration):
    conn = sqlite3.connect("screen_time.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO usage (app_name, specific_activity, duration) VALUES (?, ?, ?)", 
                   (app_name, specific_activity, duration))
    conn.commit()
    conn.close()

# Notify user
def notify_user(title, message):
    notification.notify(title=title, message=message, timeout=10)
    print(f"[INFO] Notification sent: {title}")

# Monitor usage
def monitor_usage():
    usage_log = {}
    start_time = time.time()
    total_time = 0
    app_usage = {}  # Track per-app usage
    activity_usage = {}  # Track specific activity usage
    app_limit = 1800  # 30 minutes per app
    total_limit = 10800  # 3 hours total

    try:
        while True:
            active_app, specific_activity = get_active_window()
            app_key = active_app  # Track total app usage
            activity_key = (active_app, specific_activity)  # Track specific activity usage
            
            if app_key not in app_usage:
                app_usage[app_key] = 0
            app_usage[app_key] += 1
            
            if activity_key not in activity_usage:
                activity_usage[activity_key] = 0
            activity_usage[activity_key] += 1
            
            total_time += 1

            # Notify if any app crosses 30 minutes
            if app_usage[app_key] >= app_limit:
                notify_user("App Usage Limit Reached", f"You have spent more than 30 minutes on {active_app}.")
                app_usage[app_key] = 0  # Reset for next notification
            
            # Notify if total screen time exceeds 3 hours
            if total_time >= total_limit:
                notify_user("Screen Time Alert", "You have been on your device for more than 3 hours. Consider taking a break!")
                total_time = 0  # Reset counter
            
            # Store data every 5 minutes
            if time.time() - start_time >= 30:
                for (app, activity), duration in activity_usage.items():
                    log_usage(app, activity, duration)
                export_to_excel()
                generate_visualization()
                start_time = time.time()
                activity_usage = {}
            
            time.sleep(1)  
    
    except KeyboardInterrupt:
        print("\n[INFO] Script stopped manually.")

if __name__ == "__main__":
    init_db()
    print("[INFO] Screen Time Monitor Started...")
    monitor_usage()


