from flask import Flask, request, jsonify
import docker
import os
import uuid

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
    timeout = int(data.get("timeout", 120))

    client = get_client()
    name = f"job-{uuid.uuid4().hex[:12]}"

    try:
        try:
            client.images.pull(image)
        except Exception:
            pass

        # Ejecuta en foreground y captura salida directamente (evita logs 409)
        output = client.containers.run(
            image=image,
            command=["sh", "-lc", cmd],
            name=name,
            remove=False,      # lo borramos nosotros después
            detach=False,      # output directo
            stdout=True,
            stderr=True,
        )

        # output es bytes
        stdout = output.decode("utf-8", errors="replace")

        # obtener exit code del contenedor
        c = client.containers.get(name)
        rc = int(c.wait(timeout=timeout).get("StatusCode", 1))

        return jsonify({
            "returncode": rc,
            "stdout": stdout,
            "stderr": ""
        }), 200 if rc == 0 else 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        # cleanup best-effort
        try:
            c = client.containers.get(name)
            c.remove(force=True)
        except Exception:
            pass

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "8081")))
