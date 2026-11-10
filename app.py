import os
from urllib.parse import urlparse
import requests
from flask import Flask, request, jsonify, render_template

try:
    from neo4j import GraphDatabase
except ImportError:
    GraphDatabase = None

app = Flask(__name__)

# URL Webhook n8n (Production: /webhook/chat, Testing: /webhook-test/chat)
N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL", "http://localhost:5678/webhook/chat")
N8N_TEST_WEBHOOK_URL = os.getenv("N8N_TEST_WEBHOOK_URL", "http://localhost:5678/webhook-test/chat")

# Neo4j Settings
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password123")

_neo4j_driver = None


def get_neo4j_driver():
    global _neo4j_driver
    if GraphDatabase is None:
        return None
    if _neo4j_driver is None:
        try:
            _neo4j_driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        except Exception:
            _neo4j_driver = None
    return _neo4j_driver


def _derive_n8n_base_url():
    """Return configured n8n base URL or derive it from N8N_WEBHOOK_URL."""
    explicit = os.getenv("N8N_BASE_URL")
    if explicit:
        return explicit.rstrip("/")
    parsed = urlparse(N8N_WEBHOOK_URL)
    if parsed.scheme and parsed.netloc:
        return f"{parsed.scheme}://{parsed.netloc}"
    return "http://localhost:5678"


N8N_BASE_URL = _derive_n8n_base_url()


def extract_n8n_payload(res_json):
    """Normalize dict/list responses from n8n webhooks while preserving safe metadata."""
    target = res_json[0] if isinstance(res_json, list) and len(res_json) > 0 else res_json
    if isinstance(target, dict):
        if "response" in target:
            return target
        for key in ("output", "text"):
            if target.get(key):
                payload = {"response": target[key]}
                for meta_key in ("intent", "privacy_action", "source"):
                    if meta_key in target:
                        payload[meta_key] = target[meta_key]
                return payload
        return {"response": str(target)}
    return {"response": str(res_json)}


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/n8n/status", methods=["GET"])
def n8n_status():
    try:
        r = requests.get(N8N_BASE_URL, timeout=2)
        return jsonify({"status": "online" if 200 <= r.status_code < 400 else "offline"})
    except Exception:
        return jsonify({"status": "offline"})


@app.route("/api/graph/stats", methods=["GET"])
def graph_stats():
    driver = get_neo4j_driver()
    if not driver:
        return jsonify({"status": "disconnected", "nodes": 0, "counts": {}})
    try:
        with driver.session() as session:
            total = session.run("MATCH (n) RETURN count(n) as c").single()["c"]
            prodi = session.run("MATCH (n:ProgramStudi) RETURN count(n) as c").single()["c"]
            lecturers = session.run("MATCH (n:Lecturer) RETURN count(n) as c").single()["c"]
            courses = session.run("MATCH (n:Course) RETURN count(n) as c").single()["c"]
            pages = session.run("MATCH (n:WebPage) RETURN count(n) as c").single()["c"]
            return jsonify({
                "status": "connected",
                "nodes": total,
                "counts": {
                    "prodi": prodi,
                    "lecturers": lecturers,
                    "courses": courses,
                    "pages": pages
                }
            })
    except Exception as e:
        return jsonify({"status": "disconnected", "nodes": 0, "error": str(e), "counts": {}})


@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}
    message = str(data.get("message") or "").strip()
    if not message:
        return jsonify({"response": "Silakan ajukan pertanyaan seputar UPJ."})

    # Forward user message directly to n8n Webhook
    payload = {"message": message}
    headers = {"Content-Type": "application/json"}

    # Attempt to call active production webhook, fallback to test webhook if user is editing in n8n
    target_urls = [N8N_WEBHOOK_URL, N8N_TEST_WEBHOOK_URL]
    last_err = None

    for url in target_urls:
        try:
            res = requests.post(url, json=payload, headers=headers, timeout=60)
            if res.status_code == 200:
                try:
                    # Format standard response object
                    return jsonify(extract_n8n_payload(res.json()))
                except Exception:
                    return jsonify({"response": res.text})
            elif res.status_code == 404:
                last_err = f"Endpoint webhook belum terdaftar/aktif di: {url}"
                continue
            else:
                last_err = f"n8n mengembalikan status {res.status_code}: {res.text}"
        except Exception as e:
            last_err = f"Koneksi ke n8n gagal ({str(e)})"

    # Friendly guidance if n8n webhook is not listening yet
    return jsonify({
        "response": f"⚠️ <b>Webhook n8n Belum Menerima Data:</b><br>{last_err}<br><br>"
                    f"💡 <b>Langkah Aktivasi di n8n:</b><br>"
                    f"1. Buka n8n di <a href='{N8N_BASE_URL}' target='_blank' style='color:#38bdf8;'>{N8N_BASE_URL}</a><br>"
                    f"2. Buka workflow chatbot, lalu klik toggle <b>Active = ON</b> di kanan atas (atau klik tombol <b>Test step</b> pada Webhook untuk mode pengujian).",
        "error": True
    })


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    print(f"Starting Clean Flask Gateway on http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=False)
