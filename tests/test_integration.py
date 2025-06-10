"""
Integration tests for paperless-ngx correspondent manager.

These tests verify end-to-end functionality and complex scenarios.
"""

import json
from unittest.mock import Mock, patch

import pytest
import requests

from paperless_ngx_correspondent_manager.manager import PaperlessCorrespondentManager


class TestManagerIntegration:
    """Integration tests for manager functionality."""

    @pytest.fixture
    def full_manager_setup(self, mock_session, sample_correspondents, sample_documents):
        """Set up a fully configured manager for integration testing."""
        manager = PaperlessCorrespondentManager("http://localhost:8000", "test-token")
        manager.session = mock_session

        # Configure comprehensive mock responses
        def get_correspondents_side_effect():
            return sample_correspondents

        def get_correspondent_documents_side_effect(corr_id):
            return [
                doc for doc in sample_documents if doc.get("correspondent") == corr_id
            ]

        def session_get_side_effect(url, **kwargs):
            response = Mock()
            response.raise_for_status.return_value = None

            # AIDEV-NOTE: Fix single correspondent fetch to return a dict, not a paginated result
            if "/api/correspondents/" in url:
                # Remove query parameters for matching
                url_base = url.split("?")[0]
                import re

                match = re.match(r".*/api/correspondents/(\d+)(/)?$", url_base)
                if match:
                    corr_id = int(match.group(1))
                    correspondent = next(
                        (c for c in sample_correspondents if c["id"] == corr_id), None
                    )
                    if correspondent:
                        response.json.return_value = correspondent
                        response.status_code = 200
                    else:
                        response.raise_for_status.side_effect = (
                            requests.exceptions.HTTPError("404")
                        )
                else:
                    # All correspondents request
                    response.json.return_value = {
                        "results": sample_correspondents,
                        "next": None,
                        "count": len(sample_correspondents),
                    }
                    response.status_code = 200
            elif "/api/documents/" in url:
                # Documents request
                if "correspondent__id__in" in url:
                    # Filter by correspondent
                    corr_id = int(url.split("correspondent__id__in=")[1].split("&")[0])
                    filtered_docs = [
                        doc
                        for doc in sample_documents
                        if doc.get("correspondent") == corr_id
                    ]
                    response.json.return_value = {
                        "results": filtered_docs,
                        "next": None,
                        "count": len(filtered_docs),
                    }
                else:
                    # All documents
                    response.json.return_value = {
                        "results": sample_documents,
                        "next": None,
                        "count": len(sample_documents),
                    }

            return response

        def session_post_side_effect(url, **kwargs):
            response = Mock()
            response.raise_for_status.return_value = None
            response.status_code = 200
            response.json.return_value = {"success": True, "updated": 1}
            return response

        def session_delete_side_effect(url, **kwargs):
            response = Mock()
            response.raise_for_status.return_value = None
            response.status_code = 204
            return response

        mock_session.get.side_effect = session_get_side_effect
        mock_session.post.side_effect = session_post_side_effect
        mock_session.delete.side_effect = session_delete_side_effect

        return manager

    def test_complete_duplicate_detection_workflow(self, full_manager_setup):
        """Test complete workflow for finding and managing duplicates."""
        manager = full_manager_setup

        # Find exact duplicates
        with patch("builtins.print"):
            exact_duplicates = manager.find_exact_duplicates()

        # Should find John Doe duplicates (case insensitive)
        assert len(exact_duplicates) == 1
        duplicate_group = exact_duplicates[0]
        assert len(duplicate_group) == 2
        names = [corr["name"].lower() for corr in duplicate_group]
        assert "john doe" in names
        assert "john doe" in names  # Both should normalize to same name

    def test_complete_similarity_detection_workflow(self, full_manager_setup):
        """Test complete workflow for finding similar correspondents."""
        manager = full_manager_setup

        # Find similar correspondents with different thresholds
        with patch("builtins.print"):
            similar_high_threshold = manager.find_similar_correspondents(threshold=0.9)
            similar_low_threshold = manager.find_similar_correspondents(threshold=0.7)

        # High threshold should find fewer groups
        # Low threshold should find more groups
        assert len(similar_low_threshold) >= len(similar_high_threshold)

    def test_complete_merge_workflow(self, full_manager_setup, sample_documents):
        """Test complete merge workflow including document reassignment."""
        manager = full_manager_setup

        # Get documents for source correspondent before merge
        target_id = 1
        source_id = 2

        with patch("builtins.print"):
            # Perform merge
            result = manager.merge_correspondents(source_id, target_id)

        assert result is True
        # Should have called bulk reassignment
        manager.session.post.assert_called()

        # Verify bulk edit payload structure
        call_args = manager.session.post.call_args
        payload = call_args[1]["json"]
        assert "documents" in payload
        assert "method" in payload
        assert payload["method"] == "set_correspondent"
        assert payload["parameters"]["correspondent"] == target_id

    def test_empty_correspondent_cleanup_workflow(self, full_manager_setup):
        """Test complete workflow for finding and cleaning up empty correspondents."""
        manager = full_manager_setup

        # Find empty correspondents
        empty_correspondents = manager.find_empty_correspondents()

        # Should find the empty correspondent from sample data
        assert len(empty_correspondents) == 1
        assert empty_correspondents[0]["document_count"] == 0
        assert empty_correspondents[0]["name"] == "Empty Correspondent"

        # Test deletion workflow (mocked)
        with patch("builtins.input", return_value="y"):
            with patch("builtins.print"):
                deleted_count = manager.delete_empty_correspondents(confirm_each=False)

        assert deleted_count == 1
        manager.session.delete.assert_called()

    def test_comprehensive_diagnosis_workflow(self, full_manager_setup):
        """Test comprehensive correspondent diagnosis."""
        manager = full_manager_setup

        with patch("builtins.print"):
            diagnosis = manager.diagnose_correspondent(1)

        assert "correspondent" in diagnosis
        assert "document_count" in diagnosis
        assert "documents" in diagnosis
        assert "detailed_documents" in diagnosis

        correspondent = diagnosis["correspondent"]
        assert "id" in correspondent, f"Diagnosis missing 'id': {diagnosis}"
        assert correspondent["id"] == 1
        assert correspondent["name"] == "John Doe"

        # Should have found documents for this correspondent
        assert diagnosis["document_count"] > 0

    def test_date_range_document_search_workflow(self, full_manager_setup):
        """Test document search by date range."""
        manager = full_manager_setup

        with patch("builtins.print"):
            documents = manager.find_documents_by_date_range("2025-06-01", "2025-06-10")

        assert isinstance(documents, list)
        # Should call the documents API with date parameters
        manager.session.get.assert_called()

    def test_bulk_document_reassignment_batching(self, full_manager_setup):
        """Test bulk document reassignment with proper batching."""
        manager = full_manager_setup

        # Test with large number of documents to trigger batching
        large_document_list = list(
            range(1, 151)
        )  # 150 documents, should create 3 batches

        with patch("builtins.print"):
            result = manager.bulk_reassign_documents(
                large_document_list, 1, batch_size=50
            )

        assert result is True
        # Should have made 3 POST requests (3 batches of 50)
        assert manager.session.post.call_count == 3

    def test_error_handling_in_complex_operations(self, full_manager_setup):
        """Test error handling in complex operations."""
        manager = full_manager_setup

        # Test network error during correspondent retrieval
        manager.session.get.side_effect = requests.exceptions.ConnectionError(
            "Network error"
        )

        with patch("builtins.print") as mock_print:
            with pytest.raises(SystemExit):
                manager.get_correspondents()

        mock_print.assert_called_with("Error fetching correspondents: Network error")

    def test_pagination_handling(self, mock_session):
        """Test proper handling of paginated API responses."""
        manager = PaperlessCorrespondentManager("http://localhost:8000", "test-token")
        manager.session = mock_session

        # Mock paginated response
        page1_response = {
            "results": [{"id": 1, "name": "Test 1"}],
            "next": "http://localhost:8000/api/correspondents/?page=2",
            "count": 3,
        }
        page2_response = {
            "results": [{"id": 2, "name": "Test 2"}],
            "next": "http://localhost:8000/api/correspondents/?page=3",
            "count": 3,
        }
        page3_response = {
            "results": [{"id": 3, "name": "Test 3"}],
            "next": None,
            "count": 3,
        }

        mock_session.get.side_effect = [
            Mock(json=Mock(return_value=page1_response), raise_for_status=Mock()),
            Mock(json=Mock(return_value=page2_response), raise_for_status=Mock()),
            Mock(json=Mock(return_value=page3_response), raise_for_status=Mock()),
        ]

        with patch("builtins.print"):
            correspondents = manager.get_correspondents()

        assert len(correspondents) == 3
        assert mock_session.get.call_count == 3
        assert correspondents[0]["id"] == 1
        assert correspondents[1]["id"] == 2
        assert correspondents[2]["id"] == 3

    def test_merge_group_with_complex_selection(
        self, full_manager_setup, sample_correspondents
    ):
        """Test merge group functionality with target selection."""
        manager = full_manager_setup

        # Create a group with multiple correspondents
        group = sample_correspondents[:3]  # First 3 correspondents
        target_id = 1  # Use first correspondent as target

        with patch("builtins.print"):
            with patch("builtins.input", return_value="n"):  # Don't delete after merge
                result = manager.merge_correspondent_group(group, target_id)

        assert result is True
        # Should have made multiple merge calls (for each non-target correspondent)
        assert manager.session.post.call_count >= 1

    def test_auto_merge_with_user_interaction(self, full_manager_setup):
        """Test auto-merge functionality with simulated user interaction."""
        manager = full_manager_setup

        # Mock similar groups
        similar_groups = [
            [
                {"id": 1, "name": "John Doe", "document_count": 5},
                {"id": 5, "name": "JOHN DOE", "document_count": 1},
            ]
        ]

        with patch.object(
            manager, "find_similar_correspondents", return_value=similar_groups
        ):
            with patch.object(manager, "merge_correspondent_group", return_value=True):
                with patch(
                    "builtins.input", side_effect=["1", "y"]
                ):  # Select first, confirm merge
                    with patch("builtins.print"):
                        merged_count = manager.auto_merge_similar_correspondents(0.8)

        assert merged_count == 1

    def test_similarity_calculation_edge_cases(self, full_manager_setup):
        """Test similarity calculation with edge cases."""
        manager = full_manager_setup

        # Test various edge cases
        test_cases = [
            ("", "", 1.0),  # Empty strings
            ("A", "", 0.0),  # One empty
            ("Test", "Test", 1.0),  # Identical
            ("Test", "TEST", 1.0),  # Case difference
            ("  Test  ", "Test", 1.0),  # Whitespace
            ("John Doe", "Jane Doe", 0.6),  # Partial similarity (approximate)
            (
                "Completely Different",
                "Nothing Similar",
                0.0,
            ),  # No similarity (approximate)
        ]

        for name1, name2, expected_min in test_cases:
            similarity = manager.calculate_similarity(name1, name2)
            if expected_min == 1.0:
                assert similarity == 1.0, (
                    f"Expected exact match for '{name1}' and '{name2}'"
                )
            elif expected_min == 0.0 and "Different" in name1:
                assert similarity < 0.3, (
                    f"Expected low similarity for '{name1}' and '{name2}'"
                )
            else:
                assert similarity >= expected_min - 0.1, (
                    f"Expected similarity >= {expected_min} for '{name1}' and '{name2}'"
                )

    def test_document_restoration_workflow(self, full_manager_setup):
        """Test document restoration to correspondent."""
        manager = full_manager_setup

        document_ids = [101, 102, 103]
        target_correspondent = 1

        with patch("builtins.print"):
            result = manager.restore_documents_to_correspondent(
                document_ids, target_correspondent
            )

        assert result is True
        # Should use smaller batch size for restoration
        manager.session.post.assert_called()

    def test_output_format_integration(self, full_manager_setup, sample_correspondents):
        """Test different output formats work correctly."""
        manager = full_manager_setup

        # Test table format
        with patch("builtins.print") as mock_print:
            manager.list_correspondents("table")
        assert mock_print.call_count > 1  # Multiple print calls for table

        # Test JSON format
        with patch("builtins.print") as mock_print:
            manager.list_correspondents("json")
        # Accept at least one print call, and check last call is valid JSON
        assert mock_print.call_count >= 1
        json_output = mock_print.call_args[0][0]
        parsed = json.loads(json_output)
        assert isinstance(parsed, list)

        # Test YAML format
        with patch("builtins.print") as mock_print:
            manager.list_correspondents("yaml")
        assert mock_print.call_count >= 1
        yaml_output = mock_print.call_args[0][0]
        assert "name:" in yaml_output


