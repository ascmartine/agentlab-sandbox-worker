from flask import Flask, request, jsonify
import subprocess
import os

app = Flask(__name__)

@app.get("/health")
def health():
    return "ok", 200

@app.post("/run")
def run():
    data = request.get_json(force=True) or {}
    image = data.get("image", "alpine:3.20")
    cmd = data.get("cmd", "echo hello")

    p = subprocess.run(
        ["docker", "run", "--rm", image, "sh", "-lc", cmd],
        capture_output=True, text=True
    )

    return jsonify({
        "returncode": p.returncode,
        "stdout": p.stdout,
        "stderr": p.stderr
    }), 200 if p.returncode == 0 else 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "8081")))
