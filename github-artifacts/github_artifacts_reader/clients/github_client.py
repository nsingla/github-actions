import logging
import requests
from typing import Dict, List, Optional, Any

from github_artifacts_reader.constants.github_constants import GitHubConstants


class GitHubArtifactsClient:
    """Client for interacting with GitHub Actions Artifacts API."""

    def __init__(self) -> None:
        """Initialize the GitHub API client."""
        self.logger = logging.getLogger(__name__)
        self.constants = GitHubConstants()

        if not self.constants.GITHUB_TOKEN:
            raise ValueError(
                "The GITHUB_TOKEN environment variable was not set. Cannot interact with GitHub API"
            )

        self.headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {self.constants.GITHUB_TOKEN}",
            "X-GitHub-Api-Version": GitHubConstants.API_VERSION,
            "User-Agent": "GitHub-Artifacts-Reader-Action"
        }
        self.timeout = 30

    def _parse_repository(self, repository: str) -> tuple[str, str]:
        """Parse repository string into owner and repo."""
        if not repository:
            raise ValueError("Repository must be specified in format 'owner/repo'")

        parts = repository.split("/")
        if len(parts) != 2:
            raise ValueError("Repository must be in format 'owner/repo'")

        return parts[0], parts[1]

    def _make_request(self, url: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make a request to the GitHub API."""
        self.logger.info(f"Making request to: {url}")

        try:
            response = requests.get(
                url,
                headers=self.headers,
                params=params,
                timeout=self.timeout
            )

            if response.status_code == 401:
                raise ValueError("Authentication failed. Please check your GitHub token.")
            elif response.status_code == 403:
                raise ValueError("Access denied. Please ensure your token has the required permissions.")
            elif response.status_code == 404:
                raise ValueError("Repository or run not found. Please check your repository and run ID.")
            elif response.status_code != 200:
                raise ValueError(f"GitHub API request failed with status {response.status_code}: {response.text}")

            return response.json()

        except requests.exceptions.Timeout:
            raise ValueError("Request to GitHub API timed out")
        except requests.exceptions.RequestException as e:
            raise ValueError(f"Request to GitHub API failed: {str(e)}")

    def list_workflow_run_artifacts(
        self,
        repository: str,
        run_id: str,
        artifact_name: Optional[str] = None,
        per_page: int = 30,
        page: int = 1
    ) -> Dict[str, Any]:
        """
        List artifacts for a specific workflow run.

        Args:
            repository: Repository in format "owner/repo"
            run_id: Workflow run ID
            artifact_name: Optional artifact name to filter by
            per_page: Number of results per page (max 100)
            page: Page number

        Returns:
            Dictionary containing artifacts data
        """
        owner, repo = self._parse_repository(repository)
        url = GitHubConstants.get_artifacts_endpoint(owner, repo, run_id)

        params = {
            "per_page": min(per_page, 100),
            "page": page
        }

        if artifact_name:
            params["name"] = artifact_name

        return self._make_request(url, params)

    def list_repository_artifacts(
        self,
        repository: str,
        artifact_name: Optional[str] = None,
        per_page: int = 30,
        page: int = 1
    ) -> Dict[str, Any]:
        """
        List artifacts for a repository (all workflow runs).

        Args:
            repository: Repository in format "owner/repo"
            artifact_name: Optional artifact name to filter by
            per_page: Number of results per page (max 100)
            page: Page number

        Returns:
            Dictionary containing artifacts data
        """
        owner, repo = self._parse_repository(repository)
        url = GitHubConstants.get_repo_artifacts_endpoint(owner, repo)

        params = {
            "per_page": min(per_page, 100),
            "page": page
        }

        if artifact_name:
            params["name"] = artifact_name

        return self._make_request(url, params)

    def check_artifact_exists(
        self,
        repository: str,
        artifact_name: str,
        run_id: Optional[str] = None
    ) -> bool:
        """
        Check if an artifact with the given name exists.

        Args:
            repository: Repository in format "owner/repo"
            artifact_name: Name of the artifact to check
            run_id: Optional workflow run ID to limit search

        Returns:
            True if artifact exists, False otherwise
        """
        try:
            if run_id:
                # Search in specific run
                response = self.list_workflow_run_artifacts(
                    repository=repository,
                    run_id=run_id,
                    artifact_name=artifact_name,
                    per_page=1
                )
            else:
                # Search in repository
                response = self.list_repository_artifacts(
                    repository=repository,
                    artifact_name=artifact_name,
                    per_page=1
                )

            return response.get("total_count", 0) > 0

        except Exception as e:
            self.logger.error(f"Error checking artifact existence: {e}")
            return False

    def get_artifacts_summary(self, artifacts_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get a summary of artifacts data.

        Args:
            artifacts_data: Raw artifacts data from API

        Returns:
            Summary dictionary with key information
        """
        artifacts = artifacts_data.get("artifacts", [])

        summary = {
            "total_count": artifacts_data.get("total_count", 0),
            "artifacts": []
        }

        for artifact in artifacts:
            artifact_summary = {
                "id": artifact.get("id"),
                "name": artifact.get("name"),
                "size_in_bytes": artifact.get("size_in_bytes"),
                "expired": artifact.get("expired"),
                "created_at": artifact.get("created_at"),
                "expires_at": artifact.get("expires_at"),
                "archive_download_url": artifact.get("archive_download_url")
            }

            # Add workflow run info if available
            if "workflow_run" in artifact:
                workflow_run = artifact["workflow_run"]
                artifact_summary["workflow_run"] = {
                    "id": workflow_run.get("id"),
                    "head_branch": workflow_run.get("head_branch"),
                    "head_sha": workflow_run.get("head_sha")
                }

            summary["artifacts"].append(artifact_summary)

        return summary