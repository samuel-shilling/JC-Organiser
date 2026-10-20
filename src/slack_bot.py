import os, re, sys, threading
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from src.llm_interface import ask_llm

#Load environment variables
load_dotenv()

SLACK_BOT_TOKEN=os.getenv("SLACK_BOT_TOKEN")
SLACK_APP_TOKEN=os.getenv("SLACK_APP_TOKEN")

if not SLACK_BOT_TOKEN or not SLACK_APP_TOKEN:
    raise ValueError("Missing SLACK_BOT_TOKEN or SLACK_APP_TOKEN in .env")


# nitialise Slack
app=App(token=SLACK_BOT_TOKEN)


# Store conversation history by channel and thread
conversations={}

# Allow only one LLM request at a time
llm_lock=threading.Lock()


def sender_name(user_id):
    """Return the Slack user's real name, falling back to their ID."""

    try:
        profile = app.client.users_info(user=user_id)["user"]["profile"]
        return profile.get("real_name") or user_id
    except Exception:
        return(user_id)


def handle(event, say, logger):
    """Pass a Slack message to the LLM and return its response."""

    # Ignore messages without text
    text = re.sub(
        r"<@[A-Z0-9]+>",
        "",
        event.get("text", ""),
    ).strip()

    if not text:
        return

    # Use threads in channels, but a single conversation in each DM
    is_dm=event.get("channel_type") == "im"

    thread_ts=event.get("thread_ts")

    conversation_key=(event["channel"], thread_ts)

    #Identify the sender
    user_id = event.get("user", "unknown")
    name = sender_name(user_id)

    try:
        with llm_lock:
            history = conversations.setdefault(conversation_key, [])

            #clear the history so LLM doesnt get overloaded
            if len(history) > 40:
                history.clear()
                
            history.append({"role": "user","content": f"[{name}]: {text}",})

            answer=ask_llm(history)

            if not answer:
                answer = "Sorry, I couldn't generate a response."

        say(text=answer, thread_ts=thread_ts)

    except Exception:
        logger.exception("Failed to process Slack message")

        #reset this thread's history
        conversations.pop(conversation_key, None)  
        say(text="Sorry, something went wrong processing your request.",thread_ts=thread_ts)


# Handle messages that mention the bot in a channel
@app.event("app_mention")
def on_mention(event, say, logger):
    handle(event, say, logger)


# Handle direct messages to the bot
@app.event("message")
def on_message(event, say, logger):

    if (event.get("channel_type") == "im" and not event.get("bot_id") and not event.get("subtype")):
        handle(event, say, logger)


if __name__ == "__main__":
    print("Starting the journal club Slack bot...")

    handler=SocketModeHandler(app, SLACK_APP_TOKEN)
    handler.start()
