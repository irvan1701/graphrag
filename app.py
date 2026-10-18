import os
import requests
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

# URL Webhook n8n (Production: /webhook/chat, Testing: /webhook-test/chat)
N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL", "http://localhost:5678/webhook/chat")
N8N_TEST_WEBHOOK_URL = os.getenv("N8N_TEST_WEBHOOK_URL", "http://localhost:5678/webhook-test/chat")

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/n8n/status", methods=["GET"])
def n8n_status():
    try:
        r = requests.get("http://localhost:5678", timeout=2)
        return jsonify({"status": "online" if r.status_code == 200 else "offline"})
    except Exception:
        return jsonify({"status": "offline"})

@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json() or {}
    message = data.get("message", "").strip()
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
                    res_json = res.json()
                    # Format standard response object
                    if isinstance(res_json, dict):
                        if "response" in res_json:
                            return jsonify(res_json)
                        elif "output" in res_json:
                            return jsonify({"response": res_json["output"]})
                        elif "text" in res_json:
                            return jsonify({"response": res_json["text"]})
                        return jsonify({"response": str(res_json)})
                    elif isinstance(res_json, list) and len(res_json) > 0:
                        first = res_json[0]
                        if isinstance(first, dict):
                            val = first.get("response") or first.get("output") or first.get("text")
                            if val:
                                return jsonify({"response": val})
                        return jsonify({"response": str(first)})
                    return jsonify({"response": str(res_json)})
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
                    f"1. Buka n8n di <a href='http://localhost:5678' target='_blank' style='color:#38bdf8;'>http://localhost:5678</a><br>"
                    f"2. Buka workflow chatbot, lalu klik toggle <b>Active = ON</b> di kanan atas (atau klik tombol <b>Test step</b> pada Webhook untuk mode pengujian).",
        "error": True
    })

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5001))
    print(f"Starting Clean Flask Gateway on http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=False)
