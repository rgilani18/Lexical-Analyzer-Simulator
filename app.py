from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import sys

# THIS IS THE KEY CHANGE — handles both normal run and PyInstaller .exe
def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        # Running as .exe — PyInstaller extracts files here
        return os.path.join(sys._MEIPASS, relative_path)
    # Running normally as .py
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), relative_path)

app = Flask(__name__, template_folder=resource_path('templates'))
CORS(app)

from automata import analyze

def tpl(name):
    return send_file(resource_path(os.path.join('templates', name)))

@app.route('/')
def home():
    return tpl('home.html')

@app.route('/analyzer')
def analyzer():
    return tpl('index.html')

@app.route('/visual')
def visual():
    return tpl('visual.html')

@app.route('/visual_nfa')
def visual_nfa():
    return tpl('visual_nfa.html')

@app.route('/visual_enfa')
def visual_enfa():
    return tpl('visual_enfa.html')

@app.route('/analyze', methods=['POST'])
def analyze_code():
    data = request.get_json()
    source = data.get('source', '')
    if not source.strip():
        return jsonify({"error": "Empty input"}), 400
    try:
        result = analyze(source)
        return jsonify(result)
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

@app.route('/examples', methods=['GET'])
def get_examples():
    examples = [
        {"label": "Valid: int declaration",    "code": "int a = 1;"},
        {"label": "Valid: multiple tokens",    "code": "int x = 10;\nfloat y = 3.14;\nreturn x;"},
        {"label": "Valid: condition",          "code": "if (x == 5) { return true; }"},
        {"label": "Invalid: digit-start id",   "code": "int 2a = 1;"},
        {"label": "Invalid: bad char literal", "code": "char c = 'ab';"},
        {"label": "Mixed valid+invalid",       "code": "int a = 1;\nint 3b = 2;"},
    ]
    return jsonify(examples)

if __name__ == '__main__':
    import webbrowser
    import threading

    # Auto-opens the browser when .exe is double-clicked
    def open_browser():
        import time
        time.sleep(1.5)
        webbrowser.open('http://localhost:5050')

    threading.Thread(target=open_browser, daemon=True).start()

    print("\n✅ Lexical Analyzer running at http://localhost:5050")
    print("   Open your browser if it doesn't open automatically.")
    print("   Press Ctrl+C to stop.\n")

    app.run(debug=False, port=5050, host='0.0.0.0')