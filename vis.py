import os
import pandas as pd
import pdfplumber
import matplotlib
matplotlib.use('Agg')  # Fix GUI warning
import matplotlib.pyplot as plt
import seaborn as sns
from flask import Flask, render_template, request, send_from_directory
from werkzeug.utils import secure_filename

app = Flask(__name__)
UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def extract_table_from_pdf(pdf_path):
    tables = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            table = page.extract_table()
            if table:
                df = pd.DataFrame(table[1:], columns=table[0])
                for col in df.columns[1:]:
                    df[col] = pd.to_numeric(df[col], errors='coerce')  # Convert to numeric
                tables.append(df)
    return tables[0] if tables else None

def generate_visualization(df, chart_type):
    chart_path = os.path.join(UPLOAD_FOLDER, 'chart.png')
    plt.figure(figsize=(12, 8))  # Increased size for better visibility
    
    if chart_type == 'bar':
        df.iloc[:, :2].plot(kind='bar', x=df.columns[0], y=df.columns[1], figsize=(12, 8), legend=True)
    elif chart_type == 'line':
        df.iloc[:, :2].plot(kind='line', x=df.columns[0], y=df.columns[1], figsize=(12, 8), legend=True)
    elif chart_type == 'pie':
        df.iloc[:, 1].plot(kind='pie', labels=df.iloc[:, 0], autopct='%1.1f%%', figsize=(12, 8))
    elif chart_type == 'heatmap':
        plt.figure(figsize=(12, 8))
        sns.heatmap(df.corr(), annot=True, cmap='coolwarm', fmt=".2f")
    elif chart_type == 'scatter':
        df.plot(kind='scatter', x=df.columns[0], y=df.columns[1], figsize=(12, 8))

    plt.xticks(rotation=30, ha='right')  # Rotates x-axis labels for clarity
    plt.tight_layout()  # Adjusts layout to fit everything properly
    plt.savefig(chart_path, dpi=300)  # Higher DPI for better quality
    plt.close()  # Closes the figure to prevent memory issues

    return chart_path 

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        file = request.files.get('file')
        chart_type = request.form.get('chart_type', 'bar')  # Fix missing form key
        if file:
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)

            if filename.endswith('.csv'):
                df = pd.read_csv(file_path)
            elif filename.endswith('.pdf'):
                df = extract_table_from_pdf(file_path)
            else:
                return 'Unsupported file format!'

            if df is not None:
                chart_filename = generate_visualization(df, chart_type)
                return render_template('index4.html', chart=chart_filename)
            else:
                return 'No table found!'

    return render_template('index4.html')

if __name__ == '__main__':
    app.run(debug=True)

