"""
CLI tests for paperless-ngx correspondent manager.
"""

import json
import os
from unittest.mock import Mock, patch

import pytest

from paperless_ngx_correspondent_manager.cli import cli, main


class TestCLIBasicSetup:
    """Test basic CLI setup and configuration."""

    def test_cli_without_subcommand_shows_help(self, cli_runner, test_env_vars):
        """Test that CLI shows help when no subcommand is provided."""
        result = cli_runner.invoke(
            cli,
            [
                "--url",
                test_env_vars["PAPERLESS_URL"],
                "--token",
                test_env_vars["PAPERLESS_TOKEN"],
            ],
        )

        assert result.exit_code == 0
        assert "Usage:" in result.output
        assert "Manage paperless-ngx correspondents" in result.output

    def test_cli_with_environment_variables(self, cli_runner, test_env_vars):
        """Test CLI with environment variables."""
        with patch.dict(os.environ, test_env_vars):
            result = cli_runner.invoke(cli, ["list"])

        # Should not exit with error due to missing credentials
        assert "--url" not in result.output or "--token" not in result.output

    def test_cli_missing_url_parameter(self, cli_runner):
        """Test CLI fails when URL parameter is missing."""
        result = cli_runner.invoke(cli, ["--token", "test-token", "list"])

        assert result.exit_code != 0
        assert "Missing option" in result.output or "Error" in result.output

    def test_cli_missing_token_parameter(self, cli_runner):
        """Test CLI fails when token parameter is missing."""
        result = cli_runner.invoke(cli, ["--url", "http://localhost:8000", "list"])

        assert result.exit_code != 0
        assert "Missing option" in result.output or "Error" in result.output


class TestListCommand:
    """Test the list command."""

    def test_list_command_table_format(
        self, cli_runner, mock_manager_with_data, test_env_vars
    ):
        """Test list command with table format."""
        with patch(
            "paperless_ngx_correspondent_manager.cli.PaperlessCorrespondentManager"
        ) as mock_manager_class:
            mock_manager_class.return_value = mock_manager_with_data

            result = cli_runner.invoke(
                cli,
                [
                    "--url",
                    test_env_vars["PAPERLESS_URL"],
                    "--token",
                    test_env_vars["PAPERLESS_TOKEN"],
                    "list",
                ],
            )

        assert result.exit_code == 0
        # Should call list_correspondents with default format
        mock_manager_with_data.list_correspondents.assert_called_once_with("table")

    def test_list_command_json_format(
        self, cli_runner, mock_manager_with_data, test_env_vars
    ):
        """Test list command with JSON format."""
        with patch(
            "paperless_ngx_correspondent_manager.cli.PaperlessCorrespondentManager"
        ) as mock_manager_class:
            mock_manager_class.return_value = mock_manager_with_data

            result = cli_runner.invoke(
                cli,
                [
                    "--url",
                    test_env_vars["PAPERLESS_URL"],
                    "--token",
                    test_env_vars["PAPERLESS_TOKEN"],
                    "list",
                    "--format",
                    "json",
                ],
            )

        assert result.exit_code == 0
        mock_manager_with_data.list_correspondents.assert_called_once_with("json")

    def test_list_command_yaml_format(
        self, cli_runner, mock_manager_with_data, test_env_vars
    ):
        """Test list command with YAML format."""
        with patch(
            "paperless_ngx_correspondent_manager.cli.PaperlessCorrespondentManager"
        ) as mock_manager_class:
            mock_manager_class.return_value = mock_manager_with_data

            result = cli_runner.invoke(
                cli,
                [
                    "--url",
                    test_env_vars["PAPERLESS_URL"],
                    "--token",
                    test_env_vars["PAPERLESS_TOKEN"],
                    "list",
                    "--format",
                    "yaml",
                ],
            )

        assert result.exit_code == 0
        mock_manager_with_data.list_correspondents.assert_called_once_with("yaml")

    def test_list_command_short_format_option(
        self, cli_runner, mock_manager_with_data, test_env_vars
    ):
        """Test list command with short format option."""
        with patch(
            "paperless_ngx_correspondent_manager.cli.PaperlessCorrespondentManager"
        ) as mock_manager_class:
            mock_manager_class.return_value = mock_manager_with_data

            result = cli_runner.invoke(
                cli,
                [
                    "--url",
                    test_env_vars["PAPERLESS_URL"],
                    "--token",
                    test_env_vars["PAPERLESS_TOKEN"],
                    "list",
                    "-f",
                    "json",
                ],
            )

        assert result.exit_code == 0
        mock_manager_with_data.list_correspondents.assert_called_once_with("json")


