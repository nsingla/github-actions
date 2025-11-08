import os
from typing import Final


class SlackConstants:
    URL: Final[str] = os.getenv("SLACK_BASE_URL", "https://slack.com/api")
    TOKEN = os.getenv("SLACK_BOT_TOKEN")
    SLACK_CHANNEL_NAME = os.getenv("SLACK_CHANNEL_NAME")
    SLACK_THREAD_TS = os.getenv("PARENT_SLACK_MESSAGE_TIMESTAMP")