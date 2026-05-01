from langchain_core.prompts import ChatPromptTemplate

PLANNER_PROMPT = ChatPromptTemplate.from_template(
    """
You are an interview prep planner.
Role: {role}
Experience: {experience_years} years
Topics: {topic_focus}
User message: {user_message}
Retrieved context:\n{context}

Create a concise interview strategy in 4-6 bullet points.
""".strip()
)

ANSWER_PROMPT = ChatPromptTemplate.from_template(
    """
You are an expert interview coach.
Role: {role}
Experience: {experience_years} years
Topics: {topic_focus}
User message: {user_message}
Plan:\n{plan}
Retrieved context:\n{context}

Return:
1) A polished answer the candidate can speak.
2) 3 follow-up questions interviewer may ask.
3) 3 practical exercises.

Format exactly:
ANSWER:\n...
FOLLOW_UP:\n- ...
- ...
- ...
EXERCISES:\n- ...
- ...
- ...
""".strip()
)
