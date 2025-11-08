#!/usr/bin/env python3
"""
GitHub Action entrypoint for Slack Reporter.
This script handles the GitHub Action execution and outputs.
"""

import os
import sys
import logging
from pathlib import Path

# Add the action directory to Python path to import our modules
action_dir = Path(__file__).parent
sys.path.insert(0, str(action_dir))

from slack_reporter.clients.slack_client import SlackClient
from slack_reporter.constants.slack_constants import SlackConstants


def set_github_output(name: str, value: str):
    """Set GitHub Action output."""
    github_output = os.environ.get('GITHUB_OUTPUT')
    if github_output:
        with open(github_output, 'a') as f:
            f.write(f"{name}={value}\n")
    else:
        # Fallback for older runners
        print(f"::set-output name={name}::{value}")


def main():
    """Main entrypoint for the GitHub Action."""

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s: %(message)s'
    )
    logger = logging.getLogger(__name__)

    try:
        # Get inputs from environment
        message = os.environ.get('SLACK_MESSAGE')
        add_reaction = os.environ.get('ADD_REACTION', 'false').lower() == 'true'
        reaction_emoji = os.environ.get('REACTION_EMOJI', 'white_check_mark')

        if not message:
            logger.error("Message is required but not provided")
            sys.exit(1)

        # Initialize Slack client
        logger.info("Initializing Slack client...")
        slack_client = SlackClient()

        # Send message
        logger.info(f"Sending message to channel: {SlackConstants.SLACK_CHANNEL_NAME}")
        response = slack_client.send_message(text=message)

        if not response:
            logger.error("Failed to send message: No response")
            sys.exit(1)

        if not response.get('ok'):
            error_msg = response.get('error', 'Unknown error')
            logger.error(f"Failed to send message: {error_msg}")
            sys.exit(1)

        message_ts = response.get('ts')
        channel_id = response.get('channel')

        logger.info(f"✅ Message sent successfully! Timestamp: {message_ts}")

        # Add reaction if requested
        if add_reaction and message_ts:
            logger.info(f"Adding reaction: {reaction_emoji}")
            reaction_response = slack_client.add_reaction_to_thread_by_channel_id(
                channel_id=channel_id,
                emoji_name=reaction_emoji,
                thread_ts=message_ts
            )

            if reaction_response and reaction_response.get('ok'):
                logger.info("✅ Reaction added successfully!")
            else:
                logger.warning(f"Failed to add reaction: {reaction_response.get('error') if reaction_response else 'Unknown error'}")

        # Set GitHub Action outputs
        if message_ts:
            set_github_output('message-ts', message_ts)
        if channel_id:
            set_github_output('channel-id', channel_id)

        logger.info("🎉 Slack Reporter action completed successfully!")

    except ValueError as e:
        if "SLACK_BOT_TOKEN" in str(e):
            logger.error("❌ SLACK_BOT_TOKEN environment variable is required")
        else:
            logger.error(f"❌ Configuration error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()