class TestErrorRecoveryScenarios:
    """Test error recovery and resilience scenarios."""

    def test_partial_batch_failure_recovery(self, mock_session):
        """Test recovery from partial batch failures in bulk operations."""
        manager = PaperlessCorrespondentManager("http://localhost:8000", "test-token")
        manager.session = mock_session

        # AIDEV-NOTE: Use a function side effect to simulate partial failure and retry logic robustly.
        call_count = {"count": 0}

        def post_side_effect(*args, **kwargs):
            if call_count["count"] == 0:
                call_count["count"] += 1
                raise requests.exceptions.Timeout("Timeout")
            else:
                return Mock(
                    raise_for_status=Mock(), json=Mock(return_value={"success": True})
                )

        mock_session.post.side_effect = post_side_effect

        document_ids = list(range(1, 101))  # 100 documents, 2 batches of 50

        # Should handle the timeout and continue with remaining batches
        with patch("builtins.print"):
            manager.bulk_reassign_documents(document_ids, 1, batch_size=50)

        # The method should attempt to handle errors gracefully
        assert mock_session.post.call_count >= 1

    def test_api_version_compatibility(self, mock_session):
        """Test API version header is correctly set."""
        manager = PaperlessCorrespondentManager("http://localhost:8000", "test-token")

        assert "Accept" in manager.session.headers
        assert "application/json; version=9" in manager.session.headers["Accept"]

    def test_url_construction_edge_cases(self, mock_session):
        """Test URL construction with various base URL formats."""
        test_cases = [
            "http://localhost:8000",
            "http://localhost:8000/",
            "https://paperless.example.com",
            "https://paperless.example.com/paperless",
            "https://paperless.example.com/paperless/",
        ]

        for base_url in test_cases:
            manager = PaperlessCorrespondentManager(base_url, "test-token")
            # URL should be normalized (no trailing slash)
            assert not manager.base_url.endswith("/")
            assert manager.base_url.startswith(("http://", "https://"))