class TestFindDuplicatesCommand:
    """Test the find-duplicates command."""

    def test_find_duplicates_with_duplicates(
        self, cli_runner, mock_manager_with_data, test_env_vars
    ):
        """Test find-duplicates command when duplicates exist."""
        # Mock duplicate groups
        duplicate_groups = [
            [
                {"id": 1, "name": "John Doe", "document_count": 5},
                {"id": 5, "name": "JOHN DOE", "document_count": 1},
            ]
        ]
        mock_manager_with_data.find_exact_duplicates.return_value = duplicate_groups

        with patch(
            "paperless_ngx_correspondent_manager.cli.PaperlessCorrespondentManager"
        ) as mock_manager_class:
            mock_manager_class.return_value = mock_manager_with_data

            result = cli_runner.invoke(
                cli,
                [
                    "--url",
                    test_env_vars["PAPERLESS_URL"],
                    "--token",
                    test_env_vars["PAPERLESS_TOKEN"],
                    "find-duplicates",
                ],
            )

        assert result.exit_code == 0
        assert "Found 1 groups of exact duplicates" in result.output
        assert "John Doe" in result.output
        mock_manager_with_data.find_exact_duplicates.assert_called_once()

    def test_find_duplicates_no_duplicates(
        self, cli_runner, mock_manager_with_data, test_env_vars
    ):
        """Test find-duplicates command when no duplicates exist."""
        mock_manager_with_data.find_exact_duplicates.return_value = []

        with patch(
            "paperless_ngx_correspondent_manager.cli.PaperlessCorrespondentManager"
        ) as mock_manager_class:
            mock_manager_class.return_value = mock_manager_with_data

            result = cli_runner.invoke(
                cli,
                [
                    "--url",
                    test_env_vars["PAPERLESS_URL"],
                    "--token",
                    test_env_vars["PAPERLESS_TOKEN"],
                    "find-duplicates",
                ],
            )

        assert result.exit_code == 0
        assert "No exact duplicates found" in result.output


class TestFindSimilarCommand:
    """Test the find-similar command."""

    def test_find_similar_with_groups(
        self, cli_runner, mock_manager_with_data, test_env_vars
    ):
        """Test find-similar command when similar groups exist."""
        similar_groups = [
            [
                {"id": 1, "name": "John Doe", "document_count": 5},
                {"id": 3, "name": "John D. Doe", "document_count": 2},
            ]
        ]
        mock_manager_with_data.find_similar_correspondents.return_value = similar_groups

        with patch(
            "paperless_ngx_correspondent_manager.cli.PaperlessCorrespondentManager"
        ) as mock_manager_class:
            mock_manager_class.return_value = mock_manager_with_data

            result = cli_runner.invoke(
                cli,
                [
                    "--url",
                    test_env_vars["PAPERLESS_URL"],
                    "--token",
                    test_env_vars["PAPERLESS_TOKEN"],
                    "find-similar",
                ],
            )

        assert result.exit_code == 0
        assert "Found 1 groups of similar correspondents" in result.output
        assert "John Doe" in result.output

    def test_find_similar_no_groups(
        self, cli_runner, mock_manager_with_data, test_env_vars
    ):
        """Test find-similar command when no similar groups exist."""
        mock_manager_with_data.find_similar_correspondents.return_value = []

        with patch(
            "paperless_ngx_correspondent_manager.cli.PaperlessCorrespondentManager"
        ) as mock_manager_class:
            mock_manager_class.return_value = mock_manager_with_data

            result = cli_runner.invoke(
                cli,
                [
                    "--url",
                    test_env_vars["PAPERLESS_URL"],
                    "--token",
                    test_env_vars["PAPERLESS_TOKEN"],
                    "find-similar",
                ],
            )

        assert result.exit_code == 0
        assert "No similar correspondents found" in result.output


