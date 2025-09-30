from flask import Flask, jsonify

app = Flask(__name__)


@app.route("/hello", methods=["GET"])
def hello():
    return jsonify({"message": "Hello, World!", "status": "success"})


@app.route("/hello/<name>", methods=["GET"])
def hello_name(name):
    return jsonify({"message": f"Hello, {name}!", "status": "success"})


@app.route("/", methods=["GET"])
def home():
    return jsonify(
        {
            "message": "Welcome to Flask REST API",
            "endpoints": ["/hello", "/hello/<name>"],
        }
    )


if __name__ == "__main__":
    app.run(debug=True, port=5000)
