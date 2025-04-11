import pyttsx3
import speech_recognition as sr
import wikipedia
import webbrowser
import os
import psutil
from datetime import datetime
import time
import pyautogui
import subprocess
import ctypes
import winshell
import cv2
import numpy as np

from PIL import Image
import pyperclip
import textwrap
import random
import string
import shutil
from fpdf import FPDF
import zipfile
import keyboard
import GPUtil
import speedtest
from googletrans import Translator
import json
import PyPDF2
import requests
from tkinter import Tk, filedialog
from PyPDF2 import PdfReader, PdfWriter
from pdf2image import convert_from_path
from docx import Document

import fitz  # PyMuPDF for text extraction
import pdf2image
from pdf2docx import Converter
from docx import Document
from tkinter import Tk, filedialog
import nltk
import logging
logging.getLogger("comtypes").setLevel(logging.WARNING)
wake_word_triggered = False


assistant_data_file = "assistant_name.json"
def take_command():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening...")
        recognizer.pause_threshold = 1
        audio = recognizer.listen(source)

    try:
        print("Recognizing...")
        query = recognizer.recognize_google(audio, language='en-in')
        print(f"User said: {query}")
    except Exception:
        print("Could not understand. Please say that again.")
        return None
    return query.lower()

def create_folder(folder_name, destination):
    try:
        path = os.path.join(destination, folder_name)
        os.makedirs(path)
        speak(f"Folder {folder_name} has been created successfully at {destination}.")
    except FileExistsError:
        speak("Folder already exists.")
    except Exception as e:
        speak(f"An error occurred: {e}")

def create_file(file_name, destination):
    try:
        path = os.path.join(destination, file_name)
        with open(path, 'w') as file:
            file.write("")  # Create an empty file
        speak(f"File {file_name} has been created successfully at {destination}.")
    except Exception as e:
        speak(f"An error occurred: {e}")

def set_alarm(alarm_time):
    speak(f"Alarm is set for {alarm_time}.")
    while True:
        current_time = datetime.now().strftime("%H:%M:%S")
        if current_time == alarm_time:
            speak("Wake up! It's time!")
            break
        time.sleep(1)

def calculator():
    speak("Please provide the calculation.")
    calculation = take_command()
    try:
        result = eval(calculation)
        speak(f"The result of {calculation} is {result}.")
    except Exception as e:
        speak("I couldn't perform the calculation. Please try again.")

def close_tabs():
    try:
        speak("Closing all open browser tabs.")
        pyautogui.hotkey('ctrl', 'w')
    except Exception as e:
        speak(f"An error occurred while closing tabs: {e}")

def toggle_dark_mode():
    try:
        subprocess.run('reg add HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize /v AppsUseLightTheme /t REG_DWORD /d 0 /f', shell=True)
        subprocess.run('reg add HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize /v SystemUsesLightTheme /t REG_DWORD /d 0 /f', shell=True)
        speak("Dark mode enabled.")
    except Exception as e:
        speak("Could not toggle dark mode.")


def set_mouse_sensitivity(value):
    try:
        ctypes.windll.user32.SystemParametersInfoW(113, 0, value, 0)
        speak(f"Mouse sensitivity set to {value}.")
    except Exception as e:
        speak("Could not adjust mouse sensitivity.")

def toggle_bluetooth(enable=True):
    try:
        command = "net start bthserv" if enable else "net stop bthserv"
        subprocess.run(command, shell=True)
        speak("Bluetooth enabled." if enable else "Bluetooth disabled.")
    except Exception as e:
        speak("Could not toggle Bluetooth.")

def toggle_wifi(enable=True):
    try:
        command = "netsh interface set interface Wi-Fi " + ("enabled" if enable else "disabled")
        os.system(command)
        speak("Wi-Fi turned on." if enable else "Wi-Fi turned off.")
    except Exception as e:
        speak("Could not toggle Wi-Fi.")

def lock_screen():
    ctypes.windll.user32.LockWorkStation()
    speak("Screen locked.")

def log_out():
    os.system("shutdown -l")
    speak("Logging out now.")