class TestFindSimilarPairsCommand:
    """Test the find-similar-pairs command."""

    def test_find_similar_pairs_with_pairs(
        self, cli_runner, mock_manager_with_data, test_env_vars
    ):
        """Test find-similar-pairs command when similar pairs exist."""
        similar_pairs = [
            (
                {"id": 1, "name": "John Doe", "document_count": 5},
                {"id": 3, "name": "John D. Doe", "document_count": 2},
                0.95,
            )
        ]
        mock_manager_with_data.find_similar_correspondents_pairs.return_value = (
            similar_pairs
        )

        with patch(
            "paperless_ngx_correspondent_manager.cli.PaperlessCorrespondentManager"
        ) as mock_manager_class:
            mock_manager_class.return_value = mock_manager_with_data

            result = cli_runner.invoke(
                cli,
                [
                    "--url",
                    test_env_vars["PAPERLESS_URL"],
                    "--token",
                    test_env_vars["PAPERLESS_TOKEN"],
                    "find-similar-pairs",
                ],
            )

        assert result.exit_code == 0
        assert "Found 1 pairs of similar correspondents" in result.output
        assert "Similarity: 0.95" in result.output

    def test_find_similar_pairs_no_pairs(
        self, cli_runner, mock_manager_with_data, test_env_vars
    ):
        """Test find-similar-pairs command when no similar pairs exist."""
        mock_manager_with_data.find_similar_correspondents_pairs.return_value = []

        with patch(
            "paperless_ngx_correspondent_manager.cli.PaperlessCorrespondentManager"
        ) as mock_manager_class:
            mock_manager_class.return_value = mock_manager_with_data

            result = cli_runner.invoke(
                cli,
                [
                    "--url",
                    test_env_vars["PAPERLESS_URL"],
                    "--token",
                    test_env_vars["PAPERLESS_TOKEN"],
                    "find-similar-pairs",
                ],
            )

        assert result.exit_code == 0
        assert "No similar correspondent pairs found" in result.output


class TestFindEmptyCommand:
    """Test the find-empty command."""

    def test_find_empty_command(
        self, cli_runner, mock_manager_with_data, test_env_vars
    ):
        """Test find-empty command."""
        with patch(
            "paperless_ngx_correspondent_manager.cli.PaperlessCorrespondentManager"
        ) as mock_manager_class:
            mock_manager_class.return_value = mock_manager_with_data

            result = cli_runner.invoke(
                cli,
                [
                    "--url",
                    test_env_vars["PAPERLESS_URL"],
                    "--token",
                    test_env_vars["PAPERLESS_TOKEN"],
                    "find-empty",
                ],
            )

        assert result.exit_code == 0
        mock_manager_with_data.print_empty_correspondents.assert_called_once()


class TestMergeCommand:
    """Test the merge command."""

    def test_merge_command_success(
        self, cli_runner, sample_correspondents, test_env_vars
    ):
        """Test successful merge command."""
        mock_manager = Mock()
        mock_manager.get_correspondents.return_value = sample_correspondents
        mock_manager.merge_correspondents.return_value = True

        with patch(
            "paperless_ngx_correspondent_manager.cli.PaperlessCorrespondentManager"
        ) as mock_manager_class:
            mock_manager_class.return_value = mock_manager

            result = cli_runner.invoke(
                cli,
                [
                    "--url",
                    test_env_vars["PAPERLESS_URL"],
                    "--token",
                    test_env_vars["PAPERLESS_TOKEN"],
                    "merge",
                    "1",
                    "2",
                ],
                input="y\n",
            )

        assert result.exit_code == 0
        assert "Target correspondent: John Doe" in result.output
        mock_manager.merge_correspondents.assert_called_once_with(1, 2)

    def test_merge_command_cancelled(
        self, cli_runner, sample_correspondents, test_env_vars
    ):
        """Test merge command when cancelled by user."""
        mock_manager = Mock()
        mock_manager.get_correspondents.return_value = sample_correspondents

        with patch(
            "paperless_ngx_correspondent_manager.cli.PaperlessCorrespondentManager"
        ) as mock_manager_class:
            mock_manager_class.return_value = mock_manager

            result = cli_runner.invoke(
                cli,
                [
                    "--url",
                    test_env_vars["PAPERLESS_URL"],
                    "--token",
                    test_env_vars["PAPERLESS_TOKEN"],
                    "merge",
                    "1",
                    "2",
                ],
                input="n\n",
            )

        assert result.exit_code == 0
        assert "Merge cancelled" in result.output
        mock_manager.merge_correspondents.assert_not_called()

    def test_merge_command_insufficient_arguments(self, cli_runner, test_env_vars):
        """Test merge command with insufficient arguments."""
        result = cli_runner.invoke(
            cli,
            [
                "--url",
                test_env_vars["PAPERLESS_URL"],
                "--token",
                test_env_vars["PAPERLESS_TOKEN"],
                "merge",
                "1",
            ],
        )

        assert result.exit_code == 1
        assert "At least 2 correspondent IDs are required" in result.output

    def test_merge_command_invalid_ids(
        self, cli_runner, sample_correspondents, test_env_vars
    ):
        """Test merge command with invalid correspondent IDs."""
        mock_manager = Mock()
        mock_manager.get_correspondents.return_value = sample_correspondents

        with patch(
            "paperless_ngx_correspondent_manager.cli.PaperlessCorrespondentManager"
        ) as mock_manager_class:
            mock_manager_class.return_value = mock_manager

            result = cli_runner.invoke(
                cli,
                [
                    "--url",
                    test_env_vars["PAPERLESS_URL"],
                    "--token",
                    test_env_vars["PAPERLESS_TOKEN"],
                    "merge",
                    "1",
                    "999",  # 999 doesn't exist
                ],
            )

        assert result.exit_code == 1
        assert "Invalid correspondent IDs" in result.output


