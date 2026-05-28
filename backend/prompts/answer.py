def generate_context_grounded_answer_prompt(
    query: str,
    retrieved_context_text: str,
) -> str:
    return f"""
You are a context-grounded question answering system.

Answer the user query using ONLY the provided retrieved context.

RULES:

1. Use ONLY information explicitly present in the retrieved context.
2. Do NOT use external knowledge.
3. Do NOT infer, assume, or speculate.
4. If the answer is not fully supported by the context, say:
   "I could not find the answer in the provided context."
5. Keep the answer precise, complete, and grounded.
6. Do NOT mention phrases like "According to the context" or "The document says".
7. Preserve structure, lists, tables, and formatting whenever relevant.
8. Return plain natural language only — no JSON, no extra explanation.

QUERY:
{query}

RETRIEVED CONTEXT:
{retrieved_context_text}

ANSWER:
"""
