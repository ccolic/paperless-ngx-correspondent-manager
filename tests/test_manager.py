"""
Unit tests for PaperlessCorrespondentManager class.
"""

import json
from unittest.mock import Mock, patch

import pytest
import requests

from paperless_ngx_correspondent_manager.manager import PaperlessCorrespondentManager


class TestPaperlessCorrespondentManagerInit:
    """Test initialization of PaperlessCorrespondentManager."""

    def test_init_with_valid_parameters(self):
        """Test initialization with valid parameters."""
        manager = PaperlessCorrespondentManager("http://localhost:8000", "test-token")

        assert manager.base_url == "http://localhost:8000"
        assert manager.token == "test-token"
        assert manager.session is not None
        assert manager.session.headers["Authorization"] == "Token test-token"
        assert manager.session.headers["Accept"] == "application/json; version=9"
        assert manager.session.headers["Content-Type"] == "application/json"

    def test_init_strips_trailing_slash_from_url(self):
        """Test that trailing slash is stripped from base URL."""
        manager = PaperlessCorrespondentManager("http://localhost:8000/", "test-token")
        assert manager.base_url == "http://localhost:8000"


class TestGetCorrespondents:
    """Test get_correspondents method."""

    def test_get_correspondents_success_single_page(
        self, manager_instance, correspondents_api_response
    ):
        """Test successful retrieval of correspondents from single page."""
        # AIDEV-NOTE: Mock single page response
        manager_instance.session.get.return_value.json.return_value = (
            correspondents_api_response
        )
        manager_instance.session.get.return_value.raise_for_status.return_value = None

        with patch("builtins.print") as mock_print:
            result = manager_instance.get_correspondents()

        assert len(result) == len(correspondents_api_response["results"])
        assert result == correspondents_api_response["results"]
        manager_instance.session.get.assert_called_once()
        mock_print.assert_called_once()

    def test_get_correspondents_success_multiple_pages(self, manager_instance):
        """Test successful retrieval of correspondents from multiple pages."""
        # AIDEV-NOTE: Mock paginated response
        page1_response = {
            "results": [{"id": 1, "name": "Test 1"}],
            "next": "http://localhost:8000/api/correspondents/?page=2",
            "previous": None,
        }
        page2_response = {
            "results": [{"id": 2, "name": "Test 2"}],
            "next": None,
            "previous": "http://localhost:8000/api/correspondents/?page=1",
        }

        manager_instance.session.get.side_effect = [
            Mock(json=Mock(return_value=page1_response), raise_for_status=Mock()),
            Mock(json=Mock(return_value=page2_response), raise_for_status=Mock()),
        ]

        with patch("builtins.print"):
            result = manager_instance.get_correspondents()

        assert len(result) == 2
        assert result[0]["id"] == 1
        assert result[1]["id"] == 2
        assert manager_instance.session.get.call_count == 2

    def test_get_correspondents_request_exception(self, manager_instance):
        """Test get_correspondents handles request exceptions."""
        manager_instance.session.get.side_effect = requests.exceptions.RequestException(
            "Network error"
        )

        with pytest.raises(SystemExit):
            with patch("builtins.print") as mock_print:
                manager_instance.get_correspondents()

        mock_print.assert_called_with("Error fetching correspondents: Network error")


class TestListCorrespondents:
    """Test list_correspondents method."""

    def test_list_correspondents_table_format(
        self, manager_instance, sample_correspondents
    ):
        """Test listing correspondents in table format."""
        with patch.object(
            manager_instance, "get_correspondents", return_value=sample_correspondents
        ):
            with patch("builtins.print") as mock_print:
                manager_instance.list_correspondents("table")

        # Check that print was called multiple times for table output
        assert mock_print.call_count > 5  # Header + correspondents + formatting

    def test_list_correspondents_json_format(
        self, manager_instance, sample_correspondents
    ):
        """Test listing correspondents in JSON format."""
        with patch.object(
            manager_instance, "get_correspondents", return_value=sample_correspondents
        ):
            with patch("builtins.print") as mock_print:
                manager_instance.list_correspondents("json")

        # Should call print once with JSON string
        mock_print.assert_called_once()
        call_args = mock_print.call_args[0][0]
        # Verify it's valid JSON
        parsed = json.loads(call_args)
        assert len(parsed) == len(sample_correspondents)

    def test_list_correspondents_yaml_format(
        self, manager_instance, sample_correspondents
    ):
        """Test listing correspondents in YAML format."""
        with patch.object(
            manager_instance, "get_correspondents", return_value=sample_correspondents
        ):
            with patch("builtins.print") as mock_print:
                manager_instance.list_correspondents("yaml")

        # Should call print once with YAML string
        mock_print.assert_called_once()
        call_args = mock_print.call_args[0][0]
        assert isinstance(call_args, str)
        assert "name:" in call_args  # Basic YAML structure check