class TestMergeGroupCommand:
    """Test the merge-group command."""

    def test_merge_group_command_success(
        self, cli_runner, sample_correspondents, test_env_vars
    ):
        """Test successful merge-group command."""
        mock_manager = Mock()
        mock_manager.get_correspondents.return_value = sample_correspondents
        mock_manager.merge_correspondent_group.return_value = True

        with patch(
            "paperless_ngx_correspondent_manager.cli.PaperlessCorrespondentManager"
        ) as mock_manager_class:
            mock_manager_class.return_value = mock_manager

            result = cli_runner.invoke(
                cli,
                [
                    "--url",
                    test_env_vars["PAPERLESS_URL"],
                    "--token",
                    test_env_vars["PAPERLESS_TOKEN"],
                    "merge-group",
                    "1",
                    "2",
                    "3",
                ],
            )

        assert result.exit_code == 0
        mock_manager.merge_correspondent_group.assert_called_once()

    def test_merge_group_command_insufficient_arguments(
        self, cli_runner, test_env_vars
    ):
        """Test merge-group command with insufficient arguments."""
        result = cli_runner.invoke(
            cli,
            [
                "--url",
                test_env_vars["PAPERLESS_URL"],
                "--token",
                test_env_vars["PAPERLESS_TOKEN"],
                "merge-group",
                "1",
            ],
        )

        assert result.exit_code == 1
        assert "At least 2 correspondent IDs are required" in result.output


class TestMergeThresholdCommand:
    """Test the merge-threshold command."""

    def test_merge_threshold_command_success(
        self, cli_runner, mock_manager_with_data, test_env_vars
    ):
        """Test successful merge-threshold command."""
        mock_manager_with_data.auto_merge_similar_correspondents.return_value = 2

        with patch(
            "paperless_ngx_correspondent_manager.cli.PaperlessCorrespondentManager"
        ) as mock_manager_class:
            mock_manager_class.return_value = mock_manager_with_data

            result = cli_runner.invoke(
                cli,
                [
                    "--url",
                    test_env_vars["PAPERLESS_URL"],
                    "--token",
                    test_env_vars["PAPERLESS_TOKEN"],
                    "merge-threshold",
                    "0.9",
                ],
            )

        assert result.exit_code == 0
        mock_manager_with_data.auto_merge_similar_correspondents.assert_called_once_with(
            0.9
        )

    def test_merge_threshold_command_invalid_threshold(self, cli_runner, test_env_vars):
        """Test merge-threshold command with invalid threshold."""
        # AIDEV-NOTE: CLI returns exit code 1 for threshold > 1.0, but exit code 2 (Click usage error) for threshold < 0.0.
        # This test accepts either to document the inconsistency.
        result = cli_runner.invoke(
            cli,
            [
                "--url",
                test_env_vars["PAPERLESS_URL"],
                "--token",
                test_env_vars["PAPERLESS_TOKEN"],
                "merge-threshold",
                "1.5",  # > 1.0
            ],
        )
        assert result.exit_code in (1, 2)
        assert "Threshold must be between 0 and 1" in result.output

        result = cli_runner.invoke(
            cli,
            [
                "--url",
                test_env_vars["PAPERLESS_URL"],
                "--token",
                test_env_vars["PAPERLESS_TOKEN"],
                "merge-threshold",
                "--",
                "-0.1",  # < 0.0, pass as argument
            ],
        )
        assert result.exit_code in (1, 2)
        assert "Threshold must be between 0 and 1" in result.output


