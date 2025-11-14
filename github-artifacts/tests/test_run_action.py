"""Unit tests for run_action.py module."""

import os
import sys
from unittest.mock import Mock, mock_open, patch, MagicMock
import json

import pytest

import run_action


class TestSetGithubOutput:
    """Test cases for set_github_output function."""

    @patch("builtins.open", new_callable=mock_open)
    @patch.dict(os.environ, {"GITHUB_OUTPUT": "/tmp/github_output"})
    def test_set_github_output_with_file(self, mock_file):
        """Test setting GitHub output when GITHUB_OUTPUT env var is set."""
        # Act
        run_action.set_github_output("test-name", "test-value")

        # Assert
        mock_file.assert_called_once_with("/tmp/github_output", "a")
        mock_file().write.assert_called_once_with("test-name=test-value\n")

    @patch("builtins.print")
    @patch.dict(os.environ, {}, clear=True)
    def test_set_github_output_fallback(self, mock_print):
        """Test setting GitHub output fallback when GITHUB_OUTPUT is not set."""
        # Act
        run_action.set_github_output("test-name", "test-value")

        # Assert
        mock_print.assert_called_once_with("::set-output name=test-name::test-value")


class TestMain:
    """Test cases for main function."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_env = {
            "GITHUB_TOKEN": "test-token",
            "REPOSITORY": "owner/repo",
            "RUN_ID": "12345",
            "OPERATION": "list",
            "ARTIFACT_NAME": "",
            "PER_PAGE": "30",
            "PAGE": "1"
        }

    @patch("run_action.GitHubArtifactsClient")
    @patch("run_action.set_github_output")
    @patch.dict(os.environ, clear=True)
    def test_main_missing_repository(self, mock_set_output, mock_client_class):
        """Test main function with missing repository."""
        # Set environment without repository
        env = self.mock_env.copy()
        del env["REPOSITORY"]

        with patch.dict(os.environ, env):
            with pytest.raises(SystemExit) as exc_info:
                run_action.main()

            assert exc_info.value.code == 1

    @patch("run_action.GitHubArtifactsClient")
    @patch("run_action.set_github_output")
    @patch.dict(os.environ, clear=True)
    def test_main_invalid_operation(self, mock_set_output, mock_client_class):
        """Test main function with invalid operation."""
        # Set environment with invalid operation
        env = self.mock_env.copy()
        env["OPERATION"] = "invalid"

        with patch.dict(os.environ, env):
            with pytest.raises(SystemExit) as exc_info:
                run_action.main()

            assert exc_info.value.code == 1

    @patch("run_action.GitHubArtifactsClient")
    @patch("run_action.set_github_output")
    @patch.dict(os.environ, clear=True)
    def test_main_check_operation_missing_artifact_name(self, mock_set_output, mock_client_class):
        """Test main function with check operation but missing artifact name."""
        # Set environment for check operation without artifact name
        env = self.mock_env.copy()
        env["OPERATION"] = "check"
        env["ARTIFACT_NAME"] = ""

        with patch.dict(os.environ, env):
            with pytest.raises(SystemExit) as exc_info:
                run_action.main()

            assert exc_info.value.code == 1

    @patch("run_action.GitHubArtifactsClient")
    @patch("run_action.set_github_output")
    @patch.dict(os.environ, clear=True)
    def test_main_check_operation_success(self, mock_set_output, mock_client_class):
        """Test main function with successful check operation."""
        # Set environment for check operation
        env = self.mock_env.copy()
        env["OPERATION"] = "check"
        env["ARTIFACT_NAME"] = "test-artifact"

        # Mock client
        mock_client = MagicMock()
        mock_client.check_artifact_exists.return_value = True
        mock_client_class.return_value = mock_client

        with patch.dict(os.environ, env):
            run_action.main()

            # Verify client was called correctly
            mock_client.check_artifact_exists.assert_called_once_with(
                repository="owner/repo",
                artifact_name="test-artifact",
                run_id="12345"
            )

            # Verify outputs were set
            mock_set_output.assert_any_call('artifact-exists', 'true')
            mock_set_output.assert_any_call('total-count', '1')

    @patch("run_action.GitHubArtifactsClient")
    @patch("run_action.set_github_output")
    @patch.dict(os.environ, clear=True)
    def test_main_list_operation_success(self, mock_set_output, mock_client_class):
        """Test main function with successful list operation."""
        # Set environment for list operation
        env = self.mock_env.copy()
        env["OPERATION"] = "list"

        # Mock client
        mock_client = MagicMock()
        mock_artifacts_data = {
            "total_count": 2,
            "artifacts": [
                {"id": 1, "name": "artifact1"},
                {"id": 2, "name": "artifact2"}
            ]
        }
        mock_client.list_workflow_run_artifacts.return_value = mock_artifacts_data

        mock_summary = {
            "total_count": 2,
            "artifacts": [
                {"id": 1, "name": "artifact1"},
                {"id": 2, "name": "artifact2"}
            ]
        }
        mock_client.get_artifacts_summary.return_value = mock_summary
        mock_client_class.return_value = mock_client

        with patch.dict(os.environ, env):
            run_action.main()

            # Verify client was called correctly
            mock_client.list_workflow_run_artifacts.assert_called_once_with(
                repository="owner/repo",
                run_id="12345",
                artifact_name=None,
                per_page=30,
                page=1
            )

            # Verify outputs were set
            expected_artifacts_json = json.dumps(mock_summary['artifacts'])
            mock_set_output.assert_any_call('artifacts', expected_artifacts_json)
            mock_set_output.assert_any_call('total-count', '2')

    @patch("run_action.GitHubArtifactsClient")
    @patch("run_action.set_github_output")
    @patch.dict(os.environ, clear=True)
    def test_main_list_operation_no_run_id(self, mock_set_output, mock_client_class):
        """Test main function with list operation and no run ID."""
        # Set environment for list operation without run ID
        env = self.mock_env.copy()
        env["OPERATION"] = "list"
        env["RUN_ID"] = ""

        # Mock client
        mock_client = MagicMock()
        mock_artifacts_data = {"total_count": 0, "artifacts": []}
        mock_client.list_repository_artifacts.return_value = mock_artifacts_data

        mock_summary = {"total_count": 0, "artifacts": []}
        mock_client.get_artifacts_summary.return_value = mock_summary
        mock_client_class.return_value = mock_client

        with patch.dict(os.environ, env):
            run_action.main()

            # Verify client was called correctly (repository-level, not run-specific)
            mock_client.list_repository_artifacts.assert_called_once_with(
                repository="owner/repo",
                artifact_name=None,
                per_page=30,
                page=1
            )

    @patch("run_action.GitHubArtifactsClient")
    @patch.dict(os.environ, clear=True)
    def test_main_client_initialization_error(self, mock_client_class):
        """Test main function with client initialization error."""
        # Set environment
        env = self.mock_env.copy()

        # Mock client to raise ValueError
        mock_client_class.side_effect = ValueError("Invalid token")

        with patch.dict(os.environ, env):
            with pytest.raises(SystemExit) as exc_info:
                run_action.main()

            assert exc_info.value.code == 1