from typing import Annotated, TypedDict

from django.conf import settings
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from langchain_core.messages import AIMessage, AnyMessage, HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from langchain_groq import ChatGroq
from langgraph.graph import END, START, StateGraph, add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from mem0 import MemoryClient

from companion.models import ChatMessage
from reminders.models import Reminder

model = ChatGroq(
    model="openai/gpt-oss-20b",
    temperature=0.7,
    api_key=settings.GROQ_API_KEY,
)
mem0_client = MemoryClient(api_key=settings.MEM0_API_KEY)


@tool
def create_reminder(title: str, remind_at: str, config: RunnableConfig) -> str:
    """Create a new reminder.

    Args:
        title: What the reminder is about (e.g., "Call mom").
        remind_at: When to remind them, as an ISO 8601 date and time with
            a timezone offset, e.g. "2026-11-18T17:00:00+05:30".
            Work this out from the current date and time you were given.
    """
    configurable = config.get("configurable", {})
    user_id = configurable.get("user_id")

    if not user_id:
        return "Error: User Identification missing for creating reminder."

    try:
        parsed_time = parse_datetime(remind_at)
        if not parsed_time:
            return f"Could not parse date/time '{remind_at}'. Please provide a valid timestamp."

        Reminder.objects.create(
            user_id=user_id, title=title, remind_at=parsed_time, is_notified=False
        )
        return f"Successfully saved reminder: “{title}” for {remind_at}."
    except Exception as e:
        print(f"Error saving reminder to database: {e}")
        return "Failed to save reminder due to a database error."


@tool
def get_reminders(config: RunnableConfig) -> str:
    """Retrieve and list all saved reminders from the database."""
    user_id = config.get("configurable", {}).get("user_id")
    if not user_id:
        return "Error: User Identification missing for fetching reminders."

    try:
        reminders = Reminder.objects.filter(
            user_id=user_id, is_notified=False
        ).order_by("remind_at")
        if not reminders.exists():
            return "You currently have no reminders saved."

        reminder_list = "\n".join(
            f"- {r.title} ({timezone.localtime(r.remind_at).strftime('%d %b, %I:%M %p')})"
            for r in reminders
        )
        return f"Here are your current reminders:\n{reminder_list}"
    except Exception as e:
        print(f"Error fetching reminders {e}")
        return "Failed to retrieve reminders due to a database error."


tools = [create_reminder, get_reminders]
model_with_tools = model.bind_tools(tools)


class AgentState(TypedDict):
    user_id: str
    messages: Annotated[list[AnyMessage], add_messages]
    context: str
    reply: str


def retrieve_memory_node(state: AgentState) -> AgentState:
    user_id = state["user_id"]
    latest_message = state["messages"][-1].content

    print(f"Fetching memories for user: {user_id}")
    memories = mem0_client.search(query=latest_message, filters={"user_id": user_id})

    context_str = "\n".join([m.get("memory", "") for m in memories.get("results", [])])
    state["context"] = context_str
    return state


PERSONA = """You are Echo, a warm and friendly AI companion chatting with the user on Telegram.

- Talk like a caring friend: natural, relaxed and kind. Keep replies short, usually 1-3 sentences.
- Be curious about the user's day, feelings and goals. Ask one gentle follow-up question at a time.
- Use what you remember about the user, but don't list facts back to them.
- If the user wants to be reminded of something, use the reminder tools.
- Write plain text only. Telegram will show symbols like ** and # as they are, so don't use markdown.
- If you don't know something, say so honestly."""


def call_llm_node(state: AgentState) -> AgentState:
    context = state["context"]

    current_time = timezone.localtime().strftime("%A, %B %d, %Y at %I:%M %p (UTC%z)")

    system_prompt = SystemMessage(
        content=f"""{PERSONA}
    Current Date & Time: {current_time}

    Relevant background memory about the user:
    {context if context else "None"}"""
    )

    messages = [system_prompt] + state["messages"]

    print("Generating response via Groq...")
    response = model_with_tools.invoke(messages)

    return {
        "messages": [response],
        "reply": response.content if response.content else "Processing tool...",
    }


def add_memory_node(state: AgentState) -> AgentState:
    user_id = state["user_id"]
    user_content = next(
        m.content for m in reversed(state["messages"]) if isinstance(m, HumanMessage)
    )
    ai_reply = state["reply"]

    print("Storing conversation turn into Mem0...")

    message_to_store = [
        {"role": "user", "content": user_content},
        {"role": "assistant", "content": ai_reply},
    ]

    try:
        mem0_client.add(message_to_store, user_id=user_id)
        return state
    except Exception as e:
        print(f"Error storing memory: {e}")

    return state


builder = StateGraph(AgentState)

builder.add_node("retrieve_memory", retrieve_memory_node)
builder.add_node("call_llm", call_llm_node)
builder.add_node("tools", ToolNode([create_reminder, get_reminders]))
builder.add_node("add_memory", add_memory_node)

builder.add_edge(START, "retrieve_memory")
builder.add_edge("retrieve_memory", "call_llm")
builder.add_conditional_edges(
    "call_llm", tools_condition, {"tools": "tools", END: "add_memory"}
)
builder.add_edge("tools", "call_llm")
builder.add_edge("add_memory", END)

graph = builder.compile()


HISTORY_LIMIT = 6


def get_recent_history(user_id):
    recent = list(
        ChatMessage.objects.filter(user_id=user_id).order_by("-created_at")[
            :HISTORY_LIMIT
        ]
    )
    recent.reverse()
    history = []
    for m in recent:
        history.append(HumanMessage(content=m.user_message))
        history.append(AIMessage(content=m.ai_response))
    return history


def run_companion_agent(user_message: str, user_id: int) -> str:
    initial_state = {
        "user_id": str(user_id),
        "messages": get_recent_history(user_id) + [HumanMessage(content=user_message)],
        "context": "",
        "reply": "",
    }

    config = {"configurable": {"user_id": user_id}}

    result = graph.invoke(initial_state, config=config)
    return result["reply"]