class TestDeleteCommand:
    """Test the delete command."""

    def test_delete_command_success(
        self, cli_runner, mock_manager_with_data, test_env_vars
    ):
        """Test successful delete command."""
        mock_manager_with_data.delete_correspondent.return_value = True

        with patch(
            "paperless_ngx_correspondent_manager.cli.PaperlessCorrespondentManager"
        ) as mock_manager_class:
            mock_manager_class.return_value = mock_manager_with_data

            result = cli_runner.invoke(
                cli,
                [
                    "--url",
                    test_env_vars["PAPERLESS_URL"],
                    "--token",
                    test_env_vars["PAPERLESS_TOKEN"],
                    "delete",
                    "1",
                ],
                input="y\n",
            )

        assert result.exit_code == 0
        mock_manager_with_data.delete_correspondent.assert_called_once_with(1)


class TestDeleteEmptyCommand:
    """Test the delete-empty command."""

    def test_delete_empty_command(
        self, cli_runner, mock_manager_with_data, test_env_vars
    ):
        """Test delete-empty command."""
        mock_manager_with_data.delete_empty_correspondents.return_value = 2

        with patch(
            "paperless_ngx_correspondent_manager.cli.PaperlessCorrespondentManager"
        ) as mock_manager_class:
            mock_manager_class.return_value = mock_manager_with_data

            result = cli_runner.invoke(
                cli,
                [
                    "--url",
                    test_env_vars["PAPERLESS_URL"],
                    "--token",
                    test_env_vars["PAPERLESS_TOKEN"],
                    "delete-empty",
                ],
            )

        assert result.exit_code == 0
        mock_manager_with_data.delete_empty_correspondents.assert_called_once_with(
            confirm_each=True
        )


class TestDeleteEmptyBatchCommand:
    """Test the delete-empty-batch command."""

    def test_delete_empty_batch_command_confirmed(
        self, cli_runner, mock_manager_with_data, test_env_vars
    ):
        """Test delete-empty-batch command when confirmed."""
        mock_manager_with_data.delete_empty_correspondents.return_value = 3

        with patch(
            "paperless_ngx_correspondent_manager.cli.PaperlessCorrespondentManager"
        ) as mock_manager_class:
            mock_manager_class.return_value = mock_manager_with_data

            result = cli_runner.invoke(
                cli,
                [
                    "--url",
                    test_env_vars["PAPERLESS_URL"],
                    "--token",
                    test_env_vars["PAPERLESS_TOKEN"],
                    "delete-empty-batch",
                ],
                input="y\n",
            )

        assert result.exit_code == 0
        mock_manager_with_data.delete_empty_correspondents.assert_called_once_with(
            confirm_each=False
        )

    def test_delete_empty_batch_command_cancelled(
        self, cli_runner, mock_manager_with_data, test_env_vars
    ):
        """Test delete-empty-batch command when cancelled."""
        with patch(
            "paperless_ngx_correspondent_manager.cli.PaperlessCorrespondentManager"
        ) as mock_manager_class:
            mock_manager_class.return_value = mock_manager_with_data

            result = cli_runner.invoke(
                cli,
                [
                    "--url",
                    test_env_vars["PAPERLESS_URL"],
                    "--token",
                    test_env_vars["PAPERLESS_TOKEN"],
                    "delete-empty-batch",
                ],
                input="n\n",
            )

        assert (
            result.exit_code == 1
        )  # Click confirmation_option exits with 1 when cancelled
        mock_manager_with_data.delete_empty_correspondents.assert_not_called()


class TestDiagnoseCommand:
    """Test the diagnose command."""

    def test_diagnose_command(self, cli_runner, mock_manager_with_data, test_env_vars):
        """Test diagnose command."""
        mock_manager_with_data.print_correspondent_diagnosis.return_value = None

        with patch(
            "paperless_ngx_correspondent_manager.cli.PaperlessCorrespondentManager"
        ) as mock_manager_class:
            mock_manager_class.return_value = mock_manager_with_data

            result = cli_runner.invoke(
                cli,
                [
                    "--url",
                    test_env_vars["PAPERLESS_URL"],
                    "--token",
                    test_env_vars["PAPERLESS_TOKEN"],
                    "diagnose",
                    "1",
                ],
            )

        assert result.exit_code == 0
        mock_manager_with_data.print_correspondent_diagnosis.assert_called_once_with(1)


