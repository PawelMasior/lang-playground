import json
import os
import sys
from pathlib import Path

import httpx
from langsmith import Client

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from evaluations.metrics.keyword_recall import keyword_recall  # noqa: E402

DATASET_FILE = Path("evaluations/datasets/interview_eval.jsonl")
API_URL = os.getenv("EVAL_API_URL", "http://127.0.0.1:8000/v1/interview/run")


def load_cases() -> list[dict]:
    cases: list[dict] = []
    with DATASET_FILE.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            cases.append(json.loads(line))
    return cases


def maybe_push_to_langsmith(cases: list[dict], results: list[dict]) -> None:
    api_key = os.getenv("LANGSMITH_API_KEY")
    if not api_key:
        print("LANGSMITH_API_KEY not set; skipping upload.")
        return

    project = os.getenv("LANGSMITH_PROJECT", "interview-ai-prep")
    client = Client(api_key=api_key)

    for case, result in zip(cases, results, strict=False):
        client.create_feedback(
            run_id=None,
            key="keyword_recall",
            score=result["keyword_recall"],
            comment=f"prompt={case['prompt'][:80]}",
            source_info={"project": project, "local_eval": True},
        )

    print("Uploaded evaluation feedback to LangSmith.")


def main() -> None:
    cases = load_cases()
    results: list[dict] = []

    with httpx.Client(timeout=30.0) as client:
        for idx, case in enumerate(cases, start=1):
            payload = {
                "role": case["role"],
                "experience_years": case["experience_years"],
                "topic_focus": case["topic_focus"],
                "user_message": case["prompt"],
            }
            response = client.post(API_URL, json=payload)
            response.raise_for_status()
            body = response.json()

            recall = keyword_recall(body["answer"], case["expected_keywords"])
            results.append({"index": idx, "keyword_recall": recall, "answer": body["answer"]})
            print(f"Case {idx} keyword_recall={recall:.2f}")

    avg = sum(item["keyword_recall"] for item in results) / max(len(results), 1)
    print(f"Average keyword_recall={avg:.2f}")

    maybe_push_to_langsmith(cases, results)


if __name__ == "__main__":
    main()
