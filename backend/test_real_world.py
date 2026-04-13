"""
Real-world test scenarios for SecondBrain
Tests correction detection, temporal parsing, and full pipeline
"""
import asyncio
import requests
from datetime import datetime

BASE_URL = "http://localhost:8000"

def test_correction_scenario():
    """Test speech correction: 'let's meet tomorrow... no no day after tomorrow'"""
    print("\n" + "="*60)
    print("TEST 1: Speech Correction Detection")
    print("="*60)
    
    # Simulate the extraction pipeline
    from app.pipeline.extraction_pipeline import extraction_pipeline
    
    test_text = "let's meet tomorrow... no no day after tomorrow"
    
    async def run_test():
        result = await extraction_pipeline.extract(test_text)
        print(f"Input: {test_text}")
        print(f"Has Correction: {result['has_correction']}")
        print(f"Cleaned Text: {result['cleaned_text']}")
        print(f"Intent: {result['intent']}")
        print(f"Entities: {result['entities']}")
        print(f"Expected: Meeting scheduled for day after tomorrow")
        print("✅ Test passed" if result['has_correction'] else "❌ Test failed")
    
    asyncio.run(run_test())

def test_temporal_parsing():
    """Test temporal parsing of relative dates"""
    print("\n" + "="*60)
    print("TEST 2: Temporal Parsing")
    print("="*60)
    
    from app.pipeline.extraction_pipeline import extraction_pipeline
    
    test_cases = [
        "meet tomorrow",
        "deadline in 3 days",
        "task next Monday",
        "reminder day after tomorrow"
    ]
    
    async def run_tests():
        for text in test_cases:
            result = await extraction_pipeline.extract(text)
            print(f"\nInput: {text}")
            print(f"Dates: {result['entities'].get('dates', [])}")
            print(f"Intent: {result['intent']}")
    
    asyncio.run(run_tests())

def test_intent_detection():
    """Test intent classification"""
    print("\n" + "="*60)
    print("TEST 3: Intent Detection")
    print("="*60)
    
    from app.pipeline.extraction_pipeline import extraction_pipeline
    
    test_cases = [
        ("we need to meet next week", "meeting"),
        ("deadline is tomorrow", "deadline"),
        ("I have a task to complete", "task"),
        ("remind me to call John", "reminder"),
        ("I promise to finish it", "commitment"),
        ("just a general note", "general")
    ]
    
    async def run_tests():
        for text, expected_intent in test_cases:
            result = await extraction_pipeline.extract(text)
            detected_intent = result['intent']
            status = "✅" if detected_intent == expected_intent else "❌"
            print(f"{status} '{text}' -> Expected: {expected_intent}, Got: {detected_intent}")
    
    asyncio.run(run_tests())

def test_data_validation():
    """Test noise filtering and duplicate detection"""
    print("\n" + "="*60)
    print("TEST 4: Data Validation")
    print("="*60)
    
    from app.pipeline.data_validator import data_validator
    
    test_cases = [
        ("", "invalid_length"),
        ("um uh ah", "noise"),
        ("test", "invalid_length"),
        ("This is a valid memory with enough content to pass validation", "valid")
    ]
    
    async def run_tests():
        for text, expected_reason in test_cases:
            result = await data_validator.validate_memory(text)
            status = "✅" if result['reason'] == expected_reason else "❌"
            print(f"{status} '{text}' -> Expected: {expected_reason}, Got: {result['reason']}")
    
    asyncio.run(run_tests())

def test_session_types():
    """Test different recording session types"""
    print("\n" + "="*60)
    print("TEST 5: Recording Session Types")
    print("="*60)
    
    from app.models.memory import RecordingSession
    
    session_types = ["manual", "lecture", "meeting", "general", "short"]
    
    for session_type in session_types:
        session = RecordingSession(
            session_type=session_type,
            duration=10
        )
        print(f"✅ Session type '{session_type}' created successfully")

def test_memory_lifecycle():
    """Test memory lifecycle stages"""
    print("\n" + "="*60)
    print("TEST 6: Memory Lifecycle")
    print("="*60)
    
    from app.models.memory import Memory
    
    stages = ["short_term", "long_term", "archived"]
    
    for stage in stages:
        memory = Memory(
            text="Test memory",
            summary="Test summary",
            user_id="test_user",
            lifecycle_stage=stage
        )
        print(f"✅ Memory in '{stage}' stage created successfully")

def test_full_pipeline_integration():
    """Test full pipeline from text to memory"""
    print("\n" + "="*60)
    print("TEST 7: Full Pipeline Integration")
    print("="*60)
    
    from app.pipeline.extraction_pipeline import extraction_pipeline
    
    test_text = "I need to meet with John next Monday at 3pm to discuss the project deadline"
    
    async def run_test():
        result = await extraction_pipeline.extract(test_text)
        
        print(f"Input: {test_text}")
        print(f"\nExtraction Results:")
        print(f"  Cleaned Text: {result['cleaned_text']}")
        print(f"  Intent: {result['intent']}")
        print(f"  Summary: {result['summary']}")
        print(f"  Entities: {result['entities']}")
        print(f"  Importance Boost: {result['importance_boost']}")
        
        # Validate expected results
        assert result['intent'] in ['meeting', 'task', 'deadline'], "Intent detection failed"
        assert len(result['cleaned_text']) > 0, "Text cleaning failed"
        assert result['importance_boost'] > 0, "Importance calculation failed"
        
        print("\n✅ Full pipeline integration test passed")
    
    asyncio.run(run_test())

def main():
    """Run all test scenarios"""
    print("\n" + "="*60)
    print("SecondBrain Real-World Test Suite")
    print("="*60)
    
    try:
        test_correction_scenario()
        test_temporal_parsing()
        test_intent_detection()
        test_data_validation()
        test_session_types()
        test_memory_lifecycle()
        test_full_pipeline_integration()
        
        print("\n" + "="*60)
        print("All tests completed!")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ Test suite failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