def set_wallpaper(image_path):
    ctypes.windll.user32.SystemParametersInfoW(20, 0, image_path, 3)
    speak("Wallpaper changed.")

def empty_recycle_bin():
    winshell.recycle_bin().empty(confirm=False, show_progress=False, sound=True)
    speak("Recycle bin emptied.")

def show_running_apps():
    apps = [proc.name() for proc in psutil.process_iter()]
    speak(f"Currently running applications are: {', '.join(apps)}")

def take_screenshot():
    screenshot = pyautogui.screenshot()
    screenshot.save("screenshot.png")
    speak("Screenshot taken and saved.")

def record_screen(duration=10, filename="screen_record.avi"):
    screen_size = pyautogui.size()
    fourcc = cv2.VideoWriter_fourcc(*"XVID")
    out = cv2.VideoWriter(filename, fourcc, 10.0, screen_size)

    for _ in range(duration * 10):
        frame = np.array(pyautogui.screenshot())
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        out.write(frame)

    out.release()
    speak("Screen recording saved.")

def resize_image(image_path, width, height):
    img = Image.open(image_path)
    img = img.resize((width, height))
    img.save("resized_" + image_path)
    speak("Image resized successfully.")

def battery_health():
    battery = psutil.sensors_battery()
    speak(f"Battery is at {battery.percent} percent. Plugged in: {battery.power_plugged}")

def find_large_files(directory, size_limit):
    large_files = [f for f in os.listdir(directory) if os.path.getsize(os.path.join(directory, f)) > size_limit]
    speak(f"Found {len(large_files)} large files.")

def read_clipboard():
    content = pyperclip.paste()
    speak(f"Clipboard contains: {content}")


def upload_file():
    """Open file dialog to select a file and upload it."""
    Tk().withdraw()  # Hide the main tkinter window
    file_path = filedialog.askopenfilename(title="Select a file to summarize")

    if not file_path:
        print("No file selected.")
        return None

    if os.path.exists(file_path):
        with open(file_path, "rb") as f:
            response = requests.post("http://127.0.0.1:5000/upload", files={"file": f})

        if response.status_code == 200:
            summary = response.json().get("summary", "No summary generated.")
            print(f"Summary: {summary}")
        else:
            print("Error uploading file:", response.json().get("error", "Unknown error"))
    else:
        print(f"Error: File '{file_path}' not found.")


def generate_password(length=12):
    password = ''.join(random.choices(string.ascii_letters + string.digits, k=length))
    speak(f"Generated password: {password}")

def listen_for_wake_word(wake_word="hello assistant"):
    while True:
        command = take_command()
        if command == wake_word:
            speak("I'm listening.")
            break

def measure_typing_speed():
    speak("Type this sentence as fast as you can: The quick brown fox jumps over the lazy dog.")
    start_time = time.time()
    input("Type here: ")
    elapsed_time = time.time() - start_time
    speak(f"You took {elapsed_time:.2f} seconds.")

def toggle_airplane_mode(enable=True):
    command = "netsh interface set interface name='Wi-Fi' admin=" + ("disabled" if enable else "enabled")
    subprocess.run(command, shell=True)
    speak("Airplane mode enabled." if enable else "Airplane mode disabled.")

def move_file(source, destination):
    shutil.move(source, destination)
    speak("File moved successfully.")


def batch_rename(folder_path, prefix):
    for count, filename in enumerate(os.listdir(folder_path)):
        new_name = f"{prefix}_{count}{os.path.splitext(filename)[1]}"
        os.rename(os.path.join(folder_path, filename), os.path.join(folder_path, new_name))
    speak("Files renamed successfully.")

def sort_files_by_type(folder):
    for file in os.listdir(folder):
        ext = os.path.splitext(file)[1][1:]
        if not os.path.exists(os.path.join(folder, ext)):
            os.makedirs(os.path.join(folder, ext))
        shutil.move(os.path.join(folder, file), os.path.join(folder, ext, file))
    speak("Files sorted by type.")

def text_to_pdf(text, filename="output.pdf"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, text)
    pdf.output(filename)
    speak("Text converted to PDF.")

def create_zip(folder, output_filename="compressed.zip"):
    shutil.make_archive(output_filename.replace(".zip", ""), 'zip', folder)
    speak("Files archived successfully.")

