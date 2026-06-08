# ============================================
# DENTAL CLINIC WHATSAPP BOT (Groq + Official API)
# ============================================
from flask import Flask, request, jsonify
import requests
from groq import Groq
from dotenv import load_dotenv
import os
import json
from datetime import datetime

load_dotenv()
app = Flask(__name__)

# ============================================
# CONFIG
# ============================================
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

groq_client = Groq(api_key=GROQ_API_KEY)

# ============================================
# CLINIC INFO — EDIT THIS FOR EACH CLIENT
# ============================================
CLINIC_INFO = {
    "name": "SmileCare Dental Clinic",
    "doctor": "Dr. Priya Sharma",
    "address": "123, Vijay Nagar, Indore",
    "timings": "Mon–Sat: 10am to 2pm, 5pm to 9pm. Sunday: Closed.",
    "services": [
        "Teeth Cleaning", "Cavity Filling", "Root Canal",
        "Tooth Extraction", "Braces & Aligners", "Teeth Whitening",
        "Dental X-Ray", "Crowns & Bridges"
    ],
    "fees": "Consultation: ₹300. Treatment fees vary by procedure.",
    "phone": "9876543210",
    "available_slots": [
        "Monday 10am", "Monday 11am", "Monday 5pm", "Monday 6pm",
        "Tuesday 10am", "Tuesday 11am", "Tuesday 5pm", "Tuesday 6pm",
        "Wednesday 10am", "Wednesday 5pm", "Wednesday 6pm",
        "Thursday 10am", "Thursday 11am", "Thursday 5pm",
        "Friday 10am", "Friday 11am", "Friday 5pm", "Friday 6pm",
        "Saturday 10am", "Saturday 11am", "Saturday 5pm"
    ]
}

# ============================================
# CONVERSATION MEMORY (in-memory store)
# For production use Redis or a database
# ============================================
conversation_history = {}  # {phone_number: [messages]}
appointment_data = {}      # {phone_number: {name, date, service, status}}

# ============================================
# BOT PERSONALITY + SYSTEM PROMPT
# ============================================
def get_system_prompt():
    slots_text = ", ".join(CLINIC_INFO["available_slots"])
    services_text = ", ".join(CLINIC_INFO["services"])

    return f"""
You are a friendly WhatsApp receptionist for {CLINIC_INFO["name"]}.
Doctor: {CLINIC_INFO["doctor"]}
Address: {CLINIC_INFO["address"]}
Timings: {CLINIC_INFO["timings"]}
Services: {services_text}
Fees: {CLINIC_INFO["fees"]}
Contact: {CLINIC_INFO["phone"]}
Available slots: {slots_text}

YOUR JOB:
You help patients book dental appointments step by step.

BOOKING FLOW — follow this exact order:
Step 1: Greet warmly and ask what service they need
Step 2: Ask their preferred day/time from available slots
Step 3: Ask their full name
Step 4: Ask their age
Step 5: Confirm all details and say "Your appointment is CONFIRMED ✅"

RULES:
- Reply in the same language the patient uses (Hindi/English/Hinglish)
- Keep replies short — max 3 lines
- Be warm, friendly, and professional
- If asked about fees/services/timings, answer from clinic info above
- If patient says something unrelated to dental/clinic, politely redirect
- Never make up information not in the clinic info
- For emergencies say: "Please call {CLINIC_INFO["phone"]} immediately for urgent cases"
- After confirming appointment always add: "See you at {CLINIC_INFO["name"]}! 😊"

APPOINTMENT CONFIRMATION FORMAT:
Always confirm like this:
✅ Appointment Confirmed!
👤 Name: [name]
🦷 Service: [service]
📅 Slot: [slot]
📍 {CLINIC_INFO["address"]}
📞 Questions? Call {CLINIC_INFO["phone"]}
"""

# ============================================
# AI REPLY WITH MEMORY
# ============================================
def generate_reply(sender: str, message: str) -> str:
    try:
        # Initialize history for new users
        if sender not in conversation_history:
            conversation_history[sender] = []

        # Add user message to history
        conversation_history[sender].append({
            "role": "user",
            "content": message
        })

        # Keep only last 10 messages to avoid token overflow
        recent_history = conversation_history[sender][-10:]

        # Call Groq
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": get_system_prompt()},
                *recent_history
            ],
            temperature=0.7,
            max_tokens=300
        )

        reply = response.choices[0].message.content.strip()

        # Save bot reply to history
        conversation_history[sender].append({
            "role": "assistant",
            "content": reply
        })

        print(f"User ({sender}): {message}")
        print(f"Bot: {reply}")
        return reply

    except Exception as e:
        print(f"Groq Error: {type(e).__name__}: {e}")
        return f"Sorry, something went wrong. Please call us at {CLINIC_INFO['phone']} to book your appointment. 🙏"

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
# SEND WELCOME MESSAGE (first time users)
# ============================================
def send_welcome(to: str):
    welcome = f"""👋 Welcome to {CLINIC_INFO["name"]}!

I'm your virtual assistant. I can help you:
🦷 Book an appointment
⏰ Check clinic timings
💰 Know about our services & fees

How can I help you today?"""
    send_message(to, welcome)

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
    print("Incoming:", data)

    try:
        for entry in data.get("entry", []):
            for change in entry.get("changes", []):
                value = change.get("value", {})
                messages = value.get("messages", [])

                for message in messages:
                    sender = message["from"]
                    msg_type = message.get("type")

                    # Handle text messages only
                    if msg_type != "text":
                        send_message(sender, "Please send a text message to book your appointment 😊")
                        continue

                    text = message["text"]["body"].strip()

                    # First time user — send welcome
                    is_new_user = sender not in conversation_history
                    if is_new_user:
                        send_welcome(sender)

                    # Generate and send AI reply
                    reply = generate_reply(sender, text)
                    send_message(sender, reply)

    except Exception as e:
        print("Webhook Error:", e)

    return jsonify({"status": "ok"}), 200

# ============================================
# HEALTH CHECK
# ============================================
@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "status": "running",
        "clinic": CLINIC_INFO["name"],
        "bot": "active"
    }), 200

# ============================================
# RUN
# ============================================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