class TestFindExactDuplicates:
    """Test find_exact_duplicates method."""

    def test_find_exact_duplicates_with_duplicates(self, manager_instance):
        """Test finding exact duplicates when they exist."""
        correspondents = [
            {"id": 1, "name": "John Doe"},
            {"id": 2, "name": "JOHN DOE"},  # Case insensitive duplicate
            {"id": 3, "name": "  john doe  "},  # Whitespace should be stripped
            {"id": 4, "name": "Jane Smith"},
        ]

        with patch.object(
            manager_instance, "get_correspondents", return_value=correspondents
        ):
            duplicates = manager_instance.find_exact_duplicates()

        assert len(duplicates) == 1
        assert len(duplicates[0]) == 3  # Three "John Doe" variants
        ids = [corr["id"] for corr in duplicates[0]]
        assert set(ids) == {1, 2, 3}

    def test_find_exact_duplicates_no_duplicates(self, manager_instance):
        """Test finding exact duplicates when none exist."""
        correspondents = [
            {"id": 1, "name": "John Doe"},
            {"id": 2, "name": "Jane Smith"},
            {"id": 3, "name": "Bob Johnson"},
        ]

        with patch.object(
            manager_instance, "get_correspondents", return_value=correspondents
        ):
            duplicates = manager_instance.find_exact_duplicates()

        assert len(duplicates) == 0


class TestCalculateSimilarity:
    """Test calculate_similarity method."""

    @pytest.mark.parametrize(
        "name1, name2, expected",
        [
            ("John Doe", "John Doe", 1.0),
            ("John Doe", "JOHN DOE", 1.0),
            ("  John Doe  ", "John Doe", 1.0),
            ("John Doe", "John D. Doe", 0.8),  # Should be high but not perfect
            ("John Doe", "Jane Smith", 0.0),  # Should be low
        ],
    )
    def test_calculate_similarity(
        self, manager_instance, name1: str, name2: str, expected: float
    ):
        """Test similarity calculation for various cases."""
        similarity = manager_instance.calculate_similarity(name1, name2)
        if expected == 1.0:
            assert similarity == pytest.approx(1.0)
        elif expected == 0.0:
            assert similarity < 0.5
        else:
            assert 0.8 < similarity < 1.0


class TestFindSimilarCorrespondents:
    """Test find_similar_correspondents method."""

    def test_find_similar_correspondents_with_groups(self, manager_instance):
        """Test finding similar correspondents that form groups."""
        correspondents = [
            {"id": 1, "name": "John Doe"},
            {"id": 2, "name": "John D. Doe"},
            {"id": 3, "name": "Jane Smith"},
            {"id": 4, "name": "Jane A. Smith"},
            {"id": 5, "name": "Bob Johnson"},
        ]

        with patch.object(
            manager_instance, "get_correspondents", return_value=correspondents
        ):
            similar_groups = manager_instance.find_similar_correspondents(threshold=0.8)

        # Should find groups for John Doe variants and Jane Smith variants
        assert len(similar_groups) == 2

        # Check that groups are properly formed
        for group in similar_groups:
            names = [corr["name"] for corr in group]
            assert len(group) >= 2
            if "John" in names[0]:
                assert all("John" in name for name in names)
            elif "Jane" in names[0]:
                assert all("Jane" in name for name in names)

    def test_find_similar_correspondents_no_groups(self, manager_instance):
        """Test finding similar correspondents when no groups exist."""
        correspondents = [
            {"id": 1, "name": "John Doe"},
            {"id": 2, "name": "Jane Smith"},
            {"id": 3, "name": "Bob Johnson"},
        ]

        with patch.object(
            manager_instance, "get_correspondents", return_value=correspondents
        ):
            similar_groups = manager_instance.find_similar_correspondents()

        assert len(similar_groups) == 0

    def test_find_similar_correspondents_custom_threshold(self, manager_instance):
        """Test finding similar correspondents with custom threshold."""
        correspondents = [
            {"id": 1, "name": "John Doe"},
            {"id": 2, "name": "John Smith"},  # Less similar
        ]

        with patch.object(
            manager_instance, "get_correspondents", return_value=correspondents
        ):
            # With high threshold, should find no groups
            similar_groups_high = manager_instance.find_similar_correspondents(
                threshold=0.9
            )
            assert len(similar_groups_high) == 0

            # With low threshold, should find a group
            similar_groups_low = manager_instance.find_similar_correspondents(
                threshold=0.3
            )
            assert len(similar_groups_low) == 1


