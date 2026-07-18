def build_prompt(
    chatbot_instructions: str,
    context_chunks: list[dict],
    user_query: str
) -> tuple[str, str]:
    base_system = (
        f"{chatbot_instructions}\n\n"
        "INSTRUCTIONS:\n"
        "Answer the user's question using ONLY the provided context snippets below.\n"
        "If the answer cannot be found or deduced from the context, state clearly: "
        "'I cannot answer this question based on the provided documents.'"
    )

    if not context_chunks:
        user_content = f"CONTEXT:\n[No relevant documents found]\n\nQUESTION:\n{user_query}"
        return base_system, user_content

    formatted_context = []
    for idx, chunk in enumerate(context_chunks, 1):
        source_name = chunk.get("source", "Document")
        formatted_context.append(f"[{idx}] Source: {source_name}\n{chunk.get('content', '')}")

    context_str = "\n\n".join(formatted_context)
    user_content = f"CONTEXT:\n{context_str}\n\nQUESTION:\n{user_query}"

    return base_system, user_content
