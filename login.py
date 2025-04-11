from flask import Flask, render_template, request, redirect, url_for, jsonify, session
import os, cv2, json, hashlib, numpy as np, pyttsx3, threading
import speech_recognition as sr
from datetime import datetime

app = Flask(__name__)
app.secret_key = "supersecurekey"

DATA_DIR = "face_data"
USER_DB = "users.json"
SESSION_DB = "session.json"
os.makedirs(DATA_DIR, exist_ok=True)

# Initialize TTS
engine = pyttsx3.init()

def speak(text):
    def runner():
        try:
            engine.say(text)
            engine.runAndWait()
        except RuntimeError:
            pass
    threading.Thread(target=runner).start()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def load_json(path):
    return json.load(open(path)) if os.path.exists(path) else {}

def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=4)

def capture_voice():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        speak("Please say your unlock phrase clearly.")
        try:
            audio = recognizer.listen(source, timeout=5)
            return recognizer.recognize_google(audio).lower()
        except:
            return None

# ------------------ DNN-based Face Detection ------------------

face_net = cv2.dnn.readNetFromCaffe(
    r"C:\Users\HP\Downloads\Screentime\deploy.prototxt", 
    r"C:\Users\HP\Downloads\Screentime\res10_300x300_ssd_iter_140000.caffemodel"
)

def detect_face_dnn(frame):
    h, w = frame.shape[:2]
    blob = cv2.dnn.blobFromImage(frame, 1.0, (300, 300), [104, 117, 123], False, False)
    face_net.setInput(blob)
    detections = face_net.forward()

    for i in range(detections.shape[2]):
        confidence = detections[0, 0, i, 2]
        if confidence > 0.7:
            box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
            return frame[int(box[1]):int(box[3]), int(box[0]):int(box[2])]
    return None

def capture_and_save_faces(username):
    cap = cv2.VideoCapture(0)
    os.makedirs(os.path.join(DATA_DIR, username), exist_ok=True)
    count = 0

    speak("Capturing face data. Please look at the camera.")
    while count < 20:
        ret, frame = cap.read()
        if not ret:
            continue

        face = detect_face_dnn(frame)
        if face is not None:
            face = cv2.resize(face, (160, 160))
            cv2.imwrite(os.path.join(DATA_DIR, username, f"{count}.jpg"), face)
            count += 1
            speak(f"Captured image {count}")
    cap.release()

def compare_faces(input_face, username):
    user_path = os.path.join(DATA_DIR, username)
    if not os.path.exists(user_path):
        return False

    input_face = cv2.resize(input_face, (160, 160))
    input_hist = cv2.calcHist([input_face], [0], None, [256], [0, 256])
    input_hist = cv2.normalize(input_hist, input_hist).flatten()

    match_count = 0
    for file in os.listdir(user_path):
        img = cv2.imread(os.path.join(user_path, file))
        if img is None:
            continue
        img_hist = cv2.calcHist([img], [0], None, [256], [0, 256])
        img_hist = cv2.normalize(img_hist, img_hist).flatten()
        correlation = cv2.compareHist(input_hist, img_hist, cv2.HISTCMP_CORREL)
        if correlation > 0.9:
            match_count += 1

    return match_count >= 5

# ------------------ Routes ------------------

@app.route("/", methods=["GET", "POST"])
def login():
    users = load_json(USER_DB)
    session_data = load_json(SESSION_DB)

    if session_data.get("logged_in"):
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if username in users and users[username]["password"] == hash_password(password):
            cap = cv2.VideoCapture(0)
            ret, frame = cap.read()
            cap.release()

            face = detect_face_dnn(frame)
            if face is None or not compare_faces(face, username):
                return "Access Denied: Face not recognized."

            voice = capture_voice()
            if voice != users[username]["voice_phrase"]:
                return "Access Denied: Voice not recognized."

            speak(f"Welcome {username}")
            session["username"] = username
            save_json(SESSION_DB, {"logged_in": True, "username": username})
            return redirect(url_for("dashboard"))
        else:
            return "Invalid credentials."
    return render_template("login.html")

@app.route("/biometric_login", methods=["POST"])
def biometric_login():
    users = load_json(USER_DB)

    cap = cv2.VideoCapture(0)
    ret, frame = cap.read()
    cap.release()

    face = detect_face_dnn(frame)
    if face is None:
        return jsonify({"status": "fail", "message": "Face not detected."})

    for username, data in users.items():
        if compare_faces(face, username):
            voice = capture_voice()
            if voice == data["voice_phrase"]:
                session["username"] = username
                save_json(SESSION_DB, {"logged_in": True, "username": username})
                speak(f"Welcome {username}")
                return jsonify({"status": "success", "redirect": url_for("dashboard")})

    return jsonify({"status": "fail", "message": "Authentication failed."})

@app.route("/create_account", methods=["GET", "POST"])
def create_account():
    users = load_json(USER_DB)

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if username in users:
            return "Username already exists."

        capture_and_save_faces(username)
        voice_phrase = capture_voice()
        if not voice_phrase:
            return "Voice capture failed."

        users[username] = {
            "password": hash_password(password),
            "voice_phrase": voice_phrase
        }
        save_json(USER_DB, users)
        speak("Account created successfully.")
        return redirect(url_for("login"))

    return render_template("create_account.html")

@app.route("/dashboard")
def dashboard():
    session_data = load_json(SESSION_DB)
    if not session_data.get("logged_in"):
        return redirect(url_for("login"))
    return render_template("dashboard2.html", username=session_data.get("username"))

@app.route("/logout")
def logout():
    session.clear()
    save_json(SESSION_DB, {"logged_in": False})
    speak("You have been logged out.")
    return redirect(url_for("login"))

# ------------------ Run ------------------

if __name__ == "__main__":
    app.run(debug=True)

