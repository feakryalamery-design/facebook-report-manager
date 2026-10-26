import os
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.get("/")
def home():
    return jsonify({
        "status": "online",
        "message": "Server is running"
    })

@app.post("/api/reports")
def receive_report():
    data = request.get_json(silent=True) or {}
    link = data.get("link", "").strip()
    details = data.get("details", "").strip()

    if not link.startswith("https://www.facebook.com/"):
        return jsonify({
            "success": False,
            "message": "Invalid Facebook link"
        }), 400

    if not details:
        return jsonify({
            "success": False,
            "message": "Please provide details"
        }), 400

    return jsonify({
        "success": True,
        "message": "Request received for manual review only. Nothing was sent to Facebook."
    })

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 10000))
    )
