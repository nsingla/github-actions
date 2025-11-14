import os
from typing import Final


class GitHubConstants:
    """Constants for GitHub API interaction."""

    # GitHub API settings
    API_BASE_URL: Final[str] = os.getenv("GITHUB_API_URL", "https://api.github.com")
    API_VERSION: Final[str] = "2022-11-28"

    # Environment variables (properties to allow dynamic access)
    @property
    def GITHUB_TOKEN(self) -> str:
        return os.getenv("GITHUB_TOKEN")

    @property
    def REPOSITORY(self) -> str:
        return os.getenv("REPOSITORY", os.getenv("GITHUB_REPOSITORY", ""))

    @property
    def RUN_ID(self) -> str:
        return os.getenv("RUN_ID", os.getenv("GITHUB_RUN_ID", ""))

    @property
    def OPERATION(self) -> str:
        return os.getenv("OPERATION", "list")

    @property
    def ARTIFACT_NAME(self) -> str:
        return os.getenv("ARTIFACT_NAME", "")

    @property
    def PER_PAGE(self) -> int:
        return int(os.getenv("PER_PAGE", "30"))

    @property
    def PAGE(self) -> int:
        return int(os.getenv("PAGE", "1"))

    # API endpoints
    @classmethod
    def get_artifacts_endpoint(cls, owner: str, repo: str, run_id: str) -> str:
        """Get the artifacts API endpoint for a specific workflow run."""
        return f"{cls.API_BASE_URL}/repos/{owner}/{repo}/actions/runs/{run_id}/artifacts"

    @classmethod
    def get_repo_artifacts_endpoint(cls, owner: str, repo: str) -> str:
        """Get the artifacts API endpoint for a repository."""
        return f"{cls.API_BASE_URL}/repos/{owner}/{repo}/actions/artifacts"