def extract_zip(zip_path, extract_to):
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_to)
    speak("Files extracted.")


def count_files(folder_path):
    count = len(os.listdir(folder_path))
    speak(f"There are {count} files in the folder.")

def play_music(folder_path):
    files = [f for f in os.listdir(folder_path) if f.endswith(".mp3")]
    if files:
        os.system(f'start {random.choice(files)}')
        speak("Playing music.")

def folder_structure(folder):
    structure = "\n".join([f for f in os.walk(folder)])
    with open("folder_report.txt", "w") as file:
        file.write(structure)
    speak("Folder structure report generated.")

def control_music():
    keyboard.press_and_release("play/pause media")
    speak("Music paused or resumed.")

def change_theme(light=True):
    theme = 1 if light else 0
    subprocess.run(f"reg add HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize /v SystemUsesLightTheme /t REG_DWORD /d {theme} /f", shell=True)
    speak("System theme changed.")


def mute_notifications():
    os.system("nircmd.exe mutesysvolume 1")
    speak("System notifications muted.")


def get_gpu_usage():
    gpus = GPUtil.getGPUs()
    speak(f"GPU usage is at {gpus[0].load * 100:.2f} percent.")


def internet_speed():
    st = speedtest.Speedtest()
    download = st.download() / 1e6
    upload = st.upload() / 1e6
    speak(f"Download speed: {download:.2f} Mbps, Upload speed: {upload:.2f} Mbps.")

def disk_space():
    total, used, free = shutil.disk_usage("/")
    speak(f"Total: {total//1e9} GB, Used: {used//1e9} GB, Free: {free//1e9} GB.")

def list_usb_devices():
    devices = [disk.device for disk in psutil.disk_partitions() if 'removable' in disk.opts]
    speak(f"Connected USB devices: {', '.join(devices)}")

def toggle_task_manager(enable=True):
    command = f'reg add HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\System /v DisableTaskMgr /t REG_DWORD /d {"0" if enable else "1"} /f'
    subprocess.run(command, shell=True)
    speak("Task Manager enabled." if enable else "Task Manager disabled.")

def restart_app(app_name):
    os.system(f"taskkill /IM {app_name} /F")
    time.sleep(2)
    os.system(f"start {app_name}")
    speak(f"{app_name} restarted.")

def kill_app(app_name):
    os.system(f"taskkill /IM {app_name} /F")
    speak(f"{app_name} closed.")

def toggle_camera(enable=True):
    command = f'reg add HKLM\\Software\\Microsoft\\Windows\\CurrentVersion\\CapabilityAccessManager\\ConsentStore\\webcam /v Value /t REG_SZ /d {"Allow" if enable else "Deny"} /f'
    subprocess.run(command, shell=True)
    speak("Camera enabled." if enable else "Camera disabled.")


def translate_text(text, dest_lang="es"):
    translator = Translator()
    translated = translator.translate(text, dest=dest_lang)
    speak(f"Translated text: {translated.text}")

def backup_folder(source, destination):
    shutil.copytree(source, destination)
    speak("Folder backup completed.")

def text_to_speech_file(text, filename="output.mp3"):
    engine = pyttsx3.init()
    engine.save_to_file(text, filename)
    engine.runAndWait()
    speak("Text converted to speech file.")

def dictation_mode():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        speak("Dictation mode activated. Start speaking.")
        try:
            while True:
                audio = recognizer.listen(source)
                text = recognizer.recognize_google(audio)
                with open("dictation.txt", "a") as file:
                    file.write(text + "\n")
                speak(f"You said: {text}")
        except KeyboardInterrupt:
            speak("Dictation mode ended.")

def read_pdf(file_path, start_page):
    engine = pyttsx3.init()
    with open(file_path, "rb") as file:
        reader = PyPDF2.PdfReader(file)
        for page_num in range(start_page, len(reader.pages)):
            text = reader.pages[page_num].extract_text()
            engine.say(text)
            engine.runAndWait()

reminders_file = "reminders.json"
engine = pyttsx3.init()

