import csv
import io
from typing import Any
from fastapi import HTTPException, status


def parse_and_validate_eval_csv(file_bytes: bytes) -> list[dict[str, str]]:
    try:
        content_str = file_bytes.decode("utf-8")
    except UnicodeDecodeError:
        content_str = file_bytes.decode("latin-1")

    reader = csv.DictReader(io.StringIO(content_str))

    if not reader.fieldnames:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CSV file is empty or missing headers"
        )

    # Normalize column names to lowercase stripped strings
    field_mapping = {name: name.strip().lower() for name in reader.fieldnames if name}
    has_question = any(v == "question" for v in field_mapping.values())
    has_ground_truth = any(v in ["ground_truth", "groundtruth", "target", "reference"] for v in field_mapping.values())

    if not has_question or not has_ground_truth:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CSV must contain 'question' and 'ground_truth' columns"
        )

    eval_items = []
    for row in reader:
        # Resolve normalized values
        q_val = None
        gt_val = None
        for k, v in row.items():
            if not k:
                continue
            norm_k = k.strip().lower()
            if norm_k == "question":
                q_val = v.strip() if v else ""
            elif norm_k in ["ground_truth", "groundtruth", "target", "reference"]:
                gt_val = v.strip() if v else ""

        if q_val and gt_val:
            eval_items.append({"question": q_val, "ground_truth": gt_val})

    if not eval_items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CSV contains no valid non-empty question and ground_truth rows"
        )

    return eval_items
