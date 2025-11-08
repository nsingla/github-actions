# Slack Reporter GitHub Action

A GitHub Action to send messages to Slack channels with support for threading and reactions.

## Features

- 🚀 **Simple Setup**: No Docker required - runs as a composite action
- 💬 **Send Messages**: Post messages to any Slack channel
- 🧵 **Thread Support**: Reply to existing messages in threads
- 😎 **Reactions**: Add emoji reactions to messages
- 📊 **Outputs**: Get message timestamp and channel ID for further automation

## Quick Start

### 1. Set up Slack Bot Token

1. Create a Slack app at https://api.slack.com/apps
2. Add the following OAuth scopes to your bot:
   - `chat:write` - Send messages
   - `channels:read` - Read channel information
   - `reactions:write` - Add reactions
3. Install the app to your workspace
4. Copy the Bot User OAuth Token (starts with `xoxb-`)
5. Add it as a secret in your repository: `Settings > Secrets > SLACK_BOT_TOKEN`

### 2. Use in Your Workflow

```yaml
name: Notify Slack
on:
  push:
    branches: [ main ]

jobs:
  notify:
    runs-on: ubuntu-latest
    steps:
      - name: Send Slack notification
        uses: your-username/slack-reporter@v1
        with:
          slack-bot-token: ${{ secrets.SLACK_BOT_TOKEN }}
          channel-name: 'general'
          message: '🚀 New deployment to production completed!'
          add-reaction: 'true'
          reaction-emoji: 'rocket'
```

## Usage Examples

### Basic Message

```yaml
- name: Simple notification
  uses: your-username/slack-reporter@v1
  with:
    slack-bot-token: ${{ secrets.SLACK_BOT_TOKEN }}
    channel-name: 'deployments'
    message: 'Build completed successfully ✅'
```

### Thread Reply

```yaml
- name: Send initial message
  id: initial-message
  uses: your-username/slack-reporter@v1
  with:
    slack-bot-token: ${{ secrets.SLACK_BOT_TOKEN }}
    channel-name: 'ci-cd'
    message: '🔄 Starting deployment pipeline...'

- name: Reply in thread
  uses: your-username/slack-reporter@v1
  with:
    slack-bot-token: ${{ secrets.SLACK_BOT_TOKEN }}
    channel-name: 'ci-cd'
    message: '✅ Tests passed! Deploying to production...'
    thread-ts: ${{ steps.initial-message.outputs.message-ts }}
```

### Dynamic Messages

```yaml
- name: Deployment notification
  uses: your-username/slack-reporter@v1
  with:
    slack-bot-token: ${{ secrets.SLACK_BOT_TOKEN }}
    channel-name: 'deployments'
    message: |
      🚀 **Deployment Summary**

      **Repository:** ${{ github.repository }}
      **Branch:** ${{ github.ref_name }}
      **Commit:** ${{ github.sha }}
      **Author:** ${{ github.actor }}
      **Status:** Success ✅
    add-reaction: 'true'
    reaction-emoji: 'white_check_mark'
```

### Error Notifications

```yaml
- name: Failure notification
  if: failure()
  uses: your-username/slack-reporter@v1
  with:
    slack-bot-token: ${{ secrets.SLACK_BOT_TOKEN }}
    channel-name: 'alerts'
    message: |
      ❌ **Build Failed**

      **Workflow:** ${{ github.workflow }}
      **Repository:** ${{ github.repository }}
      **Branch:** ${{ github.ref_name }}
      **Run:** ${{ github.run_id }}
    add-reaction: 'true'
    reaction-emoji: 'x'
```

## Inputs

| Input | Description | Required | Default |
|-------|-------------|----------|---------|
| `slack-bot-token` | Slack Bot Token (starts with `xoxb-`) | ✅ Yes | - |
| `channel-name` | Slack channel name (without #) | ✅ Yes | - |
| `message` | Message to send to Slack | ✅ Yes | - |
| `thread-ts` | Parent message timestamp for threading | ❌ No | - |
| `add-reaction` | Add reaction to the message (`true`/`false`) | ❌ No | `false` |
| `reaction-emoji` | Emoji name for reaction | ❌ No | `white_check_mark` |

## Outputs

| Output | Description |
|--------|-------------|
| `message-ts` | Timestamp of the sent message |
| `channel-id` | ID of the channel where message was sent |

## Python Package Usage

You can also use this as a Python package:

```bash
pip install slack-reporter
```

```python
from slack_reporter.clients.slack_client import SlackClient
import os

# Set environment variables
os.environ['SLACK_BOT_TOKEN'] = 'xoxb-your-token'
os.environ['SLACK_CHANNEL_NAME'] = 'general'

client = SlackClient()
response = client.send_message(text="Hello from Python! 🐍")
```

## Development

### Running Tests

This project includes comprehensive unit tests. To run them:

1. **Install test dependencies:**
   ```bash
   pip install -e ".[test]"
   ```

2. **Run tests:**
   ```bash
   # Run all tests
   pytest

   # Run with coverage
   pytest --cov=slack_reporter --cov-report=term-missing

   # Run specific test file
   pytest tests/test_slack_client.py

   # Run with verbose output
   pytest -v
   ```

3. **Test Configuration:**
   - Tests are configured in `pyproject.toml`
   - Coverage reports exclude test files and virtual environments
   - Tests use `pytest-mock` for mocking Slack API calls

### Code Quality

The project includes GitHub Actions for automated testing and linting:

- **Tests:** Run on Python 3.11 and 3.12 on every push and PR
- **Linting:** Uses `ruff`, `black`, and `isort` for code quality
- **Coverage:** Uploaded to Codecov for tracking test coverage

### Building and Publishing

The package is automatically built and published to PyPI when a new release is created:

1. Create a new release on GitHub with a version tag (e.g., `v1.0.0`)
2. The publish workflow will:
   - Build the package using `hatchling`
   - Test the built package on multiple Python versions
   - Publish to PyPI using trusted publishing

## Required Slack Permissions

Your Slack bot needs these OAuth scopes:

- `chat:write` - Send messages as the bot
- `channels:read` - Access channel information
- `reactions:write` - Add emoji reactions

## License

MIT License - see LICENSE file for details.