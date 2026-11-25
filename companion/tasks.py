import logging

from celery import shared_task

from .agents.agent import run_companion_agent, save_memory
from .models import ChatMessage

logger = logging.getLogger(__name__)


@shared_task
def process_telegram_message(user_id, chat_id, text):
    from .telegram_utils import send_telegram_message

    try:
        reply = run_companion_agent(user_message=text, user_id=user_id)
    except Exception:
        logger.exception("Agent failed for user %s", user_id)
        send_telegram_message(chat_id, "Sorry, something went wrong. Please try again.")
        return

    ChatMessage.objects.create(user_id=user_id, user_message=text, ai_response=reply)
    send_telegram_message(chat_id, reply)
    store_memory.delay(user_id, text, reply)


@shared_task
def store_memory(user_id, user_message, ai_reply):
    save_memory(user_id, user_message, ai_reply)
