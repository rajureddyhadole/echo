import logging

from celery import shared_task

from .agents.agent import run_companion_agent

logger = logging.getLogger(__name__)


@shared_task
def process_telegram_message(user_id, chat_id, text):
    from .telegram_utils import send_telegram_message

    try:
        reply = run_companion_agent(user_message=text, user_id=user_id)
    except Exception:
        logger.exception("Agent failed for user %s", user_id)
        reply = "Sorry, something went wrong. Please try again."
    send_telegram_message(chat_id, reply)