def speak(text):
    print(f"[SPEAKING] {text}")
    engine.say(text)
    engine.runAndWait()

def load_reminders():
    try:
        with open(reminders_file, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return []

def save_reminders(reminders):
    with open(reminders_file, "w") as file:
        json.dump(reminders, file)

def add_reminder(task, remind_time):
    reminders = load_reminders()
    reminders.append({"task": task, "time": remind_time})
    save_reminders(reminders)
    speak(f"Reminder set for {task} at {remind_time}")

def check_reminders():
    while True:
        reminders = load_reminders()
        current_time = datetime.now().strftime("%H:%M")
        for reminder in reminders:
            if reminder["time"] == current_time:
                speak(f"Reminder: {reminder['task']}")
                reminders.remove(reminder)
                save_reminders(reminders)
        time.sleep(60)


def find_recent_files(folder, days=1):
    current_time = time.time()
    files = [f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f)) and (current_time - os.path.getmtime(os.path.join(folder, f))) < days * 86400]
    speak(f"Recent files modified in last {days} days: {', '.join(files)}.")


def list_running_apps():
    apps = [p.name() for p in psutil.process_iter()]
    speak(f"Currently running applications: {', '.join(apps[:10])}.")



def control_volume(action):
    try:
        if action == "increase":
            for _ in range(5):
                pyautogui.press("volumeup")
        elif action == "decrease":
            for _ in range(5):
                pyautogui.press("volumedown")
        elif action == "mute":
            pyautogui.press("volumemute")
        speak(f"Volume {action}d successfully.")
    except Exception as e:
        speak(f"An error occurred: {e}")

def get_battery_status():
    battery = psutil.sensors_battery()
    percent = battery.percent
    speak(f"Your system is at {percent} percent battery.")
    if not battery.power_plugged:
        speak("Please connect the charger to avoid losing power.")

def weather_forecast():
    webbrowser.open("https://www.weather.com")
    speak("I have opened the weather forecast page for you.")

def news_headlines():
    webbrowser.open("https://news.google.com")
    speak("I have opened Google News for the latest headlines.")

def shutdown_system():
    speak("Are you sure you want to shut down the system? Please say yes or no.")
    confirmation = take_command()
    if "yes" in confirmation:
        speak("Shutting down the system.")
        os.system("shutdown /s /t 1")
    else:
        speak("Shutdown canceled.")

def restart_system():
    speak("Are you sure you want to restart the system? Please say yes or no.")
    confirmation = take_command()
    if "yes" in confirmation:
        speak("Restarting the system.")
        os.system("shutdown /r /t 1")
    else:
        speak("Restart canceled.")

def open_application(application_name):
    try:
        speak(f"Opening {application_name}.")
        subprocess.run(application_name, shell=True)
    except Exception as e:
        speak(f"Could not open {application_name}. {e}")

def system_status():
    cpu_usage = psutil.cpu_percent()
    memory_info = psutil.virtual_memory()
    speak(f"CPU usage is at {cpu_usage} percent.")
    speak(f"Memory usage is at {memory_info.percent} percent.")


def get_assistant_name():
    if os.path.exists(assistant_data_file):
        with open(assistant_data_file, 'r') as f:
            data = json.load(f)
            return data.get("assistant_name", "Assistant")
    else:
        speak("Please name your assistant.")
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            speak("Listening for the name.")
            audio = recognizer.listen(source)
            try:
                name = recognizer.recognize_google(audio).strip().capitalize()
                with open(assistant_data_file, 'w') as f:
                    json.dump({"assistant_name": name}, f)
                speak(f"My name is now {name}.")
                return name
            except:
                speak("Sorry, I couldn't understand. Defaulting to Assistant.")
                return "Assistant"