class TestFindSimilarCorrespondentsPairs:
    """Test find_similar_correspondents_pairs method."""

    def test_find_similar_correspondents_pairs_with_matches(self, manager_instance):
        """Test finding similar correspondent pairs."""
        correspondents = [
            {"id": 1, "name": "John Doe"},
            {"id": 2, "name": "John D. Doe"},
            {"id": 3, "name": "Jane Smith"},
        ]

        with patch.object(
            manager_instance, "get_correspondents", return_value=correspondents
        ):
            pairs = manager_instance.find_similar_correspondents_pairs(threshold=0.8)

        assert len(pairs) >= 1
        # Should find John Doe and John D. Doe as similar
        pair = pairs[0]
        assert len(pair) == 3  # (corr1, corr2, similarity)
        assert pair[2] > 0.8  # Similarity score

    def test_find_similar_correspondents_pairs_sorted_by_similarity(
        self, manager_instance
    ):
        """Test that pairs are sorted by similarity score."""
        correspondents = [
            {"id": 1, "name": "John Doe"},
            {"id": 2, "name": "John D. Doe"},  # High similarity
            {"id": 3, "name": "John Smith"},  # Lower similarity
        ]

        with patch.object(
            manager_instance, "get_correspondents", return_value=correspondents
        ):
            pairs = manager_instance.find_similar_correspondents_pairs(threshold=0.3)

        # Pairs should be sorted by similarity (descending)
        if len(pairs) > 1:
            for i in range(len(pairs) - 1):
                assert pairs[i][2] >= pairs[i + 1][2]


class TestGetCorrespondentDocuments:
    """Test get_correspondent_documents method."""

    def test_get_correspondent_documents_success(
        self, manager_instance, sample_documents
    ):
        """Test successful retrieval of correspondent documents."""
        filtered_docs = [
            doc for doc in sample_documents if doc.get("correspondent") == 1
        ]
        api_response = {"results": filtered_docs, "next": None, "previous": None}

        manager_instance.session.get.return_value.json.return_value = api_response
        manager_instance.session.get.return_value.raise_for_status.return_value = None

        documents = manager_instance.get_correspondent_documents(1)

        assert len(documents) == len(filtered_docs)
        assert all(doc.get("correspondent") == 1 for doc in documents)
        manager_instance.session.get.assert_called_once()

    def test_get_correspondent_documents_request_exception(self, manager_instance):
        """Test get_correspondent_documents handles request exceptions."""
        manager_instance.session.get.side_effect = requests.exceptions.RequestException(
            "Network error"
        )

        with patch("builtins.print") as mock_print:
            documents = manager_instance.get_correspondent_documents(1)

        assert documents == []
        mock_print.assert_called_with(
            "Error fetching documents for correspondent 1: Network error"
        )


