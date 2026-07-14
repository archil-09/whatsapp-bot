# whatsapp-bot
# WhatsApp AI Bot (Groq + WhatsApp Cloud API)

A lightweight Flask bot that connects to the official **WhatsApp Cloud API** and replies to incoming messages using **Groq's** `llama-3.3-70b-versatile` model. The bot is prompted to reply like a real person — short, casual, human-sounding messages instead of a typical "AI assistant" tone.

## How it works

1. WhatsApp sends incoming messages to a `/webhook` endpoint via the Cloud API.
2. The bot extracts the message text and sender, and sends it to Groq for a reply.
3. The generated reply is sent back to the sender using the Cloud API's `/messages` endpoint.

## Requirements

- Python 3.9+
- A [Meta developer app](https://developers.facebook.com/) with WhatsApp Cloud API access
- A [Groq API key](https://console.groq.com/)

## Setup

1. **Clone the repo**

   ```bash
   git clone https://github.com/archil-09/whatsapp-bot.git
   cd whatsapp-bot
   ```

2. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

3. **Create a `.env` file** in the project root:

   ```env
   ACCESS_TOKEN=your_whatsapp_access_token
   PHONE_NUMBER_ID=your_whatsapp_phone_number_id
   VERIFY_TOKEN=any_string_you_choose
   GROQ_API_KEY=your_groq_api_key
   ```

   - `ACCESS_TOKEN` / `PHONE_NUMBER_ID` come from your Meta app's WhatsApp > API Setup page.
   - `VERIFY_TOKEN` is a value you invent yourself — you'll enter the same value in the Meta webhook config.
   - `GROQ_API_KEY` comes from the Groq console.

4. **Run locally**

   ```bash
   python app.py
   ```

   The app runs on port `5000` by default (or `$PORT` if set).

## Configuring the WhatsApp webhook

1. Expose your local server publicly if testing locally (e.g. with [ngrok](https://ngrok.com/)):

   ```bash
   ngrok http 5000
   ```

2. In your Meta app's WhatsApp > Configuration page, set:
   - **Callback URL**: `https://<your-domain>/webhook`
   - **Verify token**: the same value as `VERIFY_TOKEN` in your `.env`

3. Subscribe to the `messages` webhook field.

Meta will send a `GET` request to verify the callback URL (handled by the `/webhook` GET route), then send incoming messages as `POST` requests.

## Deployment (Railway)

This repo includes a `railway.toml` configured to run the app with Gunicorn:

```toml
[deploy]
startCommand = "gunicorn app:app --bind 0.0.0.0:5000"
```

To deploy:

1. Push the repo to Railway (via GitHub integration or CLI).
2. Add the same environment variables (`ACCESS_TOKEN`, `PHONE_NUMBER_ID`, `VERIFY_TOKEN`, `GROQ_API_KEY`) in Railway's project settings.
3. Update the Meta webhook callback URL to your Railway deployment URL.

## Customizing the bot's personality

The reply style is controlled by the `BOT_PERSONALITY` system prompt in `app.py`. Edit this string to change tone, length, or behavior.

## Notes

- Only text messages are handled; other message types (images, audio, etc.) are currently ignored.
- `requirements.txt` includes `google-genai`, which isn't used by the current code — remove it if you don't plan to add Gemini support.
