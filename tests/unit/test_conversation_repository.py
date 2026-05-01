from interview_ai.repositories.conversation_repository import ConversationRepository


def test_conversation_repository_roundtrip(tmp_path) -> None:
    db_path = tmp_path / "chat.db"
    repo = ConversationRepository(str(db_path))

    repo.append_message("session-1", "user", "Hello")
    repo.append_message("session-1", "assistant", "Hi there")
    repo.append_message("session-2", "user", "Other")

    messages = repo.fetch_recent_messages("session-1")
    assert messages == [("user", "Hello"), ("assistant", "Hi there")]