class TestMergeCorrespondents:
    """Test merge_correspondents method."""

    def test_merge_correspondents_success(self, manager_instance, sample_documents):
        """Test successful merge of correspondents."""
        # AIDEV-NOTE: This test patches both document retrieval and bulk reassignment to simulate a merge.
        source_docs = [doc for doc in sample_documents if doc.get("correspondent") == 2]

        with patch.object(
            manager_instance, "get_correspondent_documents", return_value=source_docs
        ):
            with patch.object(
                manager_instance, "bulk_reassign_documents", return_value=True
            ) as mock_bulk:
                with patch("builtins.print"):
                    result = manager_instance.merge_correspondents(2, 1)

        assert result is True
        mock_bulk.assert_called_once_with([doc["id"] for doc in source_docs], 1)

    def test_merge_correspondents_no_documents(self, manager_instance):
        """Test merge when source correspondent has no documents."""
        with patch.object(
            manager_instance, "get_correspondent_documents", return_value=[]
        ):
            with patch("builtins.print") as mock_print:
                result = manager_instance.merge_correspondents(2, 1)

        assert result is True
        mock_print.assert_called_with("No documents found for correspondent 2")

    def test_merge_correspondents_bulk_reassign_fails(
        self, manager_instance, sample_documents
    ):
        """Test merge when bulk reassign fails."""
        source_docs = [doc for doc in sample_documents if doc.get("correspondent") == 2]

        with patch.object(
            manager_instance, "get_correspondent_documents", return_value=source_docs
        ):
            with patch.object(
                manager_instance, "bulk_reassign_documents", return_value=False
            ):
                with patch("builtins.print"):
                    result = manager_instance.merge_correspondents(2, 1)

        assert result is False


class TestDeleteCorrespondent:
    """Test delete_correspondent method."""

    def test_delete_correspondent_success(self, manager_instance):
        """Test successful deletion of correspondent."""
        manager_instance.session.delete.return_value.raise_for_status.return_value = (
            None
        )

        with patch("builtins.print") as mock_print:
            result = manager_instance.delete_correspondent(1)

        assert result is True
        manager_instance.session.delete.assert_called_once()
        mock_print.assert_called_with("Successfully deleted correspondent 1")

    def test_delete_correspondent_request_exception(self, manager_instance):
        """Test delete_correspondent handles request exceptions."""
        manager_instance.session.delete.side_effect = (
            requests.exceptions.RequestException("Delete error")
        )

        with patch("builtins.print") as mock_print:
            result = manager_instance.delete_correspondent(1)

        assert result is False
        mock_print.assert_called_with("Error deleting correspondent 1: Delete error")


class TestFindEmptyCorrespondents:
    """Test find_empty_correspondents method."""

    def test_find_empty_correspondents_with_empty(
        self, manager_instance, sample_correspondents
    ):
        """Test finding empty correspondents when they exist."""
        with patch.object(
            manager_instance, "get_correspondents", return_value=sample_correspondents
        ):
            empty_correspondents = manager_instance.find_empty_correspondents()

        # Should find correspondent with document_count == 0
        assert len(empty_correspondents) == 1
        assert empty_correspondents[0]["document_count"] == 0
        assert empty_correspondents[0]["name"] == "Empty Correspondent"

    def test_find_empty_correspondents_none_empty(self, manager_instance):
        """Test finding empty correspondents when none exist."""
        correspondents = [
            {"id": 1, "name": "John Doe", "document_count": 5},
            {"id": 2, "name": "Jane Smith", "document_count": 3},
        ]

        with patch.object(
            manager_instance, "get_correspondents", return_value=correspondents
        ):
            empty_correspondents = manager_instance.find_empty_correspondents()

        assert len(empty_correspondents) == 0


class TestBulkReassignDocuments:
    """Test bulk_reassign_documents method."""

    def test_bulk_reassign_documents_success_single_batch(self, manager_instance):
        """Test successful bulk reassignment in single batch."""
        document_ids = [101, 102, 103]

        manager_instance.session.post.return_value.raise_for_status.return_value = None

        with patch("builtins.print"):
            result = manager_instance.bulk_reassign_documents(document_ids, 1)

        assert result is True
        manager_instance.session.post.assert_called_once()

    def test_bulk_reassign_documents_success_multiple_batches(self, manager_instance):
        """Test successful bulk reassignment in multiple batches."""
        document_ids = list(
            range(1, 101)
        )  # 100 documents, should create 2 batches of 50

        manager_instance.session.post.return_value.raise_for_status.return_value = None

        with patch("builtins.print"):
            result = manager_instance.bulk_reassign_documents(document_ids, 1)

        assert result is True
        assert manager_instance.session.post.call_count == 2

    def test_bulk_reassign_documents_empty_list(self, manager_instance):
        """Test bulk reassignment with empty document list."""
        with patch("builtins.print") as mock_print:
            result = manager_instance.bulk_reassign_documents([], 1)

        assert result is True
        mock_print.assert_called_with("No documents to reassign.")

    def test_bulk_reassign_documents_timeout_retry(self, manager_instance):
        """Test bulk reassignment handles timeout and retries with smaller batches."""
        # AIDEV-NOTE: This test simulates a timeout on the first call and success on retry (recursive call).
        document_ids = list(range(1, 51))  # 50 documents

        def mock_post_side_effect(*args, **kwargs):
            if mock_post_side_effect.call_count == 1:
                mock_post_side_effect.call_count += 1
                raise requests.exceptions.Timeout("Timeout")
            else:
                response = Mock()
                response.raise_for_status.return_value = None
                return response

        mock_post_side_effect.call_count = 1
        manager_instance.session.post.side_effect = mock_post_side_effect

        with patch("builtins.print"):
            manager_instance.bulk_reassign_documents(document_ids, 1, batch_size=50)

        # Should handle timeout and attempt retry (implementation may vary)
        assert manager_instance.session.post.call_count >= 2

    def test_bulk_reassign_documents_request_exception(self, manager_instance):
        """Test bulk reassignment handles request exceptions."""
        document_ids = [101, 102, 103]

        manager_instance.session.post.side_effect = (
            requests.exceptions.RequestException("Network error")
        )

        with patch("builtins.print"):
            result = manager_instance.bulk_reassign_documents(document_ids, 1)

        assert result is False


