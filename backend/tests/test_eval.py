import io
import uuid
from unittest.mock import AsyncMock, patch
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.services.eval.eval_parser import parse_and_validate_eval_csv
from app.services.eval.eval_engine import evaluate_rag_triplet


def test_csv_parser_validation():
    # Valid CSV
    valid_csv = b"question,ground_truth\nWhat is Python?,A programming language\nWhat is FastAPI?,A web framework\n"
    items = parse_and_validate_eval_csv(valid_csv)
    assert len(items) == 2
    assert items[0]["question"] == "What is Python?"

    # Invalid CSV missing ground_truth column
    invalid_csv = b"question,invalid_column\nWhat is Python?,A programming language\n"
    with pytest.raises(Exception) as exc_info:
        parse_and_validate_eval_csv(invalid_csv)
    assert "must contain 'question' and 'ground_truth'" in str(exc_info.value)


def test_eval_triplet_metrics():
    context = [{"content": "Python is a high-level programming language created by Guido van Rossum.", "source": "py.txt"}]
    metrics = evaluate_rag_triplet(
        question="What is Python?",
        ground_truth="Python is a programming language.",
        generated_answer="Python is a programming language.",
        context_chunks=context
    )

    assert "faithfulness" in metrics
    assert "answer_relevancy" in metrics
    assert "context_recall" in metrics
    assert "context_precision" in metrics
    assert metrics["faithfulness"] > 0.0
    assert metrics["answer_relevancy"] > 0.0


@pytest.mark.asyncio
async def test_eval_api_endpoints():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Register user
        user_email = f"eval_user_{uuid.uuid4().hex[:6]}@example.com"
        reg_res = await ac.post("/api/v1/auth/register", json={"email": user_email, "password": "password123"})
        token = reg_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Create chatbot
        cb_res = await ac.post("/api/v1/chatbots", headers=headers, json={"name": "Eval Test Bot"})
        cb_id = cb_res.json()["id"]

        # Upload evaluation CSV
        csv_bytes = b"question,ground_truth\nWhat is Python?,A programming language\nWhat is FastAPI?,A web framework\n"
        files = {"file": ("test_set.csv", io.BytesIO(csv_bytes), "text/csv")}

        mock_llm = AsyncMock()
        mock_llm.complete.return_value = "Python is a programming language."

        with patch("app.api.routes.chat.get_llm_provider", return_value=mock_llm):
            upload_res = await ac.post(f"/api/v1/chatbots/{cb_id}/eval", headers=headers, files=files)
            assert upload_res.status_code == 201
            eval_run_data = upload_res.json()
            run_id = eval_run_data["id"]

            # List eval runs
            list_res = await ac.get(f"/api/v1/chatbots/{cb_id}/eval", headers=headers)
            assert list_res.status_code == 200
            assert any(r["id"] == run_id for r in list_res.json())

            # Get eval run detail summary
            detail_res = await ac.get(f"/api/v1/chatbots/{cb_id}/eval/{run_id}", headers=headers)
            assert detail_res.status_code == 200
            detail = detail_res.json()
            assert detail["id"] == run_id
            assert "results" in detail
