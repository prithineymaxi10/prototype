from flask import Flask, render_template, Response, request, jsonify
import subprocess
import threading
import queue

app = Flask(__name__)
assistant_process = None
input_queue = queue.Queue()

def enqueue_input():
    """Continuously send input from the queue to the assistant process."""
    global assistant_process
    while assistant_process and assistant_process.poll() is None:
        try:
            input_text = input_queue.get(timeout=1)
            if assistant_process.stdin:
                assistant_process.stdin.write(input_text + '\n')
                assistant_process.stdin.flush()
        except queue.Empty:
            continue

@app.route('/')
def index():
    return render_template('assistant.html')

@app.route('/stream')
def stream():
    def generate():
        global assistant_process

        assistant_process = subprocess.Popen(
            ['python', '-u', 'assistant.py'],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            stdin=subprocess.PIPE,
            text=True,
            bufsize=1
        )

        # Start a thread to handle input
        threading.Thread(target=enqueue_input, daemon=True).start()

        try:
            for line in iter(assistant_process.stdout.readline, ''):
                if assistant_process.poll() is not None:
                    break
                yield f"data: {line.strip()}\n\n"
        except GeneratorExit:
            if assistant_process:
                assistant_process.terminate()
        finally:
            if assistant_process and assistant_process.stdout:
                assistant_process.stdout.close()
            assistant_process = None

    return Response(generate(), mimetype='text/event-stream')

@app.route('/stop', methods=['POST'])
def stop():
    global assistant_process
    if assistant_process and assistant_process.poll() is None:
        assistant_process.terminate()
        assistant_process = None
        return "Assistant stopped", 200
    return "No process running", 200

@app.route('/typed-input', methods=['POST'])
def typed_input():
    data = request.get_json()
    user_text = data.get('text', '')
    input_queue.put(user_text)
    return jsonify({"status": "sent to assistant"}), 200

if __name__ == '__main__':
    app.run(debug=True, threaded=True)

