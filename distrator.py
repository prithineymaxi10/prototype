import tkinter as tk
from tkinter import messagebox, Listbox, Scrollbar
import psutil
import pygetwindow as gw
import pyautogui
import time
import threading
import re
import csv
import matplotlib.pyplot as plt
from collections import Counter
from fpdf import FPDF
import os

plt.switch_backend('Agg')  # Fix Matplotlib GUI issue

blocked_apps = set()
app_block_count = Counter()
website_block_count = Counter()
search_block_count = Counter()
monitoring_thread = None

keywords = {
    'Game': ['fifa', 'fortnite', 'minecraft', 'valorant', 'pubg'],
    'Social Media': ['facebook', 'instagram', 'twitter', 'snapchat'],
    'Streaming': ['youtube', 'netflix', 'hulu', 'primevideo'],
    'Shopping': ['amazon', 'ebay', 'flipkart', '1mg'],
    'News': ['cnn', 'bbc', 'reuters', 'nyt'],
    'Music': ['spotify', 'apple music', 'youtube music'],
    'Messaging': ['whatsapp', 'telegram', 'signal'],
    'Video Calls': ['zoom', 'google meet', 'skype'],
    'ORG': ['google', 'microsoft', 'amazon', 'apple', 'tcs', 'infosys'],
    'PRODUCT': ['iphone', 'samsung', 'ps5', 'xbox', 'nike', 'adidas']
}

def get_running_processes():
    return [proc.info['name'].lower() for proc in psutil.process_iter(['name']) if proc.info['name']]

def kill_process(proc_name):
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            if proc.info['name'] and proc_name == proc.info['name'].lower():
                proc.terminate()
                print(f"⛔ Killed process: {proc_name}")
                blocked_apps.discard(proc_name)
                app_block_count[proc_name.replace('.exe', '')] += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass

def close_browser_tab():
    pyautogui.hotkey("ctrl", "w")
    print("❌ Tab closed!")

def show_alert(msg, title="Stay Focused!"):
    root.after(0, lambda: pyautogui.alert(msg, title))

def extract_search_query(title):
    match = re.search(r"(.*) - Google Search", title, re.IGNORECASE)
    return match.group(1).strip() if match else None

