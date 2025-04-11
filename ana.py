from flask import Flask, render_template, request, jsonify, send_file
import pandas as pd
import PyPDF2
import os
import hashlib

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def extract_headings(csv_file):
    df = pd.read_csv(csv_file)
    return list(df.columns)

def detect_anomalies(csv_file):
    df = pd.read_csv(csv_file)
    if 'cleaned' in df.columns and df['cleaned'].iloc[0] == 1:
        return {}, {}
    
    anomalies = {}
    recommendations = {}
    for column in df.select_dtypes(include=['number']).columns:
        mean, std = df[column].mean(), df[column].std()
        outliers = df[(df[column] < mean - 3*std) | (df[column] > mean + 3*std)]
        anomalies[column] = outliers[column].tolist()
        recommendations[column] = mean
    return anomalies, recommendations

def hash_text(text):
    return hashlib.md5(text.encode('utf-8')).hexdigest()

def check_duplicate_pages(pdf_file_path):
    try:
        reader = PyPDF2.PdfReader(pdf_file_path)
        hashes = []
        duplicates = []
        for i, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            page_hash = hash_text(text)
            if hashes and page_hash == hashes[-1]:
                duplicates.append(i)
            hashes.append(page_hash)
        return duplicates
    except Exception as e:
        return ['Error reading PDF: ' + str(e)]

@app.route('/')
def index():
    return render_template('index5.html')

@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['file']
    if not file:
        return jsonify({'error': 'No file uploaded'}), 400

    file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(file_path)

    if file.filename.endswith('.csv'):
        headings = extract_headings(file_path)
        anomalies, recommendations = detect_anomalies(file_path)
        if not any(anomalies.values()):
            return jsonify({
                'file_path': file_path,
                'message': 'No anomalies found',
                'headings': headings
            })
        return jsonify({
            'headings': headings,
            'anomalies': anomalies,
            'recommendations': recommendations,
            'file_path': file_path
        })

    elif file.filename.endswith('.pdf'):
        duplicates = check_duplicate_pages(file_path)
        return jsonify({'duplicate_pages': duplicates})

    return jsonify({'error': 'Unsupported file type'}), 400

@app.route('/fix_anomalies', methods=['POST'])
def fix_anomalies():
    data = request.json
    file_path = data.get('file_path')
    user_inputs = data.get('user_inputs', {})

    df = pd.read_csv(file_path)
    for column, value in user_inputs.items():
        if column in df.columns:
            mean = df[column].mean()
            std = df[column].std()
            df[column] = df[column].apply(lambda x: mean if (x < mean - 3*std or x > mean + 3*std) else x)

    df['cleaned'] = 1
    cleaned_file_path = file_path.replace('.csv', '_cleaned.csv')
    df.to_csv(cleaned_file_path, index=False)
    return jsonify({'message': 'Anomalies fixed successfully', 'download_url': f'/download/{os.path.basename(cleaned_file_path)}'})

@app.route('/download/<filename>')
def download(filename):
    return send_file(os.path.join(app.config['UPLOAD_FOLDER'], filename), as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
