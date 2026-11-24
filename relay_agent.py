"""Language Relay Agent — stdlib local server for phone-call interpreting.
Prototype: live mic capture -> EN subtitles -> French voice reply -> EN subtitles.
Translation: MyMemory (free, keyless, CORS-enabled). Speech: browser speechSynthesis.

Phone call reality: a real call needs a telephony platform (Twilio, Vonage,
WhatsApp Business API, French operator app...). This prototype demonstrates the
full relay loop on your phone/PC (demo call simulation + live mic), which is the
hard part. Drop in the call media bridge when you have a provider.

Not financial/legal advice. Nothing is recorded - loop is in memory only.
"""
import json
import threading
import urllib.request
import urllib.parse
import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

MAR = "https://api.mymemory.translated.net/get"
_LOCK = threading.Lock()
_CACHE = {}

DEMO_FR = [
    "Bonjour, comment puis-je vous aider aujourd'hui ?",
    "Tous les numéros sont occupés, veuillez patienter quelques instants.",
    "Votre dossier sera rouvert dans 5 minutes.",
    "Je ne peux pas accéder à votre compte pour le moment.",
    "Je vous passe au service technique.",
    "Votre facture est en attente de paiement.",
]
DEMO_CONVERSATION = [
    "Bonjour, comment puis-je vous aider aujourd'hui ?",
    "Je cherche à parler à quelqu'un qui s'occupe de ma commande.",
    "Merci, je vais vous laisser un message vidéo.",
    "Très bien, un employé vous rappellera sous une heure en français.",
]

USER_OPENERS = [
    "Hi, my name is Alex. I ordered a product and it never arrived. Please call me.",
    "Hello, I need help with my invoice, it's wrong.",
    "I'd like to cancel my subscription before the 1st.",
    "I was charged twice and I want a refund.",
]


def _translate(text, fr_to_en=True):
    if not text:
        return None
    key = (text, fr_to_en)
    now = None
    with _LOCK:
        if key in _CACHE:
            return _CACHE[key]
    url = ("https://api.mymemory.translated.net/get"
           "?q=" + urllib.parse.quote(text)
           + "&langpair=" + ("fr|en" if fr_to_en else "en|fr"))
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.loads(r.read())
        txt = (data.get("responseData") or {}).get("translatedText")
        if txt:
            with _LOCK:
                _CACHE[key] = txt
            return txt
    except Exception as e:  # noqa: BLE001
        print("translate error:", e)
    return None


def translate_en_fr(text):
    return _translate(text, fr_to_en=False)


def translate_fr_en(text):
    return _translate(text, fr_to_en=True)


def demo_fr_phrases():
    out = []
    for fr in DEMO_FR:
        en = translate_fr_en(fr)
        out.append({"id": len(out), "fr": fr, "en": en})
    return out


def demo_convo():
    out = []
    for fr in DEMO_CONVERSATION:
        out.append({"id": len(out), "fr": fr,
                    "en": translate_fr_en(fr) or "unknown"})
    return out


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _json(self, obj, code=200):
        data = json.dumps(obj).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        u = self.path.split("?", 1)[0]
        if u == "/":
            self.serve_file("relay.html", "text/html; charset=utf-8")
        elif u == "/api/languages":
            self._json({"languages": [{"code": "en", "name": "English"},
                                      {"code": "fr", "name": "French"}]})
        elif u == "/api/demo-fr":
            self._json({"phrases": demo_fr_phrases(),
                        "conversation": demo_convo()})
        elif u.startswith("/api/translate"):
            q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            text = (q.get("text") or [""])[0]
            frm = (q.get("from") or ["en"])[0]
            to = (q.get("to") or ["fr"])[0]
            if frm == "fr" and to == "en":
                txt = translate_fr_en(text)
            elif frm == "en" and to == "fr":
                txt = translate_en_fr(text)
            else:
                txt = None
            self._json({"ok": txt is not None, "text": text,
                        "translation": txt})
        else:
            self._send(404, json.dumps({"error": "not found"}))

    def _send(self, code, body, ctype="text/html; charset=utf-8"):
        data = body.encode("utf-8") if isinstance(body, str) else body
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def serve_file(self, name, ctype):
        try:
            with open(name, encoding="utf-8") as f:
                self._send(200, f.read(), ctype)
        except OSError as e:
            self._json({"error": str(e)}, 500)


def main():
    parser = argparse.ArgumentParser(description="Language Relay Agent — phone-call interpreting (EN<->FR).")
    parser.add_argument("--port", type=int, default=8767, help="port to listen on (default 8767)")
    parser.add_argument("--lan", action="store_true",
                        help="bind to 0.0.0.0 so a phone on the same Wi-Fi can connect")
    args = parser.parse_args()
    host = "0.0.0.0" if args.lan else "127.0.0.1"
    suffix = " (same Wi-Fi on phone: http://<PC-LAN-IP>:%d)" % args.port if args.lan else ""
    srv = ThreadingHTTPServer((host, args.port), Handler)
    print("Language Relay Agent: http://%s:%d%s" % (host, args.port, suffix))
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped.")


def _lan_ip():
    try:
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "?"


if __name__ == "__main__":
    main()
