# GitHub Artifacts Reader

A GitHub Action to read and check GitHub workflow run artifacts with options to verify existence or list artifacts.

## Features

- 🚀 **Simple Setup**: No Docker required - runs as a composite action
- ✅ **Existence Check**: Check if a specific artifact exists in a workflow run
- 📋 **List Artifacts**: Get a list of all artifacts with detailed metadata
- 🔍 **Flexible Search**: Search artifacts by name, workflow run, or repository-wide
- 📊 **Outputs**: Get structured JSON data and boolean results for further automation
- 🔒 **Secure**: Uses GitHub tokens with proper permission handling

## Quick Start

### 1. Set up GitHub Token

The action requires a GitHub token with `actions:read` permission:

- **For public repositories**: The default `GITHUB_TOKEN` is sufficient
- **For private repositories**: You need a personal access token or GitHub App token with the `repo` scope

### 2. Use in Your Workflow

#### Check if an artifact exists:

```yaml
name: Check Artifacts
on:
  workflow_run:
    workflows: ["Build"]
    types: [completed]

jobs:
  check-artifacts:
    runs-on: ubuntu-latest
    steps:
      - name: Check if build artifact exists
        id: check-artifact
        uses: ./github-artifacts
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}
          operation: 'check'
          artifact-name: 'build-output'
          run-id: ${{ github.event.workflow_run.id }}

      - name: Process if artifact exists
        if: steps.check-artifact.outputs.artifact-exists == 'true'
        run: echo "Artifact found! Total count: ${{ steps.check-artifact.outputs.total-count }}"
```

#### List all artifacts:

```yaml
name: List Artifacts
on:
  push:
    branches: [ main ]

jobs:
  list-artifacts:
    runs-on: ubuntu-latest
    steps:
      - name: List workflow artifacts
        id: list-artifacts
        uses: ./github-artifacts
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}
          operation: 'list'
          per-page: 50

      - name: Display artifacts
        run: |
          echo "Total artifacts: ${{ steps.list-artifacts.outputs.total-count }}"
          echo "Artifacts JSON: ${{ steps.list-artifacts.outputs.artifacts }}"
```

## Usage Examples

### Basic Artifact Existence Check

```yaml
- name: Check for test results
  id: check-tests
  uses: ./github-artifacts
  with:
    github-token: ${{ secrets.GITHUB_TOKEN }}
    operation: 'check'
    artifact-name: 'test-results'
    run-id: ${{ github.run_id }}
```

### List Artifacts with Filtering

```yaml
- name: List deployment artifacts
  id: list-deployments
  uses: ./github-artifacts
  with:
    github-token: ${{ secrets.GITHUB_TOKEN }}
    operation: 'list'
    artifact-name: 'deployment'  # Filter by name
    per-page: 100
    page: 1
```

### Repository-wide Artifact Search

```yaml
- name: Search all repository artifacts
  id: search-all
  uses: ./github-artifacts
  with:
    github-token: ${{ secrets.GITHUB_TOKEN }}
    operation: 'list'
    repository: 'owner/repo'
    # No run-id = search entire repository
```

## Inputs

| Input | Description | Required | Default |
|-------|-------------|----------|---------|
| `github-token` | GitHub token with actions:read permission | Yes | - |
| `repository` | Repository in format "owner/repo" | No | Current repository |
| `run-id` | Workflow run ID | No | Current run |
| `operation` | Operation: "check" or "list" | Yes | `list` |
| `artifact-name` | Artifact name (required for check, optional filter for list) | No | - |
| `per-page` | Results per page (max 100) | No | `30` |
| `page` | Page number for pagination | No | `1` |

## Outputs

| Output | Description | Available For |
|--------|-------------|---------------|
| `artifact-exists` | Boolean indicating if artifact exists | `check` operation |
| `artifacts` | JSON array of artifacts with metadata | `list` operation |
| `total-count` | Total number of matching artifacts | Both operations |

### Artifacts JSON Structure

For `list` operations, the `artifacts` output contains a JSON array with the following structure:

```json
[
  {
    "id": 123456,
    "name": "build-output",
    "size_in_bytes": 1024000,
    "expired": false,
    "created_at": "2023-01-01T12:00:00Z",
    "expires_at": "2023-01-31T12:00:00Z",
    "archive_download_url": "https://api.github.com/repos/owner/repo/actions/artifacts/123456/zip",
    "workflow_run": {
      "id": 789012,
      "head_branch": "main",
      "head_sha": "abc123def456"
    }
  }
]
```

## Advanced Examples

### Conditional Workflow Based on Artifact Existence

```yaml
name: Deploy if Build Exists
on:
  workflow_dispatch:

jobs:
  check-and-deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Check for build artifacts
        id: check-build
        uses: ./github-artifacts
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}
          operation: 'check'
          artifact-name: 'production-build'

      - name: Deploy to production
        if: steps.check-build.outputs.artifact-exists == 'true'
        run: |
          echo "Build artifact found, proceeding with deployment"
          # Add your deployment logic here

      - name: Trigger build
        if: steps.check-build.outputs.artifact-exists == 'false'
        run: |
          echo "No build artifact found, triggering new build"
          # Add logic to trigger build workflow
```

### Processing Multiple Artifacts

```yaml
name: Process All Artifacts
on:
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM

jobs:
  process-artifacts:
    runs-on: ubuntu-latest
    steps:
      - name: Get all artifacts
        id: get-artifacts
        uses: ./github-artifacts
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}
          operation: 'list'
          per-page: 100

      - name: Process artifacts
        run: |
          echo '${{ steps.get-artifacts.outputs.artifacts }}' | jq -r '.[].name' | while read artifact_name; do
            echo "Processing artifact: $artifact_name"
            # Add your processing logic here
          done
```

## Error Handling

The action provides clear error messages for common issues:

- **Authentication errors**: Check your GitHub token permissions
- **Repository not found**: Verify the repository format and access rights
- **Run not found**: Ensure the run ID is valid and exists
- **Rate limiting**: The action respects GitHub API rate limits

## Development

### Testing

```bash
# Install dependencies
uv sync --dev

# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=github_artifacts_reader
```

### Local Testing

You can test the action locally by setting environment variables:

```bash
export GITHUB_TOKEN="your-token"
export REPOSITORY="owner/repo"
export OPERATION="list"

uv run run_action
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for your changes
4. Ensure all tests pass
5. Submit a pull request

## License

MIT License - see LICENSE file for details.