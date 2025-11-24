"""
Pytest configuration and fixtures
"""
import os
import pytest
import tempfile
import uuid
from pathlib import Path

# Set test environment variables
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("DATABASE_URL", "postgresql://localhost/omnidoc_test")
os.environ.setdefault("ALLOWED_ORIGINS", "http://localhost:3000")


@pytest.fixture(scope="session")
def test_client():
    """Create a test client for the FastAPI app"""
    from fastapi.testclient import TestClient
    from src.web.app import app
    return TestClient(app)


@pytest.fixture
def temp_dir(tmp_path):
    """Create a temporary directory for tests"""
    return tmp_path


@pytest.fixture
def temp_db(tmp_path):
    """Create a temporary database path for tests"""
    # For PostgreSQL, we'll use a test database URL
    # In tests, we can use an in-memory database or mock
    return str(tmp_path / "test.db")


@pytest.fixture
def test_project_id():
    """Generate a unique test project ID"""
    return f"test_project_{uuid.uuid4().hex[:8]}"


@pytest.fixture
def context_manager():
    """Create a ContextManager instance for testing"""
    from src.context.context_manager import ContextManager
    # Use test database URL from environment
    db_url = os.getenv("DATABASE_URL", "postgresql://localhost/omnidoc_test")
    try:
        cm = ContextManager(db_url=db_url)
        # Test connection by trying to get a connection
        try:
            conn = cm._get_connection()
            cm._put_connection(conn)
        except Exception as e:
            # Database not available - skip tests that need it
            pytest.skip(f"Database not available: {e}")
        yield cm
    except Exception as e:
        # If database is not available, skip the test
        pytest.skip(f"Database not available: {e}")


@pytest.fixture
def rate_limiter():
    """Create a RequestQueue instance for testing"""
    from src.rate_limit.queue_manager import RequestQueue
    # Use high limits for testing to avoid rate limiting during tests
    return RequestQueue(max_rate=1000, period=60, safety_margin=0.9)


@pytest.fixture
def api_key_available():
    """Check if API key is available for testing"""
    gemini_key = os.getenv("GEMINI_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")
    return {
        "any": bool(gemini_key or openai_key),
        "gemini": bool(gemini_key),
        "openai": bool(openai_key),
        "gemini_key": gemini_key,
        "openai_key": openai_key,
    }


@pytest.fixture
def mock_llm_provider():
    """Create a mock LLM provider for testing"""
    from unittest.mock import Mock, AsyncMock
    provider = Mock()
    provider.generate_text = Mock(return_value="# Test Document\n\nThis is test content.")
    provider.generate_async = AsyncMock(return_value="# Test Document\n\nThis is test content.")
    provider.async_generate_text = AsyncMock(return_value="# Test Document\n\nThis is test content.")
    return provider


@pytest.fixture
def file_manager(temp_dir):
    """Create a FileManager instance for testing"""
    from src.utils.file_manager import FileManager
    return FileManager(base_dir=str(temp_dir))
