"""Unit tests for run_action.py module."""

import os
import sys
from unittest.mock import Mock, mock_open, patch

import pytest
from slack_sdk.web.slack_response import SlackResponse

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

    @patch("builtins.open", new_callable=mock_open)
    @patch.dict(os.environ, {"GITHUB_OUTPUT": ""})
    @patch("builtins.print")
    def test_set_github_output_empty_env_var(self, mock_print, mock_file):
        """Test setting GitHub output when GITHUB_OUTPUT is empty."""
        # Act
        run_action.set_github_output("test-name", "test-value")

        # Assert
        mock_file.assert_not_called()
        mock_print.assert_called_once_with("::set-output name=test-name::test-value")


class TestMain:
    """Test cases for main function."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.original_argv = sys.argv.copy()

    def teardown_method(self):
        """Clean up after each test method."""
        sys.argv = self.original_argv

    @patch("run_action.set_github_output")
    @patch("run_action.SlackClient")
    @patch(
        "slack_reporter.constants.slack_constants.SlackConstants.SLACK_CHANNEL_NAME",
        "test-channel",
    )
    @patch.dict(
        os.environ,
        {
            "SLACK_MESSAGE": "Test message",
            "ADD_REACTION": "false",
            "SLACK_BOT_TOKEN": "xoxb-test-token",
            "SLACK_CHANNEL_NAME": "test-channel",
        },
    )
    def test_main_success_no_reaction(self, mock_slack_client_class, mock_set_output):
        """Test successful main execution without reaction."""
        # Arrange
        mock_slack_client = Mock()
        mock_slack_client_class.return_value = mock_slack_client

        mock_response = SlackResponse(
            client=Mock(),
            http_verb="POST",
            api_url="https://slack.com/api/chat.postMessage",
            req_args={},
            data={"ok": True, "ts": "1234567890.123456", "channel": "C123456"},
            headers={},
            status_code=200,
        )
        mock_slack_client.send_message.return_value = mock_response

        # Act
        run_action.main()

        # Assert
        mock_slack_client.send_message.assert_called_once_with(text="Test message")
        mock_slack_client.add_reaction_to_thread_by_channel_id.assert_not_called()
        mock_set_output.assert_any_call("message-ts", "1234567890.123456")
        mock_set_output.assert_any_call("channel-id", "C123456")

    @patch("run_action.set_github_output")
    @patch("run_action.SlackClient")
    @patch(
        "slack_reporter.constants.slack_constants.SlackConstants.SLACK_CHANNEL_NAME",
        "test-channel",
    )
    @patch.dict(
        os.environ,
        {
            "SLACK_MESSAGE": "Test message",
            "ADD_REACTION": "true",
            "REACTION_EMOJI": "thumbsup",
            "SLACK_BOT_TOKEN": "xoxb-test-token",
            "SLACK_CHANNEL_NAME": "test-channel",
        },
    )
    def test_main_success_with_reaction(self, mock_slack_client_class, mock_set_output):
        """Test successful main execution with reaction."""
        # Arrange
        mock_slack_client = Mock()
        mock_slack_client_class.return_value = mock_slack_client

        mock_message_response = SlackResponse(
            client=Mock(),
            http_verb="POST",
            api_url="https://slack.com/api/chat.postMessage",
            req_args={},
            data={"ok": True, "ts": "1234567890.123456", "channel": "C123456"},
            headers={},
            status_code=200,
        )
        mock_slack_client.send_message.return_value = mock_message_response

        mock_reaction_response = SlackResponse(
            client=Mock(),
            http_verb="POST",
            api_url="https://slack.com/api/reactions.add",
            req_args={},
            data={"ok": True},
            headers={},
            status_code=200,
        )
        mock_slack_client.add_reaction_to_thread_by_channel_id.return_value = (
            mock_reaction_response
        )

        # Act
        run_action.main()

        # Assert
        mock_slack_client.send_message.assert_called_once_with(text="Test message")
        mock_slack_client.add_reaction_to_thread_by_channel_id.assert_called_once_with(
            channel_id="C123456", emoji_name="thumbsup", thread_ts="1234567890.123456"
        )
        mock_set_output.assert_any_call("message-ts", "1234567890.123456")
        mock_set_output.assert_any_call("channel-id", "C123456")

    @patch("run_action.set_github_output")
    @patch("run_action.SlackClient")
    @patch(
        "slack_reporter.constants.slack_constants.SlackConstants.SLACK_CHANNEL_NAME",
        "test-channel",
    )
    @patch.dict(
        os.environ,
        {
            "SLACK_MESSAGE": "Test message",
            "ADD_REACTION": "true",
            "SLACK_BOT_TOKEN": "xoxb-test-token",
            "SLACK_CHANNEL_NAME": "test-channel",
        },
    )
    def test_main_success_with_default_reaction(
        self, mock_slack_client_class, mock_set_output
    ):
        """Test successful main execution with default reaction emoji."""
        # Arrange
        mock_slack_client = Mock()
        mock_slack_client_class.return_value = mock_slack_client

        mock_message_response = SlackResponse(
            client=Mock(),
            http_verb="POST",
            api_url="https://slack.com/api/chat.postMessage",
            req_args={},
            data={"ok": True, "ts": "1234567890.123456", "channel": "C123456"},
            headers={},
            status_code=200,
        )
        mock_slack_client.send_message.return_value = mock_message_response

        mock_reaction_response = SlackResponse(
            client=Mock(),
            http_verb="POST",
            api_url="https://slack.com/api/reactions.add",
            req_args={},
            data={"ok": True},
            headers={},
            status_code=200,
        )
        mock_slack_client.add_reaction_to_thread_by_channel_id.return_value = (
            mock_reaction_response
        )

        # Act
        run_action.main()

        # Assert
        mock_slack_client.send_message.assert_called_once_with(text="Test message")
        mock_slack_client.add_reaction_to_thread_by_channel_id.assert_called_once_with(
            channel_id="C123456",
            emoji_name="white_check_mark",  # default emoji
            thread_ts="1234567890.123456",
        )

    @patch.dict(os.environ, {}, clear=True)
    @patch("sys.exit")
    def test_main_missing_message(self, mock_exit):
        """Test main function exits when SLACK_MESSAGE is missing."""
        # Act
        run_action.main()

        # Assert - Should call sys.exit at least once with code 1
        assert mock_exit.called
        mock_exit.assert_any_call(1)

    @patch.dict(os.environ, {"SLACK_MESSAGE": ""})
    @patch("sys.exit")
    def test_main_empty_message(self, mock_exit):
        """Test main function exits when SLACK_MESSAGE is empty."""
        # Act
        run_action.main()

        # Assert - Should call sys.exit at least once with code 1
        assert mock_exit.called
        mock_exit.assert_any_call(1)

    @patch("run_action.SlackClient")
    @patch.dict(os.environ, {"SLACK_MESSAGE": "Test message"})
    @patch("sys.exit")
    def test_main_slack_client_init_error(self, mock_exit, mock_slack_client_class):
        """Test main function handles SlackClient initialization error."""
        # Arrange
        mock_slack_client_class.side_effect = ValueError(
            "The SLACK_BOT_TOKEN environment variable was not set"
        )

        # Act
        run_action.main()

        # Assert
        mock_exit.assert_called_once_with(1)

    @patch("run_action.SlackClient")
    @patch(
        "slack_reporter.constants.slack_constants.SlackConstants.SLACK_CHANNEL_NAME",
        "test-channel",
    )
    @patch.dict(
        os.environ,
        {
            "SLACK_MESSAGE": "Test message",
            "SLACK_BOT_TOKEN": "xoxb-test-token",
            "SLACK_CHANNEL_NAME": "test-channel",
        },
    )
    @patch("sys.exit")
    def test_main_message_send_failure(self, mock_exit, mock_slack_client_class):
        """Test main function handles message send failure."""
        # Arrange
        mock_slack_client = Mock()
        mock_slack_client_class.return_value = mock_slack_client

        # Mock failed response
        mock_response = SlackResponse(
            client=Mock(),
            http_verb="POST",
            api_url="https://slack.com/api/chat.postMessage",
            req_args={},
            data={"ok": False, "error": "channel_not_found"},
            headers={},
            status_code=200,
        )
        mock_slack_client.send_message.return_value = mock_response

        # Act
        run_action.main()

        # Assert
        mock_exit.assert_called_once_with(1)

    @patch("run_action.SlackClient")
    @patch(
        "slack_reporter.constants.slack_constants.SlackConstants.SLACK_CHANNEL_NAME",
        "test-channel",
    )
    @patch.dict(
        os.environ,
        {
            "SLACK_MESSAGE": "Test message",
            "SLACK_BOT_TOKEN": "xoxb-test-token",
            "SLACK_CHANNEL_NAME": "test-channel",
        },
    )
    @patch("sys.exit")
    def test_main_no_response(self, mock_exit, mock_slack_client_class):
        """Test main function handles None response from Slack."""
        # Arrange
        mock_slack_client = Mock()
        mock_slack_client_class.return_value = mock_slack_client
        mock_slack_client.send_message.return_value = None

        # Act
        run_action.main()

        # Assert - Should call sys.exit at least once with code 1
        assert mock_exit.called
        mock_exit.assert_any_call(1)

    @patch("run_action.set_github_output")
    @patch("run_action.SlackClient")
    @patch(
        "slack_reporter.constants.slack_constants.SlackConstants.SLACK_CHANNEL_NAME",
        "test-channel",
    )
    @patch.dict(
        os.environ,
        {
            "SLACK_MESSAGE": "Test message",
            "ADD_REACTION": "true",
            "SLACK_BOT_TOKEN": "xoxb-test-token",
            "SLACK_CHANNEL_NAME": "test-channel",
        },
    )
    def test_main_reaction_failure_continues(
        self, mock_slack_client_class, mock_set_output
    ):
        """Test main function continues when reaction addition fails."""
        # Arrange
        mock_slack_client = Mock()
        mock_slack_client_class.return_value = mock_slack_client

        mock_message_response = SlackResponse(
            client=Mock(),
            http_verb="POST",
            api_url="https://slack.com/api/chat.postMessage",
            req_args={},
            data={"ok": True, "ts": "1234567890.123456", "channel": "C123456"},
            headers={},
            status_code=200,
        )
        mock_slack_client.send_message.return_value = mock_message_response

        # Mock failed reaction response
        mock_reaction_response = SlackResponse(
            client=Mock(),
            http_verb="POST",
            api_url="https://slack.com/api/reactions.add",
            req_args={},
            data={"ok": False, "error": "already_reacted"},
            headers={},
            status_code=200,
        )
        mock_slack_client.add_reaction_to_thread_by_channel_id.return_value = (
            mock_reaction_response
        )

        # Act - Should not raise an exception or exit
        run_action.main()

        # Assert
        mock_slack_client.send_message.assert_called_once_with(text="Test message")
        mock_slack_client.add_reaction_to_thread_by_channel_id.assert_called_once()
        mock_set_output.assert_any_call("message-ts", "1234567890.123456")
        mock_set_output.assert_any_call("channel-id", "C123456")

    @patch("run_action.set_github_output")
    @patch("run_action.SlackClient")
    @patch(
        "slack_reporter.constants.slack_constants.SlackConstants.SLACK_CHANNEL_NAME",
        "test-channel",
    )
    @patch.dict(
        os.environ,
        {
            "SLACK_MESSAGE": "Test message",
            "ADD_REACTION": "true",
            "SLACK_BOT_TOKEN": "xoxb-test-token",
            "SLACK_CHANNEL_NAME": "test-channel",
        },
    )
    def test_main_reaction_no_response(self, mock_slack_client_class, mock_set_output):
        """Test main function continues when reaction returns None."""
        # Arrange
        mock_slack_client = Mock()
        mock_slack_client_class.return_value = mock_slack_client

        mock_message_response = SlackResponse(
            client=Mock(),
            http_verb="POST",
            api_url="https://slack.com/api/chat.postMessage",
            req_args={},
            data={"ok": True, "ts": "1234567890.123456", "channel": "C123456"},
            headers={},
            status_code=200,
        )
        mock_slack_client.send_message.return_value = mock_message_response
        mock_slack_client.add_reaction_to_thread_by_channel_id.return_value = None

        # Act - Should not raise an exception or exit
        run_action.main()

        # Assert
        mock_slack_client.send_message.assert_called_once_with(text="Test message")
        mock_slack_client.add_reaction_to_thread_by_channel_id.assert_called_once()
        mock_set_output.assert_any_call("message-ts", "1234567890.123456")
        mock_set_output.assert_any_call("channel-id", "C123456")

    @patch("run_action.SlackClient")
    @patch.dict(os.environ, {"SLACK_MESSAGE": "Test message"})
    @patch("sys.exit")
    def test_main_unexpected_exception(self, mock_exit, mock_slack_client_class):
        """Test main function handles unexpected exceptions."""
        # Arrange
        mock_slack_client_class.side_effect = Exception("Unexpected error")

        # Act
        run_action.main()

        # Assert
        mock_exit.assert_called_once_with(1)

    @patch("run_action.set_github_output")
    @patch("run_action.SlackClient")
    @patch(
        "slack_reporter.constants.slack_constants.SlackConstants.SLACK_CHANNEL_NAME",
        "test-channel",
    )
    @patch.dict(
        os.environ,
        {
            "SLACK_MESSAGE": "Test message",
            "ADD_REACTION": "FALSE",  # Test case insensitive
            "SLACK_BOT_TOKEN": "xoxb-test-token",
            "SLACK_CHANNEL_NAME": "test-channel",
        },
    )
    def test_main_add_reaction_case_insensitive(
        self, mock_slack_client_class, mock_set_output
    ):
        """Test that ADD_REACTION environment variable is case insensitive."""
        # Arrange
        mock_slack_client = Mock()
        mock_slack_client_class.return_value = mock_slack_client

        mock_response = SlackResponse(
            client=Mock(),
            http_verb="POST",
            api_url="https://slack.com/api/chat.postMessage",
            req_args={},
            data={"ok": True, "ts": "1234567890.123456", "channel": "C123456"},
            headers={},
            status_code=200,
        )
        mock_slack_client.send_message.return_value = mock_response

        # Act
        run_action.main()

        # Assert
        mock_slack_client.send_message.assert_called_once_with(text="Test message")
        # Should not call add_reaction since ADD_REACTION is 'FALSE'
        mock_slack_client.add_reaction_to_thread_by_channel_id.assert_not_called()

    @patch("run_action.set_github_output")
    @patch("run_action.SlackClient")
    @patch(
        "slack_reporter.constants.slack_constants.SlackConstants.SLACK_CHANNEL_NAME",
        "test-channel",
    )
    @patch.dict(
        os.environ,
        {
            "SLACK_MESSAGE": "Test message",
            "SLACK_BOT_TOKEN": "xoxb-test-token",
            "SLACK_CHANNEL_NAME": "test-channel",
        },
    )
    def test_main_no_outputs_when_no_response_data(
        self, mock_slack_client_class, mock_set_output
    ):
        """Test main function doesn't set outputs when response lacks data."""
        # Arrange
        mock_slack_client = Mock()
        mock_slack_client_class.return_value = mock_slack_client

        mock_response = SlackResponse(
            client=Mock(),
            http_verb="POST",
            api_url="https://slack.com/api/chat.postMessage",
            req_args={},
            data={"ok": True},  # Missing ts and channel
            headers={},
            status_code=200,
        )
        mock_slack_client.send_message.return_value = mock_response

        # Act
        run_action.main()

        # Assert
        mock_slack_client.send_message.assert_called_once_with(text="Test message")
        # set_github_output should not be called since ts and channel are None
        mock_set_output.assert_not_called()


if __name__ == "__main__":
    pytest.main([__file__])