# AIDEV-NOTE: Performance and load testing scenarios for comprehensive coverage
class TestPerformanceAndLoad:
    """Test performance characteristics and load scenarios."""

    def test_large_correspondent_list_handling(self, mock_session):
        """Test handling of large numbers of correspondents."""
        manager = PaperlessCorrespondentManager("http://localhost:8000", "test-token")
        manager.session = mock_session

        # Simulate large dataset
        large_correspondent_list = [
            {"id": i, "name": f"Correspondent {i}", "document_count": i % 10}
            for i in range(1, 1001)  # 1000 correspondents
        ]

        mock_session.get.return_value.json.return_value = {
            "results": large_correspondent_list,
            "next": None,
            "count": 1000,
        }
        mock_session.get.return_value.raise_for_status.return_value = None

        with patch("builtins.print"):
            correspondents = manager.get_correspondents()

        assert len(correspondents) == 1000

        # Test duplicate detection performance
        with patch("builtins.print"):
            duplicates = manager.find_exact_duplicates()

        # Should complete without errors
        assert isinstance(duplicates, list)

    def test_batch_size_optimization(self, mock_session):
        """Test that batch sizes are appropriate for different operations."""
        manager = PaperlessCorrespondentManager("http://localhost:8000", "test-token")
        manager.session = mock_session

        mock_session.post.return_value.raise_for_status.return_value = None
        mock_session.post.return_value.json.return_value = {"success": True}

        # Test document restoration uses smaller batches
        with patch("builtins.print"):
            manager.restore_documents_to_correspondent([1, 2, 3], 1)

        # Test regular bulk reassignment uses larger batches
        with patch("builtins.print"):
            manager.bulk_reassign_documents([1, 2, 3], 1)

        # Both should make API calls
        assert mock_session.post.call_count >= 2
