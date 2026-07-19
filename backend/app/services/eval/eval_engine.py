import re


def _clean_words(text: str) -> list[str]:
    words = []
    for w in text.split():
        cleaned = re.sub(r"[^\w]", "", w.lower())
        if len(cleaned) >= 3:
            words.append(cleaned)
    return words


def evaluate_rag_triplet(
    question: str,
    ground_truth: str,
    generated_answer: str,
    context_chunks: list[dict]
) -> dict[str, float]:
    """Calculate RAG evaluation metrics for a single question-answer-context triplet."""

    if not generated_answer or "cannot answer" in generated_answer.lower():
        return {
            "faithfulness": 0.0,
            "answer_relevancy": 0.0,
            "context_recall": 0.0,
            "context_precision": 0.0,
        }

    # 1. Faithfulness (Word overlap between generated answer and context chunks)
    context_text = " ".join(c.get("content", "") for c in context_chunks).lower()
    answer_words = _clean_words(generated_answer)
    if answer_words and context_text:
        faithfulness_score = min(1.0, sum(1 for w in answer_words if w in context_text) / len(answer_words))
    else:
        faithfulness_score = 0.5

    # 2. Answer Relevancy (Word overlap between question and generated answer)
    question_words = _clean_words(question)
    answer_text = generated_answer.lower()
    if question_words:
        relevancy_score = min(1.0, sum(1 for w in question_words if w in answer_text) / len(question_words))
    else:
        relevancy_score = 0.5

    # 3. Context Recall (Word overlap between ground_truth and context chunks)
    gt_words = _clean_words(ground_truth)
    if gt_words and context_text:
        recall_score = min(1.0, sum(1 for w in gt_words if w in context_text) / len(gt_words))
    else:
        recall_score = 0.5

    # 4. Context Precision (Proportion of context chunks with non-zero word overlap to ground truth)
    if context_chunks and gt_words:
        relevant_chunks = 0
        for chunk in context_chunks:
            c_text = chunk.get("content", "").lower()
            if any(w in c_text for w in gt_words):
                relevant_chunks += 1
        precision_score = relevant_chunks / len(context_chunks)
    else:
        precision_score = 0.5

    return {
        "faithfulness": round(faithfulness_score, 3),
        "answer_relevancy": round(relevancy_score, 3),
        "context_recall": round(recall_score, 3),
        "context_precision": round(precision_score, 3),
    }
