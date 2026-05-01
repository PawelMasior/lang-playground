.PHONY: install lint test run-api run-skills eval

install:
	pip install -e .[dev]

lint:
	ruff check .
	mypy apps/api/src apps/skill_server/src packages/shared/src

test:
	pytest

run-api:
	uvicorn interview_ai.main:app --reload --port 8000

run-skills:
	uvicorn skill_server.app:app --reload --port 8010

eval:
	python evaluations/run_eval.py