def execute_command(query):
    if "wikipedia" in query:
        try:
            speak("Searching Wikipedia...")
            query = query.replace("wikipedia", "")
            results = wikipedia.summary(query, sentences=2)
            speak("According to Wikipedia")
            print(results)
            speak(results)
        except wikipedia.exceptions.DisambiguationError:
            speak("Multiple results found. Please be more specific.")
        except wikipedia.exceptions.PageError:
            speak("No results found. Please try a different topic.")
    elif "open youtube" in query:
        webbrowser.open("https://www.youtube.com")
        speak("YouTube is open. What would you like to search?")
        search_query = take_command()
        if search_query:
            webbrowser.open(f"https://www.youtube.com/results?search_query={search_query}")
            speak(f"Searching YouTube for {search_query}")
    elif "open spotify" in query:
        webbrowser.open("https://open.spotify.com")
        speak("Spotify is open. What would you like to search?")
        search_query = take_command()
        if search_query:
            webbrowser.open(f"https://open.spotify.com/search/{search_query}")
            speak(f"Searching Spotify for {search_query}")
    elif "open google" in query:
        webbrowser.open("https://www.google.com")
        speak("Google is open. What would you like to search?")
        search_query = take_command()
        if search_query:
            webbrowser.open(f"https://www.google.com/search?q={search_query}")
            speak(f"Searching Google for {search_query}")
    elif "create folder" in query:
        speak("Please specify the folder name.")
        folder_name = take_command()
        speak("Please specify the destination path, like Desktop or C drive.")
        destination = take_command()

        if folder_name and destination:
            if "desktop" in destination:
                destination_path = os.path.join(os.path.expanduser("~"), "Desktop")
            elif "c drive" in destination:
                destination_path = "C:\\"
            elif "d drive" in destination:
                destination_path = "D:\\"
            else:
                destination_path = os.getcwd()
            create_folder(folder_name, destination_path)
    elif "set alarm" in query:
        speak("Please tell me the time to set the alarm in HH:MM:SS format.")
        alarm_time = take_command()
        set_alarm(alarm_time)
    elif "calculate" in query:
        calculator()
    elif "close tabs" in query:
        close_tabs()
    elif "volume up" in query:
        control_volume("increase")
    elif "volume down" in query:
        control_volume("decrease")
    elif "mute volume" in query:
        control_volume("mute")
    elif "battery status" in query:
        get_battery_status()
    elif "weather" in query:
        weather_forecast()
    elif "news" in query:
        news_headlines()
    elif "shutdown" in query:
        shutdown_system()
    elif "restart" in query:
        restart_system()
    elif "status" in query:
        system_status()
    elif "quit" in query or "exit" in query:
        speak("Goodbye!")
        exit()
    elif "enable dark mode" in command:
        toggle_dark_mode()
    elif "take a screenshot" in command:
        take_screenshot()
    elif "log out" in command:
        log_out()
    elif "check internet speed" in command:
        internet_speed()
    elif "lock my screen" in command:
        lock_screen()
    elif "empty recycle bin" in command:
        empty_recycle_bin()
    elif "translate" in command:
        text = command.replace("translate ", "")
        translate_text(text, "es")
    elif "battery status" in command:
        battery_health()
    elif "enable dark mode" in command:
        toggle_dark_mode()
    elif "take a screenshot" in command:
        take_screenshot()
    elif "log out" in command:
        log_out()
    elif "check internet speed" in command:
        internet_speed()
    elif "lock my screen" in command:
        lock_screen()
    elif "empty recycle bin" in command:
        empty_recycle_bin()
    elif "set mouse sensitivity" in command:
        value = int(command.split()[-1])
        set_mouse_sensitivity(value)
    
    elif "enable bluetooth" in command:
        toggle_bluetooth(True)

    elif "disable bluetooth" in command:
        toggle_bluetooth(False)

    elif "enable wifi" in command:
        toggle_wifi(True)

    elif "disable wifi" in command:
        toggle_wifi(False)

    elif "set wallpaper" in command:
        image_path = command.replace("set wallpaper to ", "").strip()
        set_wallpaper(image_path)

    elif "show running apps" in command:
        show_running_apps()

    elif "record screen" in command and command.split()[-1].isdigit():
        duration = int(command.split()[-1])
        record_screen(duration)

    elif "record screen" in command:
        duration = input("Enter duration (in seconds) for screen recording: ") or "10"
        record_screen(int(duration) if duration.isdigit() else 10)

    elif "resize image" in command:
        parts = command.split()
        image_path, width, height = parts[2], int(parts[3]), int(parts[4])
        resize_image(image_path, width, height)

    elif "find large files" in command:
        directory = command.replace("find large files in ", "").strip()
        find_large_files(directory, size_limit=100000000)  # Example: 100MB limit

    elif "read clipboard" in command:
        read_clipboard()

    elif "summarise file" in command:
        upload_file()

    elif "generate password" in command and command.split()[-1].isdigit():
        length = int(command.split()[-1])
        generate_password(length)
    elif "generate password" in command:
        generate_password(12)  

    elif "measure typing speed" in command:
        measure_typing_speed()

    elif "enable airplane mode" in command:
        toggle_airplane_mode(True)

    elif "disable airplane mode" in command:
        toggle_airplane_mode(False)

    elif "move file" in command:
        parts = command.replace("move file ", "").split(" to ")
        move_file(parts[0].strip(), parts[1].strip())

    elif "batch rename" in command:
        parts = command.replace("batch rename ", "").split(" with prefix ")
        batch_rename(parts[0].strip(), parts[1].strip())

    elif "sort files" in command:
        folder = command.replace("sort files in ", "").strip()
        sort_files_by_type(folder)

    elif "convert text to pdf" in command:
        text = command.replace("convert text to pdf ", "").strip()
        text_to_pdf(text)

    elif "create zip" in command:
        folder = command.replace("create zip ", "").strip()
        create_zip(folder)

    elif "extract zip" in command:
        parts = command.replace("extract zip ", "").split(" to ")
        extract_zip(parts[0].strip(), parts[1].strip())

    elif "count files" in command:
        folder_path = command.replace("count files in ", "").strip()
        count_files(folder_path)

    elif "play music" in command:
        folder_path = command.replace("play music in ", "").strip()
        play_music(folder_path)

    elif "show folder structure" in command:
        folder = command.replace("show folder structure of ", "").strip()
        folder_structure(folder)

    elif "pause or resume music" in command:
        control_music()

    elif "enable light theme" in command:
        change_theme(True)

    elif "enable dark theme" in command:
        change_theme(False)

    elif "mute notifications" in command:
        mute_notifications()

    elif "check GPU usage" in command:
        get_gpu_usage()

    elif "check disk space" in command:
        disk_space()

    elif "list USB devices" in command:
        list_usb_devices()

    elif "enable task manager" in command:
        toggle_task_manager(True)

    elif "disable task manager" in command:
        toggle_task_manager(False)

    elif "restart app" in command:
        app_name = command.replace("restart app ", "").strip()
        restart_app(app_name)

    elif "close app" in command:
        app_name = command.replace("close app ", "").strip()
        kill_app(app_name)

    elif "enable camera" in command:
        toggle_camera(True)

    elif "disable camera" in command:
        toggle_camera(False)

    elif "backup folder" in command:
        parts = command.replace("backup folder ", "").split(" to ")
        backup_folder(parts[0].strip(), parts[1].strip())

    elif "convert text to speech file" in command:
        text = command.replace("convert text to speech file ", "").strip()
        text_to_speech_file(text)

    elif "start dictation mode" in command:
        dictation_mode()

    elif "read pdf" in command:
        parts = command.replace("read pdf ", "").split(" from page ")
        read_pdf(parts[0].strip(), int(parts[1]))

    elif "find recent files" in command:
        folder = command.replace("find recent files in ", "").strip()
        find_recent_files(folder)

    elif "list running applications" in command:
        list_running_apps()
   
    else:
        speak("Sorry, I can't handle that command yet.")

if __name__ == "__main__":
    assistant_name = get_assistant_name().lower()
    intro_message = f"{assistant_name.capitalize()} is ready. Say '{assistant_name}' or just speak your command."
    print(f"[SPEAKING] {intro_message}")
    speak(intro_message)

    while True:
        command = take_command()
        if not command:
            continue

        command = command.lower()

        if assistant_name in command:
            command = command.replace(assistant_name, "").strip()
            if command:
                print(f"[COMMAND] {command}")
                execute_command(command)
            else:
                print("[SPEAKING] Yes?")
                speak("Yes?")
        else:
            print(f"[COMMAND] {command}")
            execute_command(command)
