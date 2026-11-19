# Echo

An AI companion you can talk to on Telegram. Echo remembers your conversations,
gets to know you over time, and can help with small things like reminders.

## Features
- Natural conversation on Telegram, powered by an AI agent (LangGraph + Groq)
- Long-term memory of what you share (Mem0)
- Reminders you can set just by chatting, delivered back to you on Telegram

## Tech stack
Django, Django REST Framework, Celery + Redis, LangGraph, Groq, Mem0, Telegram Bot API

## Setup
1. Clone the repo and create a virtual environment
2. `pip install -r requirements.txt`
3. Copy `.env.example` to `.env` and fill in the values
4. `python manage.py migrate`
5. Start Redis, then run:
   - `python manage.py runserver`
   - `celery -A echo worker -l info`
   - `celery -A echo beat -l info`
6. Set your Telegram webhook to `https://<your-url>/api/webhook/telegram/`
   with the same secret as `TELEGRAM_WEBHOOK_SECRET`

## Tests
`python manage.py test`