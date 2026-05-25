# ============================================
# WHATSAPP AI BOT (Gemini + Official API)
# ============================================
from flask import Flask, request, jsonify
import requests
from google import genai
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)

# ============================================
# CONFIG
# ============================================

ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# ============================================
# GEMINI SETUP
# ============================================

client = genai.Client(api_key=GEMINI_API_KEY)

BOT_PERSONALITY = """
You are replying as a real WhatsApp user.

Style:
- casual and friendly
- short replies (max 2 lines)
- human sounding
- slightly funny when appropriate
- never too formal
- don't sound like AI

Always stay helpful and on-topic.
"""

# ============================================
# GEMINI REPLY FUNCTION
# ============================================

def generate_reply(message: str) -> str:
    prompt = f"""
{BOT_PERSONALITY}

User message: {message}

Reply naturally.
"""
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash-lite",
            contents=prompt
        )
        return response.text.strip()
    except Exception as e:
        print("Gemini Error:", e)
        return "hey, something went wrong — try again!"

# ============================================
# SEND WHATSAPP MESSAGE
# ============================================

def send_message(to: str, text: str):
    url = f"https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": text}
    }
    res = requests.post(url, headers=headers, json=payload)
    print(f"Sent to {to}: {res.status_code} {res.text}")

# ============================================
# WEBHOOK VERIFICATION
# ============================================

@app.route("/webhook", methods=["GET"])
def verify():
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    if token == VERIFY_TOKEN:
        return challenge, 200
    return "Forbidden", 403

# ============================================
# RECEIVE & REPLY TO MESSAGES
# ============================================

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    print("Incoming data:", data)
    try:
        for entry in data.get("entry", []):
            for change in entry.get("changes", []):
                value = change.get("value", {})
                messages = value.get("messages", [])
                for message in messages:
                    sender = message["from"]
                    msg_type = message.get("type")

                    if msg_type != "text":
                        continue

                    text = message["text"]["body"]
                    print(f"\nNew message from {sender}: {text}")

                    reply = generate_reply(text)
                    print(f"Gemini Reply: {reply}")

                    send_message(sender, reply)

    except Exception as e:
        print("Webhook Error:", e)

    return jsonify({"status": "ok"}), 200

# ============================================
# RUN
# ============================================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
    
