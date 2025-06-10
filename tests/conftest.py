"""
Test fixtures and configuration for paperless-ngx correspondent manager tests.
"""

from unittest.mock import Mock

import pytest

from paperless_ngx_correspondent_manager.manager import PaperlessCorrespondentManager


@pytest.fixture
def mock_session():
    """Mock requests session for testing."""
    session = Mock()
    session.get = Mock()
    session.post = Mock()
    session.put = Mock()
    session.delete = Mock()
    return session


@pytest.fixture
def sample_correspondents():
    """Sample correspondent data for testing."""
    return [
        {
            "id": 1,
            "slug": "john-doe",
            "name": "John Doe",
            "match": "john",
            "matching_algorithm": 1,
            "is_insensitive": True,
            "document_count": 5,
            "last_correspondence": "2025-06-10",
            "owner": 1,
            "permissions": {
                "view": {"users": [1], "groups": []},
                "change": {"users": [1], "groups": []},
            },
            "user_can_change": True,
        },
        {
            "id": 2,
            "slug": "jane-smith",
            "name": "Jane Smith",
            "match": "jane",
            "matching_algorithm": 1,
            "is_insensitive": True,
            "document_count": 3,
            "last_correspondence": "2025-06-09",
            "owner": 1,
            "permissions": {
                "view": {"users": [1], "groups": []},
                "change": {"users": [1], "groups": []},
            },
            "user_can_change": True,
        },
        {
            "id": 3,
            "slug": "john-d-doe",
            "name": "John D. Doe",
            "match": "john",
            "matching_algorithm": 1,
            "is_insensitive": True,
            "document_count": 2,
            "last_correspondence": "2025-06-08",
            "owner": 1,
            "permissions": {
                "view": {"users": [1], "groups": []},
                "change": {"users": [1], "groups": []},
            },
            "user_can_change": True,
        },
        {
            "id": 4,
            "slug": "empty-correspondent",
            "name": "Empty Correspondent",
            "match": "",
            "matching_algorithm": 1,
            "is_insensitive": True,
            "document_count": 0,
            "last_correspondence": None,
            "owner": 1,
            "permissions": {
                "view": {"users": [1], "groups": []},
                "change": {"users": [1], "groups": []},
            },
            "user_can_change": True,
        },
        {
            "id": 5,
            "slug": "john-doe-duplicate",
            "name": "JOHN DOE",
            "match": "john",
            "matching_algorithm": 1,
            "is_insensitive": True,
            "document_count": 1,
            "last_correspondence": "2025-06-07",
            "owner": 1,
            "permissions": {
                "view": {"users": [1], "groups": []},
                "change": {"users": [1], "groups": []},
            },
            "user_can_change": True,
        },
    ]


@pytest.fixture
def sample_documents():
    """Sample document data for testing."""
    return [
        {
            "id": 101,
            "correspondent": 1,
            "document_type": 1,
            "storage_path": 1,
            "title": "Invoice from John Doe",
            "content": "Invoice content here",
            "tags": [1, 2],
            "created": "2025-06-10",
            "modified": "2025-06-10T19:51:28.693Z",
            "added": "2025-06-10T19:51:28.693Z",
            "deleted_at": None,
            "archive_serial_number": 1001,
            "original_file_name": "invoice_john_doe.pdf",
            "archived_file_name": "1001_invoice_john_doe.pdf",
            "owner": 1,
            "permissions": {
                "view": {"users": [1], "groups": []},
                "change": {"users": [1], "groups": []},
            },
            "user_can_change": True,
            "is_shared_by_requester": False,
            "notes": [],
            "custom_fields": [],
            "page_count": 2,
            "mime_type": "application/pdf",
        },
        {
            "id": 102,
            "correspondent": 2,
            "document_type": 2,
            "storage_path": 1,
            "title": "Letter from Jane Smith",
            "content": "Letter content here",
            "tags": [1],
            "created": "2025-06-09",
            "modified": "2025-06-09T14:20:00Z",
            "added": "2025-06-09T14:20:00Z",
            "deleted_at": None,
            "archive_serial_number": 1002,
            "original_file_name": "letter_jane_smith.pdf",
            "archived_file_name": "1002_letter_jane_smith.pdf",
            "owner": 1,
            "permissions": {
                "view": {"users": [1], "groups": []},
                "change": {"users": [1], "groups": []},
            },
            "user_can_change": True,
            "is_shared_by_requester": False,
            "notes": [
                {
                    "id": 1,
                    "note": "Important letter",
                    "created": "2025-06-09T15:00:00.000Z",
                    "user": {
                        "id": 1,
                        "username": "testuser",
                        "first_name": "Test",
                        "last_name": "User",
                    },
                }
            ],
            "custom_fields": [{"value": "urgent", "field": 1}],
            "page_count": 1,
            "mime_type": "application/pdf",
        },
        {
            "id": 103,
            "correspondent": None,
            "document_type": 1,
            "storage_path": 1,
            "title": "Document without correspondent",
            "content": "General document content",
            "tags": [],
            "created": "2025-06-08",
            "modified": "2025-06-08T09:15:00Z",
            "added": "2025-06-08T09:15:00Z",
            "deleted_at": None,
            "archive_serial_number": 1003,
            "original_file_name": "general_doc.pdf",
            "archived_file_name": "1003_general_doc.pdf",
            "owner": 1,
            "permissions": {
                "view": {"users": [1], "groups": []},
                "change": {"users": [1], "groups": []},
            },
            "user_can_change": True,
            "is_shared_by_requester": False,
            "notes": [],
            "custom_fields": [],
            "page_count": 3,
            "mime_type": "application/pdf",
        },
    ]