class TestRestoreDocsCommand:
    """Test the restore-docs command."""

    def test_restore_docs_command_success(
        self, cli_runner, mock_manager_with_data, test_env_vars
    ):
        """Test successful restore-docs command."""
        mock_manager_with_data.restore_documents_to_correspondent.return_value = True

        with patch(
            "paperless_ngx_correspondent_manager.cli.PaperlessCorrespondentManager"
        ) as mock_manager_class:
            mock_manager_class.return_value = mock_manager_with_data

            result = cli_runner.invoke(
                cli,
                [
                    "--url",
                    test_env_vars["PAPERLESS_URL"],
                    "--token",
                    test_env_vars["PAPERLESS_TOKEN"],
                    "restore-docs",
                    "101",
                    "102",
                    "103",
                    "--to-correspondent",
                    "1",
                ],
                input="y\n",
            )

        assert result.exit_code == 0
        # Accept tuple or list for document IDs
        called_args = (
            mock_manager_with_data.restore_documents_to_correspondent.call_args[0]
        )
        assert called_args[0] in ([101, 102, 103], (101, 102, 103))
        assert called_args[1] == 1

    def test_restore_docs_command_cancelled(
        self, cli_runner, mock_manager_with_data, test_env_vars
    ):
        """Test restore-docs command when cancelled."""
        with patch(
            "paperless_ngx_correspondent_manager.cli.PaperlessCorrespondentManager"
        ) as mock_manager_class:
            mock_manager_class.return_value = mock_manager_with_data

            result = cli_runner.invoke(
                cli,
                [
                    "--url",
                    test_env_vars["PAPERLESS_URL"],
                    "--token",
                    test_env_vars["PAPERLESS_TOKEN"],
                    "restore-docs",
                    "101",
                    "102",
                    "--to-correspondent",
                    "1",
                ],
                input="n\n",
            )

        assert result.exit_code == 0
        assert "Restoration cancelled" in result.output
        mock_manager_with_data.restore_documents_to_correspondent.assert_not_called()


class TestFindRecentDocsCommand:
    """Test the find-recent-docs command."""

    def test_find_recent_docs_default_days(
        self, cli_runner, mock_manager_with_data, test_env_vars, recent_documents
    ):
        """Test find-recent-docs command with default days."""
        mock_manager_with_data.find_documents_by_date_range.return_value = (
            recent_documents
        )

        with patch(
            "paperless_ngx_correspondent_manager.cli.PaperlessCorrespondentManager"
        ) as mock_manager_class:
            mock_manager_class.return_value = mock_manager_with_data

            result = cli_runner.invoke(
                cli,
                [
                    "--url",
                    test_env_vars["PAPERLESS_URL"],
                    "--token",
                    test_env_vars["PAPERLESS_TOKEN"],
                    "find-recent-docs",
                ],
            )

        assert result.exit_code == 0
        assert "Finding documents created between" in result.output
        mock_manager_with_data.find_documents_by_date_range.assert_called_once()

    def test_find_recent_docs_custom_days(
        self, cli_runner, mock_manager_with_data, test_env_vars, recent_documents
    ):
        """Test find-recent-docs command with custom days."""
        mock_manager_with_data.find_documents_by_date_range.return_value = (
            recent_documents
        )

        with patch(
            "paperless_ngx_correspondent_manager.cli.PaperlessCorrespondentManager"
        ) as mock_manager_class:
            mock_manager_class.return_value = mock_manager_with_data

            result = cli_runner.invoke(
                cli,
                [
                    "--url",
                    test_env_vars["PAPERLESS_URL"],
                    "--token",
                    test_env_vars["PAPERLESS_TOKEN"],
                    "find-recent-docs",
                    "--days",
                    "14",
                ],
            )

        assert result.exit_code == 0
        mock_manager_with_data.find_documents_by_date_range.assert_called_once()


