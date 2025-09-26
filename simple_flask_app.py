from flask import Flask, jsonify

app = Flask(__name__)


@app.route("/")
def hello():
    """Root endpoint that returns a welcome message"""
    return jsonify({"message": "Welcome to the Simple Flask API!", "status": "success"})


@app.route("/health")
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "service": "Simple Flask App"})


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
