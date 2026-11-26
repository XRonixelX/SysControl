"""
SysControl - Telegram integration module
"""
import requests
import threading


class TelegramBot:
    def __init__(self):
        self.token = ""
        self.chat_id = ""

    def configure(self, token, chat_id):
        self.token = token.strip()
        self.chat_id = chat_id.strip()

    def is_configured(self):
        return bool(self.token and self.chat_id)

    def send_message(self, text, callback=None):
        if not self.is_configured():
            if callback:
                callback(False, "Bot token or Chat ID not configured")
            return

        def _send():
            try:
                url = f"https://api.telegram.org/bot{self.token}/sendMessage"
                data = {
                    "chat_id": self.chat_id,
                    "text": text,
                    "parse_mode": "HTML",
                }
                r = requests.post(url, data=data, timeout=10)
                if r.status_code == 200:
                    if callback:
                        callback(True, "Message sent successfully!")
                else:
                    err = r.json().get("description", "Unknown error")
                    if callback:
                        callback(False, f"Error: {err}")
            except Exception as e:
                if callback:
                    callback(False, f"Connection error: {str(e)}")

        threading.Thread(target=_send, daemon=True).start()

    def send_alert(self, title, body, callback=None):
        text = f"<b>🚨 {title}</b>\n\n{body}"
        self.send_message(text, callback)

    def send_report(self, report_text, callback=None):
        text = f"<b>📊 SysControl Report</b>\n\n<pre>{report_text}</pre>"
        self.send_message(text, callback)
