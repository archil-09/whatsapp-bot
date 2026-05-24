# ============================================
# INSTAGRAM AI DM BOT (Gemini + Official API)
# ============================================
# INSTALL:
# pip install flask requests google-genai python-dotenv

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
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# ============================================
# GEMINI SETUP (New SDK)
# ============================================

client = genai.Client(api_key=GEMINI_API_KEY)

BOT_PERSONALITY = """
You are replying as a real Instagram user.

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
            model="gemini-2.0-flash",
            contents=prompt
        )
        return response.text.strip()
    except Exception as e:
        print("Gemini Error:", e)
        return "hey, something went wrong on my end — try again!"

# ============================================
# SEND DM VIA META API
# ============================================

def send_message(recipient_id: str, text: str):
    url = "https://graph.facebook.com/v19.0/me/messages"
    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": text},
        "access_token": ACCESS_TOKEN
    }
    res = requests.post(url, json=payload)
    print(f"Sent to {recipient_id}: {res.status_code}")

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
# RECEIVE & REPLY TO DMs
# ============================================

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    try:
        for entry in data.get("entry", []):
            for event in entry.get("messaging", []):

                sender_id = event["sender"]["id"]
                message_data = event.get("message", {})
                text = message_data.get("text", "")

                # Skip empty or echo messages
                if not text or message_data.get("is_echo"):
                    continue

                print(f"\nNew DM from {sender_id}: {text}")

                # Generate AI reply
                reply = generate_reply(text)
                print(f"Gemini Reply: {reply}")

                # Send it back
                send_message(sender_id, reply)

    except Exception as e:
        print("Webhook Error:", e)

    return jsonify({"status": "ok"}), 200

# ============================================
# RUN
# ============================================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