class TestDeleteEmptyCorrespondents:
    """Test delete_empty_correspondents method."""

    def test_delete_empty_correspondents_none_found(self, manager_instance):
        """Test deleting empty correspondents when none exist."""
        with patch.object(
            manager_instance, "find_empty_correspondents", return_value=[]
        ):
            with patch("builtins.print") as mock_print:
                result = manager_instance.delete_empty_correspondents()

        assert result == 0
        mock_print.assert_called_with("No empty correspondents found to delete.")

    def test_delete_empty_correspondents_with_confirmation(self, manager_instance):
        """Test deleting empty correspondents with individual confirmation."""
        empty_correspondents = [{"id": 1, "name": "Empty 1"}]

        with patch.object(
            manager_instance,
            "find_empty_correspondents",
            return_value=empty_correspondents,
        ):
            with patch.object(manager_instance, "print_empty_correspondents"):
                with patch.object(
                    manager_instance, "delete_correspondent", return_value=True
                ):
                    with patch("builtins.input", return_value="y"):
                        with patch("builtins.print"):
                            result = manager_instance.delete_empty_correspondents(
                                confirm_each=True
                            )

        assert result == 1

    def test_delete_empty_correspondents_batch_mode_confirmed(self, manager_instance):
        """Test deleting empty correspondents in batch mode with confirmation."""
        empty_correspondents = [
            {"id": 1, "name": "Empty 1"},
            {"id": 2, "name": "Empty 2"},
        ]

        with patch.object(
            manager_instance,
            "find_empty_correspondents",
            return_value=empty_correspondents,
        ):
            with patch.object(manager_instance, "print_empty_correspondents"):
                with patch.object(
                    manager_instance, "delete_correspondent", return_value=True
                ):
                    with patch("builtins.input", return_value="y"):
                        with patch("builtins.print"):
                            result = manager_instance.delete_empty_correspondents(
                                confirm_each=False
                            )

        assert result == 2

    def test_delete_empty_correspondents_batch_mode_cancelled(self, manager_instance):
        """Test deleting empty correspondents in batch mode cancelled."""
        empty_correspondents = [{"id": 1, "name": "Empty 1"}]

        with patch.object(
            manager_instance,
            "find_empty_correspondents",
            return_value=empty_correspondents,
        ):
            with patch.object(manager_instance, "print_empty_correspondents"):
                with patch("builtins.input", return_value="n"):
                    with patch("builtins.print") as mock_print:
                        result = manager_instance.delete_empty_correspondents(
                            confirm_each=False
                        )

        assert result == 0
        # Should include cancellation message
        call_args_list = [call[0][0] for call in mock_print.call_args_list]
        assert any("cancelled" in str(arg).lower() for arg in call_args_list)


