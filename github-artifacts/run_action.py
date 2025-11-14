#!/usr/bin/env python3
"""
GitHub Action entrypoint for GitHub Artifacts Reader.
This script handles the GitHub Action execution and outputs.
"""

import os
import sys
import logging
import json
from pathlib import Path

# Add the action directory to Python path to import our modules
action_dir = Path(__file__).parent
sys.path.insert(0, str(action_dir))

from github_artifacts_reader.clients.github_client import GitHubArtifactsClient
from github_artifacts_reader.constants.github_constants import GitHubConstants


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)

def set_github_output(name: str, value: str):
    """Set GitHub Action output."""
    github_output = os.environ.get('GITHUB_OUTPUT')
    if github_output:
        with open(github_output, 'a') as f:
            f.write(f"{name}={value}\n")
            logger.info(f"Setting GitHub output: {name}={value}")
    else:
        # Fallback for older runners
        print(f"::set-output name={name}::{value}")
        logger.info(f"Set GitHub output (fallback): {name}={value}")


def main():
    """Main entrypoint for the GitHub Action."""

    try:
        # Initialize constants
        constants = GitHubConstants()

        # Get inputs from environment
        repository = constants.REPOSITORY
        run_id = constants.RUN_ID
        operation = constants.OPERATION.lower()
        artifact_name = constants.ARTIFACT_NAME
        per_page = constants.PER_PAGE
        page = constants.PAGE

        # Validate inputs
        if not repository:
            logger.error(f"Repository is required but not provided. REPOSITORY env: '{os.getenv('REPOSITORY', 'NOT_SET')}', GITHUB_REPOSITORY env: '{os.getenv('GITHUB_REPOSITORY', 'NOT_SET')}'")
            sys.exit(1)

        if operation not in ['check', 'list']:
            logger.error("Operation must be either 'check' or 'list'")
            sys.exit(1)

        if operation == 'check' and not artifact_name:
            logger.error("Artifact name is required when operation is 'check'")
            sys.exit(1)

        logger.info(f"Repository: {repository}")
        logger.info(f"Operation: {operation}")
        if run_id:
            logger.info(f"Run ID: {run_id}")
        if artifact_name:
            logger.info(f"Artifact name: {artifact_name}")

        # Initialize GitHub client
        logger.info("Initializing GitHub client...")
        github_client = GitHubArtifactsClient()

        if operation == 'check':
            # Check if artifact exists
            logger.info(f"Checking if artifact '{artifact_name}' exists...")
            artifact_exists = False
            artifact_list = github_client.list_workflow_run_artifacts(
                repository=repository,
                run_id=run_id if run_id else None,
                per_page=1000
            )
            total_artifacts = artifact_list['total_count']
            logger.info(f"Found a total of {total_artifacts} artifacts")
            logger.info(f"Arifacts: {artifact_list['artifacts']}")
            if total_artifacts > 0:
                for artifact in artifact_list['artifacts']:
                    if artifact['name'].lower() == artifact_name.lower():
                        artifact_exists = True
            else:
                artifact_exists = False


            logger.info(f"✅ Artifact existence check completed, artifacts exists={str(artifact_exists).lower()}")

            # Set output
            set_github_output('artifact-exists', str(artifact_exists).lower())

        elif operation == 'list':
            # List artifacts
            logger.info(f"Listing artifacts (page {page}, per_page {per_page})...")

            if run_id:
                # List artifacts for specific run
                artifacts_data = github_client.list_workflow_run_artifacts(
                    repository=repository,
                    run_id=run_id,
                    artifact_name=artifact_name if artifact_name else None,
                    per_page=per_page,
                    page=page
                )
            else:
                # List artifacts for repository
                artifacts_data = github_client.list_repository_artifacts(
                    repository=repository,
                    artifact_name=artifact_name if artifact_name else None,
                    per_page=per_page,
                    page=page
                )

            # Get summary
            summary = github_client.get_artifacts_summary(artifacts_data)
            total_count = summary['count']
            artifacts_count = len(summary['artifacts'])

            logger.info(f"✅ Found {artifacts_count} artifacts on this page (total: {total_count})")

            # Set outputs
            set_github_output('artifacts', json.dumps(summary['artifacts']))
            set_github_output('total-count', str(total_count))

        logger.info("🎉 GitHub Artifacts Reader action completed successfully!")

    except ValueError as e:
        logger.error(f"❌ Configuration or API error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()