"""
Flask application — Autonomous Research Assistant.
Provides the web interface and API endpoints for the research pipeline.
"""
import json
import queue
import threading
from flask import Flask, render_template, request, jsonify, Response

from config import Config
from orchestrator import ResearchOrchestrator

app = Flask(__name__)
app.config.from_object(Config)

# In-memory session storage (for demo; could be Redis/DB for production)
sessions: dict[str, dict] = {}
event_queues: dict[str, queue.Queue] = {}


@app.route("/")
def index():
    """Serve the main UI."""
    return render_template("index.html")


@app.route("/api/research", methods=["POST"])
def start_research():
    """Start a new autonomous research session."""
    data = request.get_json()
    topic = data.get("topic", "").strip()
    if not topic:
        return jsonify({"error": "Topic is required."}), 400

    if not Config.GEMINI_API_KEY or Config.GEMINI_API_KEY == "your_gemini_api_key_here":
        return jsonify({"error": "GEMINI_API_KEY is not configured. Please set it in your .env file."}), 500

    import uuid
    session_id = str(uuid.uuid4())[:8]
    event_queues[session_id] = queue.Queue()

    def run_research():
        orchestrator = ResearchOrchestrator()

        def progress_callback(stage, message, data=None):
            event_queues[session_id].put({
                "stage": stage,
                "message": message,
                "data": data,
            })

        result = orchestrator.run(topic, progress_callback=progress_callback)
        sessions[session_id] = result
        event_queues[session_id].put({"stage": "done", "message": "Session complete.", "data": None})

    thread = threading.Thread(target=run_research, daemon=True)
    thread.start()

    return jsonify({"session_id": session_id, "status": "started"})


@app.route("/api/research/<session_id>/stream")
def stream_events(session_id):
    """Server-Sent Events stream for real-time progress updates."""
    if session_id not in event_queues:
        return jsonify({"error": "Session not found."}), 404

    def generate():
        q = event_queues[session_id]
        while True:
            try:
                event = q.get(timeout=120)
                yield f"data: {json.dumps(event)}\n\n"
                if event.get("stage") in ("done", "error", "complete"):
                    break
            except queue.Empty:
                yield f"data: {json.dumps({'stage': 'heartbeat', 'message': 'Still working...'})}\n\n"

    return Response(generate(), mimetype="text/event-stream")


@app.route("/api/research/<session_id>")
def get_session(session_id):
    """Get the full results of a completed research session."""
    if session_id not in sessions:
        return jsonify({"error": "Session not found or still running."}), 404
    return jsonify(sessions[session_id])


if __name__ == "__main__":
    app.run(debug=True, port=5000, threaded=True)