class TestDiagnoseCorrespondent:
    """Test diagnose_correspondent method."""

    def test_diagnose_correspondent_success(self, manager_instance, sample_documents):
        """Test successful correspondent diagnosis."""
        correspondent = {"id": 1, "name": "John Doe", "document_count": 5}
        correspondent_docs = [
            doc for doc in sample_documents if doc.get("correspondent") == 1
        ]

        manager_instance.session.get.return_value.json.return_value = correspondent
        manager_instance.session.get.return_value.raise_for_status.return_value = None

        with patch.object(
            manager_instance,
            "get_correspondent_documents",
            return_value=correspondent_docs,
        ):
            diagnosis = manager_instance.diagnose_correspondent(1)

        assert "correspondent" in diagnosis
        assert "document_count" in diagnosis
        assert "documents" in diagnosis
        assert "detailed_documents" in diagnosis
        assert diagnosis["correspondent"]["id"] == 1
        assert diagnosis["document_count"] == len(correspondent_docs)

    def test_diagnose_correspondent_request_exception(self, manager_instance):
        """Test diagnose_correspondent handles request exceptions."""
        manager_instance.session.get.side_effect = requests.exceptions.RequestException(
            "Network error"
        )

        with patch("builtins.print") as mock_print:
            diagnosis = manager_instance.diagnose_correspondent(1)

        assert diagnosis == {}
        mock_print.assert_called_with("Error fetching correspondent 1: Network error")


class TestFindDocumentsByDateRange:
    """Test find_documents_by_date_range method."""

    def test_find_documents_by_date_range_success(
        self, manager_instance, sample_documents
    ):
        """Test successful document search by date range."""
        api_response = {
            "results": sample_documents[:2],  # Return first 2 documents
            "next": None,
            "previous": None,
        }

        manager_instance.session.get.return_value.json.return_value = api_response
        manager_instance.session.get.return_value.raise_for_status.return_value = None

        documents = manager_instance.find_documents_by_date_range(
            "2025-06-01", "2025-06-10"
        )

        assert len(documents) == 2
        manager_instance.session.get.assert_called_once()
        # Check that date parameters were included in the request
        call_args = manager_instance.session.get.call_args
        assert "created__date__gte" in call_args[1]["params"]
        assert "created__date__lte" in call_args[1]["params"]

    def test_find_documents_by_date_range_no_dates(
        self, manager_instance, sample_documents
    ):
        """Test document search without date parameters."""
        api_response = {"results": sample_documents, "next": None, "previous": None}

        manager_instance.session.get.return_value.json.return_value = api_response
        manager_instance.session.get.return_value.raise_for_status.return_value = None

        documents = manager_instance.find_documents_by_date_range()

        assert len(documents) == len(sample_documents)
        call_args = manager_instance.session.get.call_args
        assert call_args[1]["params"] == {}

    def test_find_documents_by_date_range_request_exception(self, manager_instance):
        """Test find_documents_by_date_range handles request exceptions."""
        manager_instance.session.get.side_effect = requests.exceptions.RequestException(
            "Network error"
        )

        with patch("builtins.print") as mock_print:
            documents = manager_instance.find_documents_by_date_range(
                "2025-06-01", "2025-06-10"
            )

        assert documents == []
        mock_print.assert_called_with("Error fetching documents: Network error")


class TestRestoreDocumentsToCorrespondent:
    """Test restore_documents_to_correspondent method."""

    def test_restore_documents_success(self, manager_instance):
        """Test successful document restoration."""
        document_ids = [101, 102, 103]

        with patch.object(
            manager_instance, "bulk_reassign_documents", return_value=True
        ) as mock_bulk:
            with patch("builtins.print"):
                result = manager_instance.restore_documents_to_correspondent(
                    document_ids, 1
                )

        assert result is True
        mock_bulk.assert_called_once_with(document_ids, 1, batch_size=25)

    def test_restore_documents_empty_list(self, manager_instance):
        """Test document restoration with empty list."""
        with patch("builtins.print") as mock_print:
            result = manager_instance.restore_documents_to_correspondent([], 1)

        assert result is True
        mock_print.assert_called_with("No documents to restore.")

    def test_restore_documents_bulk_reassign_fails(self, manager_instance):
        """Test document restoration when bulk reassign fails."""
        document_ids = [101, 102, 103]

        with patch.object(
            manager_instance, "bulk_reassign_documents", return_value=False
        ):
            with patch("builtins.print"):
                result = manager_instance.restore_documents_to_correspondent(
                    document_ids, 1
                )

        assert result is False


# AIDEV-NOTE: Additional test classes for complex methods like auto_merge_similar_correspondents
# and merge_correspondent_group would require more sophisticated mocking of user inputs
# These are covered in integration tests where we can better simulate user interactions
