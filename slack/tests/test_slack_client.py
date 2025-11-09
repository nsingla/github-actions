"""Unit tests for SlackClient class."""

from unittest.mock import Mock, patch

import pytest
from slack_sdk.errors import SlackApiError
from slack_sdk.web.slack_response import SlackResponse

from slack_reporter.clients.slack_client import SlackClient


class TestSlackClient:
    """Test cases for SlackClient class."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        # Mock the environment variable to avoid actual token requirements
        self.mock_token = "xoxb-test-token"

    @patch(
        "slack_reporter.clients.slack_client.SlackConstants.TOKEN", "xoxb-test-token"
    )
    @patch("slack_reporter.clients.slack_client.WebClient")
    def test_init_success(self, mock_webclient):
        """Test successful initialization of SlackClient."""
        # Arrange
        mock_client_instance = Mock()
        mock_webclient.return_value = mock_client_instance

        # Act
        client = SlackClient()

        # Assert
        assert client.client == mock_client_instance
        mock_webclient.assert_called_once_with(token="xoxb-test-token", timeout=30)

    @patch("slack_reporter.clients.slack_client.SlackConstants.TOKEN", None)
    def test_init_no_token_raises_error(self):
        """Test initialization fails when no token is provided."""
        # Act & Assert
        with pytest.raises(
            ValueError, match="The SLACK_BOT_TOKEN environment variable was not set"
        ):
            SlackClient()

    @patch("slack_reporter.clients.slack_client.SlackConstants.TOKEN", "")
    def test_init_empty_token_raises_error(self):
        """Test initialization fails when empty token is provided."""
        # Act & Assert
        with pytest.raises(
            ValueError, match="The SLACK_BOT_TOKEN environment variable was not set"
        ):
            SlackClient()

    @patch(
        "slack_reporter.clients.slack_client.SlackConstants.TOKEN", "xoxb-test-token"
    )
    @patch("slack_reporter.clients.slack_client.WebClient")
    def test_get_channel_id_by_name_success(self, mock_webclient):
        """Test successful retrieval of channel ID by name."""
        # Arrange
        mock_client_instance = Mock()
        mock_webclient.return_value = mock_client_instance

        mock_response = {
            "channels": [
                {"name": "general", "id": "C123456"},
                {"name": "test-channel", "id": "C789012"},
            ],
            "response_metadata": {"next_cursor": ""},
        }
        mock_client_instance.conversations_list.return_value = mock_response

        client = SlackClient()

        # Act
        channel_id = client.get_channel_id_by_name("test-channel")

        # Assert
        assert channel_id == "C789012"
        mock_client_instance.conversations_list.assert_called_once_with(
            limit=100, cursor=None
        )

    @patch(
        "slack_reporter.clients.slack_client.SlackConstants.TOKEN", "xoxb-test-token"
    )
    @patch("slack_reporter.clients.slack_client.WebClient")
    def test_get_channel_id_by_name_with_pagination(self, mock_webclient):
        """Test channel ID retrieval with pagination."""
        # Arrange
        mock_client_instance = Mock()
        mock_webclient.return_value = mock_client_instance

        # First page response
        first_response = {
            "channels": [
                {"name": "general", "id": "C123456"},
            ],
            "response_metadata": {"next_cursor": "cursor123"},
        }

        # Second page response
        second_response = {
            "channels": [
                {"name": "test-channel", "id": "C789012"},
            ],
            "response_metadata": {"next_cursor": ""},
        }

        mock_client_instance.conversations_list.side_effect = [
            first_response,
            second_response,
        ]

        client = SlackClient()

        # Act
        channel_id = client.get_channel_id_by_name("test-channel")

        # Assert
        assert channel_id == "C789012"
        assert mock_client_instance.conversations_list.call_count == 2

    @patch(
        "slack_reporter.clients.slack_client.SlackConstants.TOKEN", "xoxb-test-token"
    )
    @patch("slack_reporter.clients.slack_client.WebClient")
    def test_get_channel_id_by_name_not_found(self, mock_webclient):
        """Test channel ID retrieval when channel is not found."""
        # Arrange
        mock_client_instance = Mock()
        mock_webclient.return_value = mock_client_instance

        mock_response = {
            "channels": [
                {"name": "general", "id": "C123456"},
            ],
            "response_metadata": {"next_cursor": ""},
        }
        mock_client_instance.conversations_list.return_value = mock_response

        client = SlackClient()

        # Act
        channel_id = client.get_channel_id_by_name("nonexistent-channel")

        # Assert
        assert channel_id is None

    @patch(
        "slack_reporter.clients.slack_client.SlackConstants.TOKEN", "xoxb-test-token"
    )
    @patch("slack_reporter.clients.slack_client.WebClient")
    def test_get_channel_id_by_name_empty_name(self, mock_webclient):
        """Test channel ID retrieval with empty channel name."""
        # Arrange
        mock_client_instance = Mock()
        mock_webclient.return_value = mock_client_instance

        client = SlackClient()

        # Act
        channel_id = client.get_channel_id_by_name("")

        # Assert
        assert channel_id is None
        mock_client_instance.conversations_list.assert_not_called()

    @patch(
        "slack_reporter.clients.slack_client.SlackConstants.TOKEN", "xoxb-test-token"
    )
    @patch("slack_reporter.clients.slack_client.WebClient")
    def test_get_channel_id_by_name_api_error(self, mock_webclient):
        """Test channel ID retrieval when Slack API returns an error."""
        # Arrange
        mock_client_instance = Mock()
        mock_webclient.return_value = mock_client_instance

        mock_client_instance.conversations_list.side_effect = SlackApiError(
            message="API Error", response={"error": "invalid_auth"}
        )

        client = SlackClient()

        # Act
        channel_id = client.get_channel_id_by_name("test-channel")

        # Assert
        assert channel_id is None

    @patch(
        "slack_reporter.clients.slack_client.SlackConstants.TOKEN", "xoxb-test-token"
    )
    @patch("slack_reporter.clients.slack_client.WebClient")
    def test_send_message_in_thread_by_channel_id_success(self, mock_webclient):
        """Test successful message sending to a thread."""
        # Arrange
        mock_client_instance = Mock()
        mock_webclient.return_value = mock_client_instance

        mock_response = SlackResponse(
            client=mock_client_instance,
            http_verb="POST",
            api_url="https://slack.com/api/chat.postMessage",
            req_args={},
            data={"ok": True, "ts": "1234567890.123456", "channel": "C123456"},
            headers={},
            status_code=200,
        )
        mock_client_instance.chat_postMessage.return_value = mock_response

        client = SlackClient()

        # Act
        response = client.send_message_in_thread_by_channel_id(
            channel_id="C123456", text="Test message", thread_ts="1234567890.123456"
        )

        # Assert
        assert response == mock_response
        mock_client_instance.chat_postMessage.assert_called_once_with(
            channel="C123456",
            mrkdwn=True,
            text="Test message",
            thread_ts="1234567890.123456",
            unfurl_links=False,
            unfurl_media=False,
        )

    @patch(
        "slack_reporter.clients.slack_client.SlackConstants.TOKEN", "xoxb-test-token"
    )
    @patch("slack_reporter.clients.slack_client.WebClient")
    def test_send_message_in_thread_by_channel_id_no_thread(self, mock_webclient):
        """Test successful message sending without threading."""
        # Arrange
        mock_client_instance = Mock()
        mock_webclient.return_value = mock_client_instance

        mock_response = SlackResponse(
            client=mock_client_instance,
            http_verb="POST",
            api_url="https://slack.com/api/chat.postMessage",
            req_args={},
            data={"ok": True, "ts": "1234567890.123456", "channel": "C123456"},
            headers={},
            status_code=200,
        )
        mock_client_instance.chat_postMessage.return_value = mock_response

        client = SlackClient()

        # Act
        response = client.send_message_in_thread_by_channel_id(
            channel_id="C123456", text="Test message", thread_ts=None
        )

        # Assert
        assert response == mock_response
        mock_client_instance.chat_postMessage.assert_called_once_with(
            channel="C123456",
            mrkdwn=True,
            text="Test message",
            thread_ts=None,
            unfurl_links=False,
            unfurl_media=False,
        )

    @patch(
        "slack_reporter.clients.slack_client.SlackConstants.TOKEN", "xoxb-test-token"
    )
    @patch("slack_reporter.clients.slack_client.WebClient")
    def test_send_message_in_thread_api_error(self, mock_webclient):
        """Test message sending when Slack API returns an error."""
        # Arrange
        mock_client_instance = Mock()
        mock_webclient.return_value = mock_client_instance

        mock_client_instance.chat_postMessage.side_effect = SlackApiError(
            message="API Error", response={"error": "channel_not_found"}
        )

        client = SlackClient()

        # Act
        response = client.send_message_in_thread_by_channel_id(
            channel_id="C123456", text="Test message"
        )

        # Assert
        assert response is None

    @patch(
        "slack_reporter.clients.slack_client.SlackConstants.TOKEN", "xoxb-test-token"
    )
    @patch("slack_reporter.clients.slack_client.WebClient")
    def test_add_reaction_to_thread_by_channel_id_success(self, mock_webclient):
        """Test successful reaction addition."""
        # Arrange
        mock_client_instance = Mock()
        mock_webclient.return_value = mock_client_instance

        mock_response = SlackResponse(
            client=mock_client_instance,
            http_verb="POST",
            api_url="https://slack.com/api/reactions.add",
            req_args={},
            data={"ok": True},
            headers={},
            status_code=200,
        )
        mock_client_instance.reactions_add.return_value = mock_response

        client = SlackClient()

        # Act
        response = client.add_reaction_to_thread_by_channel_id(
            channel_id="C123456", emoji_name="thumbsup", thread_ts="1234567890.123456"
        )

        # Assert
        assert response == mock_response
        mock_client_instance.reactions_add.assert_called_once_with(
            channel="C123456", name="thumbsup", timestamp="1234567890.123456"
        )

    @patch(
        "slack_reporter.clients.slack_client.SlackConstants.TOKEN", "xoxb-test-token"
    )
    @patch("slack_reporter.clients.slack_client.WebClient")
    def test_add_reaction_default_emoji(self, mock_webclient):
        """Test reaction addition with default emoji."""
        # Arrange
        mock_client_instance = Mock()
        mock_webclient.return_value = mock_client_instance

        mock_response = SlackResponse(
            client=mock_client_instance,
            http_verb="POST",
            api_url="https://slack.com/api/reactions.add",
            req_args={},
            data={"ok": True},
            headers={},
            status_code=200,
        )
        mock_client_instance.reactions_add.return_value = mock_response

        client = SlackClient()

        # Act
        response = client.add_reaction_to_thread_by_channel_id(
            channel_id="C123456", thread_ts="1234567890.123456"
        )

        # Assert
        assert response == mock_response
        mock_client_instance.reactions_add.assert_called_once_with(
            channel="C123456", name="approved", timestamp="1234567890.123456"
        )

    @patch(
        "slack_reporter.clients.slack_client.SlackConstants.TOKEN", "xoxb-test-token"
    )
    @patch("slack_reporter.clients.slack_client.WebClient")
    def test_add_reaction_api_error(self, mock_webclient):
        """Test reaction addition when Slack API returns an error."""
        # Arrange
        mock_client_instance = Mock()
        mock_webclient.return_value = mock_client_instance

        mock_client_instance.reactions_add.side_effect = SlackApiError(
            message="API Error", response={"error": "already_reacted"}
        )

        client = SlackClient()

        # Act
        response = client.add_reaction_to_thread_by_channel_id(
            channel_id="C123456", emoji_name="thumbsup", thread_ts="1234567890.123456"
        )

        # Assert
        assert response is None

    @patch(
        "slack_reporter.clients.slack_client.SlackConstants.TOKEN", "xoxb-test-token"
    )
    @patch(
        "slack_reporter.clients.slack_client.SlackConstants.SLACK_CHANNEL_NAME",
        "test-channel",
    )
    @patch(
        "slack_reporter.clients.slack_client.SlackConstants.SLACK_THREAD_TS",
        "1234567890.123456",
    )
    @patch("slack_reporter.clients.slack_client.WebClient")
    def test_send_message_integration(self, mock_webclient):
        """Test the integrated send_message method."""
        # Arrange
        mock_client_instance = Mock()
        mock_webclient.return_value = mock_client_instance

        # Mock get_channel_id_by_name response
        mock_conversations_response = {
            "channels": [
                {"name": "test-channel", "id": "C789012"},
            ],
            "response_metadata": {"next_cursor": ""},
        }
        mock_client_instance.conversations_list.return_value = (
            mock_conversations_response
        )

        # Mock send message response
        mock_response = SlackResponse(
            client=mock_client_instance,
            http_verb="POST",
            api_url="https://slack.com/api/chat.postMessage",
            req_args={},
            data={"ok": True, "ts": "1234567890.123456", "channel": "C789012"},
            headers={},
            status_code=200,
        )
        mock_client_instance.chat_postMessage.return_value = mock_response

        client = SlackClient()

        # Act
        response = client.send_message(
            channel_name="test-channel",
            text="Integration test message",
            thread_ts="1234567890.123456",
        )

        # Assert
        assert response == mock_response
        assert client.channel_id == "C789012"
        mock_client_instance.conversations_list.assert_called_once()
        mock_client_instance.chat_postMessage.assert_called_once_with(
            channel="C789012",
            mrkdwn=True,
            text="Integration test message",
            thread_ts="1234567890.123456",
            unfurl_links=False,
            unfurl_media=False,
        )

    @patch(
        "slack_reporter.clients.slack_client.SlackConstants.TOKEN", "xoxb-test-token"
    )
    @patch(
        "slack_reporter.clients.slack_client.SlackConstants.SLACK_CHANNEL_NAME",
        "default-channel",
    )
    @patch("slack_reporter.clients.slack_client.SlackConstants.SLACK_THREAD_TS", None)
    @patch("slack_reporter.clients.slack_client.WebClient")
    def test_send_message_with_defaults(self, mock_webclient):
        """Test send_message using default constants."""
        # Arrange
        mock_client_instance = Mock()
        mock_webclient.return_value = mock_client_instance

        # Mock get_channel_id_by_name response
        mock_conversations_response = {
            "channels": [
                {"name": "default-channel", "id": "C111111"},
            ],
            "response_metadata": {"next_cursor": ""},
        }
        mock_client_instance.conversations_list.return_value = (
            mock_conversations_response
        )

        # Mock send message response
        mock_response = SlackResponse(
            client=mock_client_instance,
            http_verb="POST",
            api_url="https://slack.com/api/chat.postMessage",
            req_args={},
            data={"ok": True, "ts": "1234567890.123456", "channel": "C111111"},
            headers={},
            status_code=200,
        )
        mock_client_instance.chat_postMessage.return_value = mock_response

        client = SlackClient()

        # Act
        response = client.send_message(
            channel_name="default-channel", text="Default test message"
        )

        # Assert
        assert response == mock_response
        assert client.channel_id == "C111111"
        mock_client_instance.conversations_list.assert_called_once_with(
            limit=100, cursor=None
        )
        mock_client_instance.chat_postMessage.assert_called_once_with(
            channel="C111111",
            mrkdwn=True,
            text="Default test message",
            thread_ts=None,
            unfurl_links=False,
            unfurl_media=False,
        )
