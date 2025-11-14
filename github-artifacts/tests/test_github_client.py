"""Unit tests for GitHubArtifactsClient."""

import os
from unittest.mock import patch, MagicMock
import json

import pytest
import responses

from github_artifacts_reader.clients.github_client import GitHubArtifactsClient


class TestGitHubArtifactsClient:
    """Test cases for GitHubArtifactsClient."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_env = {
            "GITHUB_TOKEN": "test-token"
        }

    @patch.dict(os.environ, {}, clear=True)
    def test_init_without_token(self):
        """Test client initialization without token."""
        with pytest.raises(ValueError) as exc_info:
            GitHubArtifactsClient()

        assert "GITHUB_TOKEN environment variable was not set" in str(exc_info.value)

    @patch.dict(os.environ, clear=True)
    def test_init_with_token(self):
        """Test client initialization with token."""
        with patch.dict(os.environ, self.mock_env):
            client = GitHubArtifactsClient()

            assert client.headers["Authorization"] == "Bearer test-token"
            assert client.headers["Accept"] == "application/vnd.github+json"
            assert client.headers["X-GitHub-Api-Version"] == "2022-11-28"

    @patch.dict(os.environ, clear=True)
    def test_parse_repository_valid(self):
        """Test repository parsing with valid format."""
        with patch.dict(os.environ, self.mock_env):
            client = GitHubArtifactsClient()

            owner, repo = client._parse_repository("octocat/Hello-World")

            assert owner == "octocat"
            assert repo == "Hello-World"

    @patch.dict(os.environ, clear=True)
    def test_parse_repository_empty(self):
        """Test repository parsing with empty string."""
        with patch.dict(os.environ, self.mock_env):
            client = GitHubArtifactsClient()

            with pytest.raises(ValueError) as exc_info:
                client._parse_repository("")

            assert "Repository must be specified" in str(exc_info.value)

    @patch.dict(os.environ, clear=True)
    def test_parse_repository_invalid_format(self):
        """Test repository parsing with invalid format."""
        with patch.dict(os.environ, self.mock_env):
            client = GitHubArtifactsClient()

            with pytest.raises(ValueError) as exc_info:
                client._parse_repository("invalid-format")

            assert "Repository must be in format 'owner/repo'" in str(exc_info.value)

    @patch.dict(os.environ, clear=True)
    @responses.activate
    def test_make_request_success(self):
        """Test successful API request."""
        with patch.dict(os.environ, self.mock_env):
            client = GitHubArtifactsClient()

            # Mock successful response
            mock_response = {"total_count": 1, "artifacts": []}
            responses.add(
                responses.GET,
                "https://api.github.com/test",
                json=mock_response,
                status=200
            )

            response = client._make_request("https://api.github.com/test")

            assert response == mock_response

    @patch.dict(os.environ, clear=True)
    @responses.activate
    def test_make_request_401_unauthorized(self):
        """Test API request with 401 unauthorized."""
        with patch.dict(os.environ, self.mock_env):
            client = GitHubArtifactsClient()

            responses.add(
                responses.GET,
                "https://api.github.com/test",
                status=401
            )

            with pytest.raises(ValueError) as exc_info:
                client._make_request("https://api.github.com/test")

            assert "Authentication failed" in str(exc_info.value)

    @patch.dict(os.environ, clear=True)
    @responses.activate
    def test_make_request_403_forbidden(self):
        """Test API request with 403 forbidden."""
        with patch.dict(os.environ, self.mock_env):
            client = GitHubArtifactsClient()

            responses.add(
                responses.GET,
                "https://api.github.com/test",
                status=403
            )

            with pytest.raises(ValueError) as exc_info:
                client._make_request("https://api.github.com/test")

            assert "Access denied" in str(exc_info.value)

    @patch.dict(os.environ, clear=True)
    @responses.activate
    def test_make_request_404_not_found(self):
        """Test API request with 404 not found."""
        with patch.dict(os.environ, self.mock_env):
            client = GitHubArtifactsClient()

            responses.add(
                responses.GET,
                "https://api.github.com/test",
                status=404
            )

            with pytest.raises(ValueError) as exc_info:
                client._make_request("https://api.github.com/test")

            assert "Repository or run not found" in str(exc_info.value)

    @patch.dict(os.environ, clear=True)
    @responses.activate
    def test_list_workflow_run_artifacts_success(self):
        """Test successful workflow run artifacts listing."""
        with patch.dict(os.environ, self.mock_env):
            client = GitHubArtifactsClient()

            mock_response = {
                "total_count": 2,
                "artifacts": [
                    {"id": 1, "name": "artifact1"},
                    {"id": 2, "name": "artifact2"}
                ]
            }

            responses.add(
                responses.GET,
                "https://api.github.com/repos/owner/repo/actions/runs/12345/artifacts",
                json=mock_response,
                status=200
            )

            result = client.list_workflow_run_artifacts("owner/repo", "12345")

            assert result == mock_response

    @patch.dict(os.environ, clear=True)
    @responses.activate
    def test_list_workflow_run_artifacts_with_filters(self):
        """Test workflow run artifacts listing with filters."""
        with patch.dict(os.environ, self.mock_env):
            client = GitHubArtifactsClient()

            mock_response = {
                "total_count": 1,
                "artifacts": [{"id": 1, "name": "specific-artifact"}]
            }

            responses.add(
                responses.GET,
                "https://api.github.com/repos/owner/repo/actions/runs/12345/artifacts",
                json=mock_response,
                status=200,
                match=[
                    responses.matchers.query_param_matcher({
                        "name": "specific-artifact",
                        "per_page": "10",
                        "page": "2"
                    })
                ]
            )

            result = client.list_workflow_run_artifacts(
                "owner/repo", "12345", "specific-artifact", 10, 2
            )

            assert result == mock_response

    @patch.dict(os.environ, clear=True)
    @responses.activate
    def test_list_repository_artifacts_success(self):
        """Test successful repository artifacts listing."""
        with patch.dict(os.environ, self.mock_env):
            client = GitHubArtifactsClient()

            mock_response = {
                "total_count": 1,
                "artifacts": [{"id": 1, "name": "repo-artifact"}]
            }

            responses.add(
                responses.GET,
                "https://api.github.com/repos/owner/repo/actions/artifacts",
                json=mock_response,
                status=200
            )

            result = client.list_repository_artifacts("owner/repo")

            assert result == mock_response

    @patch.dict(os.environ, clear=True)
    @responses.activate
    def test_check_artifact_exists_true(self):
        """Test artifact existence check returning True."""
        with patch.dict(os.environ, self.mock_env):
            client = GitHubArtifactsClient()

            mock_response = {
                "total_count": 1,
                "artifacts": [{"id": 1, "name": "test-artifact"}]
            }

            responses.add(
                responses.GET,
                "https://api.github.com/repos/owner/repo/actions/runs/12345/artifacts",
                json=mock_response,
                status=200
            )

            result = client.check_artifact_exists("owner/repo", "test-artifact", "12345")

            assert result is True

    @patch.dict(os.environ, clear=True)
    @responses.activate
    def test_check_artifact_exists_false(self):
        """Test artifact existence check returning False."""
        with patch.dict(os.environ, self.mock_env):
            client = GitHubArtifactsClient()

            mock_response = {
                "total_count": 0,
                "artifacts": []
            }

            responses.add(
                responses.GET,
                "https://api.github.com/repos/owner/repo/actions/runs/12345/artifacts",
                json=mock_response,
                status=200
            )

            result = client.check_artifact_exists("owner/repo", "test-artifact", "12345")

            assert result is False

    @patch.dict(os.environ, clear=True)
    def test_check_artifact_exists_exception(self):
        """Test artifact existence check with exception."""
        with patch.dict(os.environ, self.mock_env):
            client = GitHubArtifactsClient()

            # Mock _make_request to raise an exception
            with patch.object(client, '_make_request') as mock_request:
                mock_request.side_effect = Exception("API Error")

                result = client.check_artifact_exists("owner/repo", "test-artifact", "12345")

                assert result is False

    @patch.dict(os.environ, clear=True)
    def test_get_artifacts_summary(self):
        """Test artifacts summary generation."""
        with patch.dict(os.environ, self.mock_env):
            client = GitHubArtifactsClient()

            artifacts_data = {
                "total_count": 2,
                "artifacts": [
                    {
                        "id": 1,
                        "name": "artifact1",
                        "size_in_bytes": 1024,
                        "expired": False,
                        "created_at": "2023-01-01T00:00:00Z",
                        "expires_at": "2023-01-31T00:00:00Z",
                        "archive_download_url": "https://example.com/download/1",
                        "workflow_run": {
                            "id": 12345,
                            "head_branch": "main",
                            "head_sha": "abcdef"
                        }
                    },
                    {
                        "id": 2,
                        "name": "artifact2",
                        "size_in_bytes": 2048,
                        "expired": True,
                        "created_at": "2023-01-02T00:00:00Z",
                        "expires_at": "2023-02-01T00:00:00Z",
                        "archive_download_url": "https://example.com/download/2"
                    }
                ]
            }

            summary = client.get_artifacts_summary(artifacts_data)

            assert summary["total_count"] == 2
            assert len(summary["artifacts"]) == 2

            # Check first artifact
            artifact1 = summary["artifacts"][0]
            assert artifact1["id"] == 1
            assert artifact1["name"] == "artifact1"
            assert artifact1["size_in_bytes"] == 1024
            assert artifact1["expired"] is False
            assert "workflow_run" in artifact1
            assert artifact1["workflow_run"]["id"] == 12345

            # Check second artifact (no workflow_run)
            artifact2 = summary["artifacts"][1]
            assert artifact2["id"] == 2
            assert artifact2["name"] == "artifact2"
            assert "workflow_run" not in artifact2