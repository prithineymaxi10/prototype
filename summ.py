from flask import Flask, render_template, request, send_file
import fitz  # PyMuPDF
from deep_translator import GoogleTranslator
from docx import Document
import os
import time

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "output"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def extract_text_from_pdf(pdf_path):
    text = ""
    doc = fitz.open(pdf_path)
    for page in doc:
        text += page.get_text("text") + "\n"
    return text.strip()

def split_text(text, max_chars=5000):
    chunks = []
    while len(text) > max_chars:
        split_index = text.rfind(".", 0, max_chars)
        if split_index == -1:
            split_index = max_chars
        chunks.append(text[:split_index + 1])
        text = text[split_index + 1:].strip()
    chunks.append(text)
    return chunks

def translate_text(text, lang):
    translator = GoogleTranslator(source="auto", target=lang)
    chunks = split_text(text)
    translated_chunks = []

    for chunk in chunks:
        try:
            translated_chunks.append(translator.translate(chunk))
            time.sleep(1)  # Prevent rate limit issues
        except Exception as e:
            print(f"Error translating chunk: {e}")
            translated_chunks.append("[Translation Failed]")
    
    return " ".join(translated_chunks)

def save_as_txt(text, filename):
    path = os.path.join(OUTPUT_FOLDER, filename + ".txt")
    with open(path, "w", encoding="utf-8") as file:
        file.write(text)
    return path

def save_as_docx(text, filename):
    path = os.path.join(OUTPUT_FOLDER, filename + ".docx")
    doc = Document()
    doc.add_paragraph(text)
    doc.save(path)
    return path

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        file = request.files["file"]
        lang = request.form["language"]
        output_format = request.form["format"]

        if file and file.filename.endswith(".pdf"):
            file_path = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(file_path)

            extracted_text = extract_text_from_pdf(file_path)
            translated_text = translate_text(extracted_text, lang)

            filename = os.path.splitext(file.filename)[0] + "_translated"
            if output_format == "txt":
                output_path = save_as_txt(translated_text, filename)
            elif output_format == "docx":
                output_path = save_as_docx(translated_text, filename)

            return send_file(output_path, as_attachment=True)

    return render_template("index2.html")

if __name__ == "__main__":
    app.run(debug=True)
