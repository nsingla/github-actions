import logging

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from slack_sdk.web.slack_response import SlackResponse

from slack_reporter.constants.slack_constants import SlackConstants


class SlackClient:
    """Client with interacting with Slack API."""

    client: WebClient = None
    channel_id: str = None
    logger: logging.Logger = logging.getLogger(__name__)

    def __init__(self) -> None:
        """Initialize session for interacting with Slack API."""
        access_token = SlackConstants.TOKEN
        if not access_token:
            raise ValueError(
                "The SLACK_BOT_TOKEN environment variable was not set. Cannot interact with Slack"
            )
        self.client = WebClient(token=SlackConstants.TOKEN)

    def get_channel_id_by_name(self, channel_name: str) -> str | None:
        """
        Send GET request to get the channel ID by it's name
        :param channel_name - name of the slack channel for which you want to get id for
        """
        self.logger.info(f"Getting channel id by it's name {channel_name}...")
        next_cursor = None
        try:
            if channel_name:
                while True:
                    conversations = self.client.conversations_list(
                        limit=100, cursor=next_cursor
                    )
                    for channel in conversations["channels"]:
                        if channel["name"] == channel_name:
                            channel_id = channel["id"]
                            self.logger.info(
                                f"Slack channel {channel_name} has ID {channel_id}"
                            )
                            return channel_id
                    if next_cursor := conversations["response_metadata"]["next_cursor"]:
                        self.logger.debug(
                            f"The Slack channel was not found on the fetched page; trying the next page using the cursor: "
                            f"{next_cursor}"
                        )
                    else:
                        self.logger.warning(
                            f"The channel {channel_name} was not found in the conversation list. Cannot get it's ID"
                        )
            else:
                self.logger.error("Please provide a slack channel name")
        except SlackApiError as e:
            self.logger.error("Error fetching conversations: {}".format(e))
            return None

    def send_message_in_thread_by_channel_id(
        self, channel_id: str, text: str, thread_ts: str = None
    ) -> SlackResponse:
        """Send the given text to the given slack channel, thread.
        :param channel_id - id of the slack channel where you want to post your message)
        :param text - body of your message
        :param thread_ts - timestamp of the parent message (Optional - if None, then the message is posted as a parent message)
        """
        self.logger.info(
            f"Sending the message to thread {thread_ts} on channel {channel_id}"
        )
        try:
            return self.client.chat_postMessage(
                channel=channel_id,
                mrkdwn=True,
                text=text,
                thread_ts=thread_ts,
                unfurl_links=False,
                unfurl_media=False,
            )
        except SlackApiError as e:
            self.logger.error(f"Failed to send the Slack message: {e}")

    def add_reaction_to_thread_by_channel_id(
        self, channel_id: str, emoji_name: str = "approved", thread_ts: str = None
    ) -> SlackResponse:
        """Send the given text to the given slack channel, thread.
        :param channel_id - id of the slack channel where you want to post your message)
        :param emoji_name - name of the emoji you want to reach with
        :param successful_run - Add an emoji of failed or pass to a slack message
        :param thread_ts - timestamp of the parent message (Optional - if None, then the message is posted as a parent message)
        """
        self.logger.info(
            f"Adding {emoji_name} reaction to thread {thread_ts}... on channel {channel_id} "
        )
        try:
            return self.client.reactions_add(
                channel=channel_id, name=emoji_name, timestamp=thread_ts
            )
        except SlackApiError as e:
            self.logger.error(f"Failed to add reaction to the Slack message: {e}")

    def send_message(
        self,
        channel_name: str = SlackConstants.SLACK_CHANNEL_NAME,
        text: str = None,
        thread_ts: str = SlackConstants.SLACK_THREAD_TS,
    ) -> SlackResponse:
        """
        Send the given text to the given slack channel as a parent message or in a thread
        :param channel_name - name of the slack channel where you want to post your message (Defalts to {SlackConstants.SLACK_CHANNEL_NAME})
        :param text - body of your message (Defaults to None)
        :param successful_run - If true adds a right tick as a reaction to the slack message
        :param thread_ts - timestamp of the parent message (Optional - if None, then the message is posted as a parent message)
        """
        self.channel_id: str = self.get_channel_id_by_name(channel_name=channel_name)
        return self.send_message_in_thread_by_channel_id(
            channel_id=self.channel_id, thread_ts=thread_ts, text=text
        )
