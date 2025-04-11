import os
import re
import PyPDF2
import pytesseract
import docx
from flask import Flask, request, render_template, jsonify
from werkzeug.utils import secure_filename
from PIL import Image

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"pdf", "txt", "png", "jpg", "jpeg", "docx"}
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_from_pdf(pdf_path):
    text = ""
    try:
        with open(pdf_path, "rb") as file:
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                text += page.extract_text() + "\n"
    except Exception as e:
        return f"Error extracting text from PDF: {str(e)}"
    return text.strip()

def extract_text_from_image(image_path):
    try:
        image = Image.open(image_path)
        return pytesseract.image_to_string(image).strip()
    except Exception as e:
        return f"Error extracting text from Image: {str(e)}"

def extract_text_from_txt(txt_path):
    try:
        with open(txt_path, "r", encoding="utf-8") as file:
            return file.read().strip()
    except Exception as e:
        return f"Error extracting text from TXT: {str(e)}"

def extract_text_from_docx(docx_path):
    try:
        doc = docx.Document(docx_path)
        return "\n".join([para.text for para in doc.paragraphs]).strip()
    except Exception as e:
        return f"Error extracting text from DOCX: {str(e)}"

def find_best_answer(text, question):
    sentences = re.split(r'(?<=[.!?])\s+', text)
    question_words = set(question.lower().split()) - {"what", "is", "the", "of", "how", "who", "when", "why", "where"}

    best_match = ""
    max_overlap = 0

    for sentence in sentences:
        sentence_words = set(sentence.lower().split())
        overlap = len(question_words & sentence_words)

        if overlap > max_overlap:
            max_overlap = overlap
            best_match = sentence

    return best_match if best_match else "No relevant answer found."

@app.route("/", methods=["GET", "POST"])
def upload_file():
    if request.method == "POST":
        if "file" not in request.files:
            return jsonify({"error": "No file uploaded"}), 400

        file = request.files["file"]
        if file.filename == "":
            return jsonify({"error": "No file selected"}), 400

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(file_path)

            file_ext = filename.rsplit(".", 1)[1].lower()
            extracted_text = ""

            if file_ext == "pdf":
                extracted_text = extract_text_from_pdf(file_path)
            elif file_ext in {"png", "jpg", "jpeg"}:
                extracted_text = extract_text_from_image(file_path)
            elif file_ext == "txt":
                extracted_text = extract_text_from_txt(file_path)
            elif file_ext == "docx":
                extracted_text = extract_text_from_docx(file_path)

            os.remove(file_path)  # Delete the file after processing

            if not extracted_text:
                return jsonify({"error": "No text extracted from the file"}), 400

            question = request.form.get("question", "").strip()
            answer = find_best_answer(extracted_text, question) if question else "No question provided."

            return jsonify({"extracted_text": extracted_text, "answer": answer})

    return render_template("index1.html")

if __name__ == "__main__":
    app.run(debug=True)
