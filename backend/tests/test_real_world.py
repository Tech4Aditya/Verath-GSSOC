import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# ── Speech correction detection ───────────────────────────────────────────────
@pytest.mark.parametrize("text,should_detect_correction", [
    ("let's meet tomorrow no no day after tomorrow", True),
    ("remind me at 3pm actually make that 4pm", True),
    ("meeting on Monday", False),
    ("submit report by Friday", False),
])
def test_correction_detection(text: str, should_detect_correction: bool):
    from app.pipeline.extraction_pipeline import detect_correction
    result = detect_correction(text)
    assert result == should_detect_correction, (
        f"Expected correction={should_detect_correction} for: '{text}'"
    )


# ── Temporal parsing ──────────────────────────────────────────────────────────
@pytest.mark.parametrize("phrase,expect_parsed", [
    ("tomorrow at 3pm", True),
    ("next Monday", True),
    ("in 3 days", True),
    ("day after tomorrow", True),
    ("sometime soon", False),   # too vague to parse
    ("", False),
])
def test_temporal_parsing(phrase: str, expect_parsed: bool):
    from app.pipeline.extraction_pipeline import parse_temporal_expression
    result = parse_temporal_expression(phrase)
    if expect_parsed:
        assert result is not None, f"Expected a parsed date for '{phrase}', got None"
    else:
        assert result is None, f"Expected None for '{phrase}', got {result}"


# ── Intent classification ─────────────────────────────────────────────────────
@pytest.mark.parametrize("text,expected_intent", [
    ("meeting with John at 3pm", "meeting"),
    ("submit the report by Friday", "deadline"),
    ("remind me to call Sarah", "reminder"),
    ("I need to finish the slides", "task"),
    ("had lunch with the team today", "general"),
])
def test_intent_classification(text: str, expected_intent: str):
    from app.pipeline.extraction_pipeline import classify_intent
    intent = classify_intent(text)
    assert intent == expected_intent, (
        f"Expected intent='{expected_intent}' for: '{text}', got '{intent}'"
    )


# ── Entity extraction ─────────────────────────────────────────────────────────
@pytest.mark.parametrize("text,expected_people", [
    ("Meeting with John and Sarah at 3pm", ["John", "Sarah"]),
    ("Call Dr. Smith tomorrow", ["Smith"]),
    ("submit the report", []),
])
def test_entity_extraction_people(text: str, expected_people: list):
    from app.pipeline.extraction_pipeline import extract_entities
    entities = extract_entities(text)
    extracted = entities.get("people", [])
    for person in expected_people:
        assert any(person in p for p in extracted), (
            f"Expected '{person}' in extracted people {extracted} for: '{text}'"
        )


# ── Data validation ───────────────────────────────────────────────────────────
@pytest.mark.parametrize("text,should_pass", [
    ("Meeting with John tomorrow", True),
    ("um ah", False),                  # too short / noise
    ("a" * 10001, False),              # too long
    ("<script>alert(1)</script>", False),  # XSS attempt
    ("   ", False),                    # whitespace only
])
def test_data_validation(text: str, should_pass: bool):
    from app.pipeline.data_validator import validate_text
    is_valid, _ = validate_text(text)
    assert is_valid == should_pass, (
        f"Expected valid={should_pass} for text: '{text[:60]}'"
    )


# ── Memory lifecycle promotion ────────────────────────────────────────────────
@pytest.mark.parametrize("importance,expected_lifecycle", [
    (0.9, "long_term"),
    (0.6, "long_term"),
    (0.59, "short_term"),
    (0.1, "short_term"),
])
@pytest.mark.asyncio
async def test_memory_lifecycle_promotion(importance: float, expected_lifecycle: str):
    from app.db.memory_lifecycle import determine_lifecycle
    result = determine_lifecycle(importance=importance)
    assert result == expected_lifecycle, (
        f"importance={importance} → expected '{expected_lifecycle}', got '{result}'"
    )


# ── Full pipeline integration ─────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_full_pipeline_meeting_with_people(monkeypatch):
    """End-to-end: text in → structured memory out, no external calls."""
    store_calls = []

    async def mock_store(user_id, text, metadata):
        store_calls.append({"user_id": user_id, "text": text, "metadata": metadata})
        return "mock_memory_id"

    monkeypatch.setattr("app.services.memory_store.store_memory", mock_store)
    monkeypatch.setattr(
        "app.services.embedding.get_embedding",
        lambda text: [0.1] * 768
    )
    monkeypatch.setattr(
        "app.pipeline.extraction_pipeline.summarize_with_llm",
        AsyncMock(return_value="Meeting with John and Sarah at 3pm")
    )

    from app.pipeline.extraction_pipeline import run_extraction_pipeline

    result = await run_extraction_pipeline(
        user_id="test_user",
        text="Meeting with John and Sarah at 3pm to discuss the project",
    )

    assert result["intent"] == "meeting"
    assert len(store_calls) == 1
    assert "John" in str(result["entities"].get("people", []))


@pytest.mark.asyncio
async def test_full_pipeline_speech_correction(monkeypatch):
    """Correction phrases should resolve to the corrected version."""
    monkeypatch.setattr("app.services.memory_store.store_memory", AsyncMock(return_value="id"))
    monkeypatch.setattr("app.services.embedding.get_embedding", lambda t: [0.1] * 768)
    monkeypatch.setattr(
        "app.pipeline.extraction_pipeline.summarize_with_llm",
        AsyncMock(return_value="Meeting day after tomorrow")
    )

    from app.pipeline.extraction_pipeline import run_extraction_pipeline

    result = await run_extraction_pipeline(
        user_id="test_user",
        text="let's meet tomorrow no no day after tomorrow",
    )

    assert result["has_correction"] is True
    assert "day after tomorrow" in result["cleaned_text"].lower()
