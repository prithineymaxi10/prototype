import os
from flask import Flask, request, render_template, send_file
from werkzeug.utils import secure_filename
from pdf2docx import Converter
from docx import Document
import pdfplumber
import fitz  # PyMuPDF for PDF to image
from PIL import Image
import pandas as pd
import PyPDF2

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
PROCESSED_FOLDER = "processed"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["PROCESSED_FOLDER"] = PROCESSED_FOLDER
ALLOWED_EXTENSIONS = {"pdf", "docx", "txt", "csv", "html", "jpg", "png"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/", methods=["GET", "POST"])
def upload_file():
    if request.method == "POST":
        files = request.files.getlist("file")  # Allow multiple files
        action = request.form["action"]

        if not files:
            return "No file selected"

        file_paths = []
        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
                file.save(file_path)
                file_paths.append(file_path)

        if action == "pdf_to_word":
            file_path = file_paths[0]
            output_file = file_path.replace(".pdf", ".docx")
            cv = Converter(file_path)
            cv.convert(output_file)
            cv.close()
            return send_file(output_file, as_attachment=True)

        elif action == "word_to_pdf":
            file_path = file_paths[0]
            output_file = file_path.replace(".docx", ".pdf")
            doc = Document(file_path)
            doc.save(output_file)
            return send_file(output_file, as_attachment=True)

        elif action == "pdf_to_txt":
            file_path = file_paths[0]
            with pdfplumber.open(file_path) as pdf:
                text = "\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])
            output_file = file_path.replace(".pdf", ".txt")
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(text)
            return send_file(output_file, as_attachment=True)

        elif action == "pdf_to_html":
            file_path = file_paths[0]
            with pdfplumber.open(file_path) as pdf:
                text = "\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])
            output_file = file_path.replace(".pdf", ".html")
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(f"<html><body><pre>{text}</pre></body></html>")
            return send_file(output_file, as_attachment=True)

        elif action == "pdf_to_csv":
            file_path = file_paths[0]
            with pdfplumber.open(file_path) as pdf:
                text = [page.extract_text() for page in pdf.pages if page.extract_text()]
            output_file = file_path.replace(".pdf", ".csv")
            df = pd.DataFrame({"Text": text})
            df.to_csv(output_file, index=False)
            return send_file(output_file, as_attachment=True)

        elif action == "image_to_pdf":
            images = [Image.open(f) for f in file_paths]
            output_file = os.path.join(app.config["PROCESSED_FOLDER"], "converted_images.pdf")
            images[0].save(output_file, save_all=True, append_images=images[1:])
            return send_file(output_file, as_attachment=True)

        elif action == "merge_pdfs":
            merger = PyPDF2.PdfMerger()
            for pdf in file_paths:
                merger.append(pdf)
            output_file = os.path.join(app.config["PROCESSED_FOLDER"], "merged.pdf")
            merger.write(output_file)
            merger.close()
            return send_file(output_file, as_attachment=True)

        elif action == "split_pdf":
            file_path = file_paths[0]
            with open(file_path, "rb") as file:
                reader = PyPDF2.PdfReader(file)
                for i in range(len(reader.pages)):
                    writer = PyPDF2.PdfWriter()
                    writer.add_page(reader.pages[i])
                    output_file = os.path.join(app.config["PROCESSED_FOLDER"], f"page_{i+1}.pdf")
                    with open(output_file, "wb") as out_pdf:
                        writer.write(out_pdf)
            return "PDF split successfully. Check processed folder."

    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)


