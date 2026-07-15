"""
LangGraph nodes: retrieve -> answer -> verify -> (pass / escalate).

- retrieve: pulls top-k relevant chunks for the query
- answer: generates a grounded answer, matching the input language
- verify: scores groundedness/confidence of the answer against retrieved chunks
- escalate: routes low-confidence answers to a "needs human review" flag
"""


def retrieve_node(state: dict) -> dict:
    raise NotImplementedError


def answer_node(state: dict) -> dict:
    raise NotImplementedError


def verify_node(state: dict) -> dict:
    raise NotImplementedError
