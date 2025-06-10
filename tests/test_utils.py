"""Test utilities and helper functions for paperless-ngx correspondent manager tests."""

from unittest.mock import Mock

import pytest


def create_mock_response(json_data, status_code=200, raise_for_status=None):
    """Create a mock response object for testing API calls."""
    response = Mock()
    response.json.return_value = json_data
    response.status_code = status_code

    if raise_for_status:
        response.raise_for_status.side_effect = raise_for_status
    else:
        response.raise_for_status.return_value = None

    return response


def create_test_correspondent(correspondent_id, name, document_count=0, **kwargs):
    """Create a test correspondent dictionary."""
    correspondent = {
        "id": correspondent_id,
        "name": name,
        "slug": name.lower().replace(" ", "-"),
        "match": name.split()[0].lower() if name else "",
        "matching_algorithm": 1,
        "is_insensitive": True,
        "document_count": document_count,
        "last_correspondence": "2024-01-01",
    }
    correspondent.update(kwargs)
    return correspondent


def create_test_document(
    document_id, correspondent_id=None, title="Test Document", **kwargs
):
    """Create a test document dictionary."""
    document = {
        "id": document_id,
        "title": title,
        "correspondent": correspondent_id,
        "document_type": 1,
        "storage_path": 1,
        "tags": [],
        "created": "2024-01-01T00:00:00Z",
        "modified": "2024-01-01T00:00:00Z",
        "added": "2024-01-01T00:00:00Z",
        "archive_serial_number": None,
        "original_file_name": f"{title}.pdf",
        "archived_file_name": f"{document_id:07d}.pdf",
    }
    document.update(kwargs)
    return document


def verify_cli_output_contains(result, expected_strings):
    """Verify that CLI output contains all expected strings."""
    for expected in expected_strings:
        assert expected in result.output, (
            f"Expected '{expected}' in output: {result.output}"
        )


def verify_cli_success(result):
    """Verify that CLI command executed successfully."""
    assert result.exit_code == 0, (
        f"Command failed with exit code {result.exit_code}. Output: {result.output}"
    )


def verify_cli_failure(result, expected_exit_code=1):
    """Verify that CLI command failed as expected."""
    assert result.exit_code == expected_exit_code, (
        f"Expected exit code {expected_exit_code}, got {result.exit_code}. Output: {result.output}"
    )


@pytest.fixture
def test_data_factory():
    """Pytest fixture providing access to test data factory."""

    class TestDataFactory:
        def __init__(self):
            self.correspondents = []
            self.documents = []

        def add_correspondents(self, correspondents):
            self.correspondents.extend(correspondents)

        def add_documents(self, documents):
            self.documents.extend(documents)

    return TestDataFactory()