@pytest.fixture
def manager_instance(mock_session):
    """Create a PaperlessCorrespondentManager instance with mocked session."""
    manager = PaperlessCorrespondentManager("http://localhost:8000", "test-token")
    manager.session = mock_session
    return manager


@pytest.fixture
def api_response_template():
    """Template for API response structure."""
    return {"count": 0, "next": None, "previous": None, "results": []}


@pytest.fixture
def correspondents_api_response(sample_correspondents):
    """Mock API response for correspondents endpoint."""
    return {
        "count": len(sample_correspondents),
        "next": None,
        "previous": None,
        "results": sample_correspondents,
        "all": [c["id"] for c in sample_correspondents],
    }


@pytest.fixture
def documents_api_response(sample_documents):
    """Mock API response for documents endpoint."""
    return {
        "count": len(sample_documents),
        "next": None,
        "previous": None,
        "results": sample_documents,
        "all": [d["id"] for d in sample_documents],
    }


@pytest.fixture
def empty_api_response():
    """Mock empty API response."""
    return {"count": 0, "next": None, "previous": None, "results": [], "all": []}


@pytest.fixture
def paginated_correspondents_response(sample_correspondents):
    """Mock paginated API response for correspondents."""
    return {
        "count": 123,
        "next": "http://api.example.org/correspondents/?page=2",
        "previous": None,
        "results": sample_correspondents[:3],  # First page with 3 items
        "all": list(range(1, 124)),  # All IDs 1-123
    }


@pytest.fixture
def cli_runner():
    """Click CLI test runner."""
    from click.testing import CliRunner

    return CliRunner()


@pytest.fixture
def mock_manager_with_data(mock_session, sample_correspondents, sample_documents):
    """Manager instance with pre-configured mock data and Mock() methods for CLI tests."""
    from paperless_ngx_correspondent_manager.manager import (
        PaperlessCorrespondentManager,
    )

    manager = PaperlessCorrespondentManager("http://localhost:8000", "test-token")
    manager.session = mock_session

    # Assign Mock() to all methods used in CLI tests
    manager.list_correspondents = Mock()
    manager.find_exact_duplicates = Mock()
    manager.find_similar_correspondents = Mock()
    manager.find_similar_correspondents_pairs = Mock()
    manager.print_empty_correspondents = Mock()
    manager.merge_correspondents = Mock()
    manager.merge_correspondent_group = Mock()
    manager.auto_merge_similar_correspondents = Mock()
    manager.delete_correspondent = Mock()
    manager.delete_empty_correspondents = Mock()
    manager.print_correspondent_diagnosis = Mock()
    manager.restore_documents_to_correspondent = Mock()
    manager.find_documents_by_date_range = Mock()

    # For get_correspondents and get_correspondent_documents, use real data
    manager.get_correspondents = Mock(return_value=sample_correspondents)
    manager.get_correspondent_documents = Mock(
        side_effect=lambda corr_id: [
            doc for doc in sample_documents if doc.get("correspondent") == corr_id
        ]
    )

    return manager


@pytest.fixture
def bulk_edit_response():
    """Mock response for bulk edit operations."""
    return {"success": True, "updated": 5}


@pytest.fixture
def correspondent_single_response():
    """Mock response for single correspondent GET/PUT/DELETE."""
    return {
        "id": 1,
        "slug": "john-doe",
        "name": "John Doe",
        "match": "john",
        "matching_algorithm": 1,
        "is_insensitive": True,
        "document_count": 5,
        "last_correspondence": "2025-06-10",
        "owner": 1,
        "permissions": {
            "view": {"users": [1], "groups": []},
            "change": {"users": [1], "groups": []},
        },
        "user_can_change": True,
    }


@pytest.fixture
def recent_documents():
    """Mock recent documents for date range queries."""
    return [
        {
            "id": 201,
            "title": "Recent Invoice",
            "correspondent": 1,
            "created": "2025-06-09",
            "modified": "2025-06-09T10:00:00Z",
        },
        {
            "id": 202,
            "title": "Recent Letter",
            "correspondent": 2,
            "created": "2025-06-08",
            "modified": "2025-06-08T15:30:00Z",
        },
    ]


# AIDEV-NOTE: Test data setup for comprehensive CLI testing
@pytest.fixture
def test_env_vars():
    """Environment variables for testing."""
    return {
        "PAPERLESS_URL": "http://localhost:8000",
        "PAPERLESS_TOKEN": "test-token-12345",
    }