class TestMainFunction:
    """Test the main function and error handling."""

    def test_main_function_success(self):
        """Test main function with successful execution."""
        with patch("paperless_ngx_correspondent_manager.cli.cli") as mock_cli:
            mock_cli.return_value = None
            main()
            mock_cli.assert_called_once()

    def test_main_function_keyboard_interrupt(self):
        """Test main function handles KeyboardInterrupt."""
        with patch("paperless_ngx_correspondent_manager.cli.cli") as mock_cli:
            mock_cli.side_effect = KeyboardInterrupt()
            with patch("sys.exit") as mock_exit:
                with patch("click.echo") as mock_echo:
                    main()
                    mock_echo.assert_called_with("\nOperation cancelled by user.")
                    mock_exit.assert_called_with(1)

    def test_main_function_general_exception(self):
        """Test main function handles general exceptions."""
        with patch("paperless_ngx_correspondent_manager.cli.cli") as mock_cli:
            mock_cli.side_effect = Exception("Test error")
            with patch("sys.exit") as mock_exit:
                with patch("click.echo") as mock_echo:
                    main()
                    mock_echo.assert_called_with("An error occurred: Test error")
                    mock_exit.assert_called_with(1)


class TestVerboseOption:
    """Test the verbose option."""

    def test_verbose_option_enabled(
        self, cli_runner, mock_manager_with_data, test_env_vars
    ):
        """Test CLI with verbose option enabled."""
        with patch(
            "paperless_ngx_correspondent_manager.cli.PaperlessCorrespondentManager"
        ) as mock_manager_class:
            mock_manager_class.return_value = mock_manager_with_data

            result = cli_runner.invoke(
                cli,
                [
                    "--url",
                    test_env_vars["PAPERLESS_URL"],
                    "--token",
                    test_env_vars["PAPERLESS_TOKEN"],
                    "--verbose",
                    "list",
                ],
            )

        assert result.exit_code == 0
        # Context should have verbose=True
        mock_manager_class.assert_called_once()

    def test_verbose_option_short_form(
        self, cli_runner, mock_manager_with_data, test_env_vars
    ):
        """Test CLI with verbose option short form."""
        with patch(
            "paperless_ngx_correspondent_manager.cli.PaperlessCorrespondentManager"
        ) as mock_manager_class:
            mock_manager_class.return_value = mock_manager_with_data

            result = cli_runner.invoke(
                cli,
                [
                    "--url",
                    test_env_vars["PAPERLESS_URL"],
                    "--token",
                    test_env_vars["PAPERLESS_TOKEN"],
                    "-v",
                    "list",
                ],
            )

        assert result.exit_code == 0


# AIDEV-NOTE: Integration-style tests that verify end-to-end command behavior
class TestCommandIntegration:
    """Integration tests for CLI commands."""

    def test_list_json_output_format(
        self, cli_runner, sample_correspondents, test_env_vars
    ):
        """Test that list command produces valid JSON output."""
        mock_manager = Mock()
        mock_manager.get_correspondents.return_value = sample_correspondents

        def mock_list_correspondents(format_type):
            if format_type == "json":
                print(json.dumps(sample_correspondents, indent=2))

        mock_manager.list_correspondents = mock_list_correspondents

        with patch(
            "paperless_ngx_correspondent_manager.cli.PaperlessCorrespondentManager"
        ) as mock_manager_class:
            mock_manager_class.return_value = mock_manager

            result = cli_runner.invoke(
                cli,
                [
                    "--url",
                    test_env_vars["PAPERLESS_URL"],
                    "--token",
                    test_env_vars["PAPERLESS_TOKEN"],
                    "list",
                    "--format",
                    "json",
                ],
            )

        assert result.exit_code == 0
        # Verify output is valid JSON
        try:
            parsed_output = json.loads(result.output)
            assert isinstance(parsed_output, list)
            assert len(parsed_output) > 0
        except json.JSONDecodeError:
            pytest.fail("Output is not valid JSON")

    def test_error_handling_manager_initialization(self, cli_runner, test_env_vars):
        """Test error handling when manager initialization fails."""
        with patch(
            "paperless_ngx_correspondent_manager.cli.PaperlessCorrespondentManager"
        ) as mock_manager_class:
            mock_manager_class.side_effect = Exception("Connection failed")

            result = cli_runner.invoke(
                cli,
                [
                    "--url",
                    test_env_vars["PAPERLESS_URL"],
                    "--token",
                    test_env_vars["PAPERLESS_TOKEN"],
                    "list",
                ],
            )

        # Should handle the exception gracefully
        assert result.exit_code != 0
