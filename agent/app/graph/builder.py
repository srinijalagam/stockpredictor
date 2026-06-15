"""Assemble the LangGraph workflow."""
from __future__ import annotations

from functools import lru_cache

from langgraph.graph import END, START, StateGraph

from .nodes import company_node, predict_node, resolve_node, web_node, yahoo_node
from .state import AgentState


def build_graph():
    g = StateGraph(AgentState)

    g.add_node("resolve", resolve_node)
    g.add_node("market", yahoo_node)
    g.add_node("news", web_node)
    g.add_node("filings", company_node)
    g.add_node("predict", predict_node)

    g.add_edge(START, "resolve")
    g.add_edge("resolve", "market")
    # Fan out gathering after we know the ticker + website.
    g.add_edge("market", "news")
    g.add_edge("market", "filings")
    # Converge on prediction once both gathering branches complete.
    g.add_edge("news", "predict")
    g.add_edge("filings", "predict")
    g.add_edge("predict", END)

    return g.compile()


@lru_cache
def get_graph():
    return build_graph()
