from flask import Flask, request, jsonify
import docker
import os

app = Flask(__name__)

def get_client():
    return docker.DockerClient(base_url="unix://var/run/docker.sock")

@app.get("/health")
def health():
    return "ok", 200

@app.post("/run")
def run():
    data = request.get_json(force=True) or {}
    image = data.get("image", "alpine:3.20")
    cmd = data.get("cmd", "echo hello")

    try:
        client = get_client()

        try:
            client.images.pull(image)
        except Exception:
            pass

        c = client.containers.run(
            image=image,
            command=["sh", "-lc", cmd],
            remove=True,
            detach=True,
        )

        result = c.wait(timeout=120)
        logs = c.logs(stdout=True, stderr=True).decode("utf-8", errors="replace")

        rc = int(result.get("StatusCode", 1))
        return jsonify({
            "returncode": rc,
            "stdout": logs,
            "stderr": ""
        }), 200 if rc == 0 else 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "8081")))