def save_report():
    with open("distraction_report.csv", "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["Category", "Name", "Block Count"])
        for app, count in app_block_count.items():
            writer.writerow(["App", app, count])
        for site, count in website_block_count.items():
            writer.writerow(["Website", site, count])
        for search, count in search_block_count.items():
            writer.writerow(["Search", search, count])

    generate_charts()
    generate_pdf_report()

def generate_charts():
    for category, data, filename in [
        ("Blocked Apps", app_block_count, "app_chart.png"),
        ("Blocked Websites", website_block_count, "website_chart.png"),
        ("Blocked Searches", search_block_count, "search_chart.png"),
    ]:
        if data:
            plt.figure(figsize=(8, 5))
            plt.bar(data.keys(), data.values(), color="red")
            plt.xlabel(category)
            plt.ylabel("Block Count")
            plt.title(category)
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()
            plt.savefig(filename)
            plt.close()

def generate_pdf_report():
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    pdf.set_font("Arial", "B", 16)
    pdf.cell(200, 10, "Distraction Monitoring Report", ln=True, align="C")

    pdf.ln(10)
    pdf.set_font("Arial", "", 12)
    pdf.cell(200, 10, f"Total Distractions Detected: {sum(app_block_count.values()) + sum(website_block_count.values()) + sum(search_block_count.values())}", ln=True)
    pdf.ln(5)
    
    for category, data in [("Blocked Applications", app_block_count),
                            ("Blocked Websites", website_block_count),
                            ("Blocked Searches", search_block_count)]:
        if data:
            pdf.set_font("Arial", "B", 12)
            pdf.cell(200, 10, category + ":", ln=True)
            pdf.set_font("Arial", "", 12)
            for name, count in data.items():
                pdf.cell(200, 10, f"{name}: {count} times", ln=True)
            pdf.ln(5)
    
    for filename in ["app_chart.png", "website_chart.png", "search_chart.png"]:
        try:
            pdf.ln(10)
            pdf.image(filename, x=30, w=150)
        except Exception:
            pass

    pdf.output("distraction_report.pdf")
    print("📄 PDF report generated!")

def auto_save():
    while monitoring_thread:
        time.sleep(20)
        save_report()


def normalize_app_name(app_name):
    """Removes extensions and converts to lowercase for consistency."""
    return os.path.splitext(app_name.lower())[0]

def monitor_distractions(name, apps, websites, entities, good_hobby):
    selected_keywords = set()
    for ent in entities:
        selected_keywords.update(keywords.get(ent, []))

    auto_save_thread = threading.Thread(target=auto_save, daemon=True)
    auto_save_thread.start()

    while monitoring_thread:
        running_processes = get_running_processes()

        # Monitor running apps
        for proc_name in running_processes:
            norm_proc_name = normalize_app_name(proc_name)

            if any(normalize_app_name(app) in norm_proc_name for app in apps):
                app_block_count[norm_proc_name] += 1
                show_alert(f"🚨 App detected: {proc_name}! Try {good_hobby} instead!")
                kill_process(proc_name)

        # Monitor browser windows
        for window in gw.getWindowsWithTitle(""):
            try:
                window_title = window.title.lower()

                if "google search" in window_title:
                    search_query = extract_search_query(window_title)
                    if search_query:
                        print(f"🔍 Detected search: {search_query}")

                        if any(site.lower() in search_query for site in websites):
                            search_block_count[search_query] += 1
                            show_alert(f"❌ Blocked search: {search_query}! Try {good_hobby} instead!")
                            close_browser_tab()
                            time.sleep(2)

                        for keyword in selected_keywords:
                            if keyword in search_query:
                                search_block_count[search_query] += 1
                                show_alert(f"❌ Blocked search: {search_query}! Try {good_hobby} instead!")
                                close_browser_tab()
                                time.sleep(2)

                for site in websites:
                    if site.lower() in window_title:
                        website_block_count[site] += 1
                        show_alert(f"❌ Blocked site: {site}! Try {good_hobby} instead!")
                        close_browser_tab()
                        time.sleep(2)

                for shopping_site in keywords.get('Shopping', []):
                    if shopping_site in window_title:
                        website_block_count[shopping_site] += 1
                        show_alert(f"🚫 Shopping site detected: {window_title}! Try {good_hobby} instead!")
                        close_browser_tab()
                        time.sleep(2)

            except Exception as e:
                print("⚠️ Error processing window:", e)
        time.sleep(3)

def start_monitoring():
    global monitoring_thread
    if monitoring_thread:
        messagebox.showwarning("Already Running", "Monitoring is already active!")
        return

    blocked_apps.clear()
    app_block_count.clear()

    name = name_entry.get().strip()
    apps = [a.strip().lower() for a in apps_entry.get().split(',') if a.strip()]
    websites = [w.strip().lower() for w in website_entry.get().split(',') if w.strip()]
    entities = [entity_listbox.get(i) for i in entity_listbox.curselection()]
    good_hobby = hobby_entry.get().strip()

    if not name or not apps or not websites or not entities or not good_hobby:
        messagebox.showwarning("Input Error", "Please fill all fields!")
        return

    messagebox.showinfo("Monitoring Started", "Real-time monitoring activated!")
    monitoring_thread = threading.Thread(target=monitor_distractions, args=(name, apps, websites, entities, good_hobby), daemon=True)
    monitoring_thread.start()

def stop_monitoring():
    global monitoring_thread
    if monitoring_thread:
        monitoring_thread = None
        save_report()
        messagebox.showinfo("Monitoring Stopped", "Distraction monitoring has been stopped.")
    else:
        messagebox.showwarning("Not Running", "Monitoring is not active!")

def reset_fields():
    name_entry.delete(0, tk.END)
    apps_entry.delete(0, tk.END)
    website_entry.delete(0, tk.END)
    entity_listbox.selection_clear(0, tk.END)
    hobby_entry.delete(0, tk.END)



# GUI Setup
root = tk.Tk()
root.title("Distractor Blocker")
root.geometry("450x600")

tk.Label(root, text="Your Name:").pack(pady=5)
name_entry = tk.Entry(root, width=40)
name_entry.pack()

tk.Label(root, text="Distracting Apps (comma-separated):").pack(pady=5)
apps_entry = tk.Entry(root, width=40)
apps_entry.pack()

tk.Label(root, text="Distracting Websites (comma-separated):").pack(pady=5)
website_entry = tk.Entry(root, width=40)
website_entry.pack()

tk.Label(root, text="Entities (Select for real-time detection):").pack(pady=5)
entity_frame = tk.Frame(root)
entity_frame.pack()

entity_scrollbar = Scrollbar(entity_frame)
entity_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

entity_listbox = Listbox(entity_frame, selectmode=tk.MULTIPLE, yscrollcommand=entity_scrollbar.set, height=8, width=30)
entity_listbox.pack(side=tk.LEFT)
entity_scrollbar.config(command=entity_listbox.yview)

for category in keywords.keys():
    entity_listbox.insert(tk.END, category)

tk.Label(root, text="Good Hobby (to replace distractions):").pack(pady=5)
hobby_entry = tk.Entry(root, width=40)
hobby_entry.pack()

tk.Button(root, text="Start Monitoring", command=start_monitoring).pack(pady=10)
tk.Button(root, text="Stop Monitoring", command=stop_monitoring).pack(pady=10)
tk.Button(root, text="Reset", command=reset_fields).pack(pady=10)

root.mainloop()





