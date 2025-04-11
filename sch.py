from flask import Flask, render_template, request, redirect, url_for, send_file, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import datetime
import os
import csv

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tasks.db'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
db = SQLAlchemy(app)

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(50), default="General")
    priority = db.Column(db.String(20), default="Medium")
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    progress = db.Column(db.String(20), default="Not Started")
    assigned_to = db.Column(db.String(100))
    parent_task_id = db.Column(db.Integer, db.ForeignKey('task.id'))
    is_recurring = db.Column(db.Boolean, default=False)
    recurrence_type = db.Column(db.String(20))
    status = db.Column(db.String(20), default="Pending")
    file_attachment = db.Column(db.String(300))

with app.app_context():
    db.create_all()
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@app.route('/')
def index():
    return render_template('index6.html')

@app.route('/add_task', methods=['POST'])
def add_task():
    try:
        data = request.get_json()
        title = data.get('name')
        description = data.get('description')
        priority = data.get('priority')
        due_date = data.get('due_date')
        start_time_input = data.get('start_time')  # in format 'HH:MM'
        end_time_input = data.get('end_time')      # in format 'HH:MM'
        status = data.get('status')                # maps to Task.progress

        if not title or not priority or not due_date or not start_time_input or not end_time_input or not status:
            return jsonify({'error': 'Missing required fields'}), 400

        start_time = datetime.datetime.strptime(f"{due_date}T{start_time_input}", "%Y-%m-%dT%H:%M")
        end_time = datetime.datetime.strptime(f"{due_date}T{end_time_input}", "%Y-%m-%dT%H:%M")

        new_task = Task(
            title=title,
            description=description,
            priority=priority,
            start_time=start_time,
            end_time=end_time,
            progress=status
        )

        db.session.add(new_task)
        db.session.commit()
        return jsonify({"message": "Task added successfully"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/get_tasks')
def get_tasks():
    tasks = Task.query.order_by(Task.start_time.asc()).all()
    return jsonify([{
        'id': t.id,
        'name': t.title,
        'description': t.description,
        'due_date': t.start_time.strftime('%Y-%m-%d'),
        'status': t.progress,
        'priority': t.priority
    } for t in tasks])

@app.route('/update_task/<int:id>', methods=['POST'])
def update_task(id):
    try:
        task = Task.query.get_or_404(id)
        data = request.get_json()
        task.progress = data.get('status', task.progress)
        db.session.commit()
        return jsonify({"message": "Task updated successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/delete_task/<int:id>', methods=['DELETE'])
def delete_task(id):
    try:
        task = Task.query.get_or_404(id)
        db.session.delete(task)
        db.session.commit()
        return jsonify({"message": "Task deleted successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/dashboard')
def dashboard():
    now = datetime.datetime.now()
    stats = {
        'completed': Task.query.filter_by(progress="Completed").count(),
        'pending': Task.query.filter_by(progress="Not Started").count(),
        'overdue': Task.query.filter(Task.end_time < now, Task.progress != "Completed").count(),
        'almost_due': Task.query.filter(Task.end_time.between(now, now + datetime.timedelta(hours=3))).count()
    }
    return render_template('dashboard1.html', stats=stats)

@app.route('/export_tasks')
def export_tasks():
    try:
        tasks = Task.query.all()
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], "tasks.csv")

        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["Title", "Description", "Category", "Priority", "Start Time", "End Time", "Progress", "Assigned To"])
            for t in tasks:
                writer.writerow([
                    t.title, t.description, t.category, t.priority,
                    t.start_time.strftime("%Y-%m-%d %H:%M"),
                    t.end_time.strftime("%Y-%m-%d %H:%M"),
                    t.progress, t.assigned_to
                ])
        return send_file(file_path, as_attachment=True)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/upload_file/<int:task_id>', methods=['POST'])
def upload_file(task_id):
    try:
        task = Task.query.get_or_404(task_id)
        file = request.files['file']
        if file:
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            task.file_attachment = filename
            db.session.commit()
            return jsonify({"message": "File uploaded successfully"})
        return jsonify({"error": "No file provided"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
