from typing import TypedDict

from django.conf import settings
from langchain_groq import ChatGroq
from langgraph.graph import END, START, StateGraph
from mem0 import MemoryClient

model = ChatGroq(
    model="openai/gpt-oss-20b",
    temperature=0.7,
    api_key=settings.GROQ_API_KEY,
)
mem0_client = MemoryClient(api_key=settings.MEM0_API_KEY)


class AgentState(TypedDict):
    user_id: str
    messages: list[str]
    context: str
    reply: str


def retrieve_memory_node(state: AgentState) -> AgentState:
    user_id = state["user_id"]
    latest_message = state["messages"][-1]

    print(f"Fetching memories for user: {user_id}")
    memories = mem0_client.search(query=latest_message, filters={"user_id": user_id})

    context_str = "\n".join([m.get("memory", "") for m in memories.get("results", [])])
    state["context"] = context_str
    return state


def call_llm_node(state: AgentState) -> AgentState:
    user_message = state["messages"][-1]
    context = state["context"]

    prompt = f"""
    Relevant background memory about the user:
    {context if context else "None"}

    User Message: {user_message}"""

    print("Generating response via Groq...")
    response = model.invoke(prompt)
    state["reply"] = response.content
    return state


def add_memory_node(state: AgentState) -> AgentState:
    user_id = state["user_id"]
    user_message = state["messages"][-1]
    ai_reply = state["reply"]

    print("Storing conversation turn into Mem0...")

    message_to_store = [
        {"role": "user", "content": user_message},
        {"role": "assistant", "content": ai_reply},
    ]

    mem0_client.add(message_to_store, user_id=user_id)
    return state


builder = StateGraph(AgentState)

builder.add_node("retrieve_memory", retrieve_memory_node)
builder.add_node("call_llm", call_llm_node)
builder.add_node("add_memory", add_memory_node)

builder.add_edge(START, "retrieve_memory")
builder.add_edge("retrieve_memory", "call_llm")
builder.add_edge("call_llm", "add_memory")
builder.add_edge("add_memory", END)

graph = builder.compile()


def run_companion_agent(user_message: str, user_id: int) -> str:
    initial_state = {
        "user_id": str(user_id),
        "messages": [user_message],
        "context": "",
        "reply": "",
    }

    result = graph.invoke(initial_state)
    return result["reply"]
