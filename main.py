from slackclient import SlackClient
import time
import re
import os
import krakenex

slack_client = SlackClient(os.environ.get('SLACK_BOT_TOKEN'))
kraken =krakenex.API(key=os.environ.get('KRAKEN_KEY'),secret=os.environ.get('KRAKEN_SECRET'))
print(kraken)
starterbot_id = None
# constants

RTM_READ_DELAY = 1 # 1 second delay between reading from RTM

POSITIONS_COMMAND = "positions"
BALANCE_COMMAND = "balance"
HELP_COMMAND = "help"
MENTION_REGEX = "^<@(|[WU].+?)>(.*)"

def parse_bot_commands(slack_events):
    """
        Parses a list of events coming from the Slack RTM API to find bot commands.
        If a bot command is found, this function returns a tuple of command and channel.
        If its not found, then this function returns None, None.
    """
    for event in slack_events:
        if event["type"] == "message" and not "subtype" in event:
            user_id, message = parse_direct_mention(event["text"])
            if user_id == starterbot_id:
                return message, event["channel"]
    return None, None

def parse_direct_mention(message_text):
    """
        Finds a direct mention (a mention that is at the beginning) in message text
        and returns the user ID which was mentioned. If there is no direct mention, returns None
    """
    matches = re.search(MENTION_REGEX, message_text)
    # the first group contains the username, the second group contains the remaining message
    return (matches.group(1), matches.group(2).strip()) if matches else (None, None)

def handle_command(command, channel):
    """
        Executes bot command if the command is known
    """
    # Default response is help text for the user
    default_response = "Not sure what you mean. Try*{}*.".format(HELP_COMMAND)

    # Finds and executes the given command, filling in response
    response = None
    # This is where you start to implement more commands!
    if command.startswith(BALANCE_COMMAND):
        response = kraken.query_private('Balance')['result']
        formatted_response = ""
        for k,v in response.items():
            formatted_response += k[1:]+ ': '+ v+'\n'


        # Sends the response back to the channel
        slack_client.api_call(
            "chat.postMessage",
            channel=channel,
            text=formatted_response or default_response
        )
    if command.startswith(POSITIONS_COMMAND):
        response = kraken.query_private('OpenPositions')['result']


        # Sends the response back to the channel
        slack_client.api_call(
            "chat.postMessage",
            channel=channel,
            text=response or "You have no open positions right now"
        )

    elif command.startswith(HELP_COMMAND):
        response = "Available commands:\n" + HELP_COMMAND+'\n'+BALANCE_COMMAND+'\n'+POSITIONS_COMMAND


        # Sends the response back to the channel
        slack_client.api_call(
            "chat.postMessage",
            channel=channel,
            text=response or default_response
        )

if __name__ == "__main__":
    if slack_client.rtm_connect(with_team_state=False):
        print("Starter Bot connected and running!")
        # Read bot's user ID by calling Web API method
        # `auth.test`
        starterbot_id = slack_client.api_call("auth.test")["user_id"]
        print("Bot id:",str(starterbot_id))
        while True:
            command, channel = parse_bot_commands(slack_client.rtm_read())
            if command:

                handle_command(command,channel)
            else:
                time.sleep(RTM_READ_DELAY)

