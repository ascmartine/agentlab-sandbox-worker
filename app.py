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

    client = get_client()
    c = None

    try:
        try:
            client.images.pull(image)
        except Exception:
            pass

        # NO remove=True aquí (para poder leer logs seguro)
        c = client.containers.run(
            image=image,
            command=["sh", "-lc", cmd],
            detach=True,
        )

        result = c.wait(timeout=120)
        rc = int(result.get("StatusCode", 1))

        out = ""
        err = ""
        try:
            out = c.logs(stdout=True, stderr=False).decode("utf-8", errors="replace")
        except Exception:
            pass
        try:
            err = c.logs(stdout=False, stderr=True).decode("utf-8", errors="replace")
        except Exception:
            pass

        return jsonify({
            "returncode": rc,
            "stdout": out,
            "stderr": err
        }), 200 if rc == 0 else 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        if c is not None:
            try:
                c.remove(force=True)
            except Exception:
                pass

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "8081")))
