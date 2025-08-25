from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_ollama import ChatOllama
from langchain_core.messages import BaseMessage


class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], "Chat history"]


llm = ChatOllama(model="MrSplatchy/Cookama")


def call_model(state: AgentState) -> AgentState:
    response = llm.invoke(state["messages"])
    return {"messages": state["messages"] + [response]}


# Graph
graph = StateGraph(AgentState)
graph.add_node("chat", call_model)
graph.set_entry_point("chat")
graph.add_edge("chat", "chat")

memory = MemorySaver()
app_graph = graph.compile(checkpointer=memory)

# Thats crazy how easier it is to look at compared with the code from 6-9 nmonths ago.