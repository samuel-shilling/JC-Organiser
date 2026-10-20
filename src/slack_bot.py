import os, re, sys, threading
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from apscheduler.schedulers.background import BackgroundScheduler
from src.llm_interface import ask_llm
from src.main import daily_workflow
from src.utilities import format_schedule

#Load environment variables
load_dotenv()

SLACK_BOT_TOKEN=os.getenv("SLACK_BOT_TOKEN")
SLACK_APP_TOKEN=os.getenv("SLACK_APP_TOKEN")
SLACK_CHANNEL_ID=os.getenv("SLACK_CHANNEL_ID")

if not SLACK_BOT_TOKEN or not SLACK_APP_TOKEN:
    raise ValueError("Missing SLACK_BOT_TOKEN or SLACK_APP_TOKEN in .env")


# nitialise Slack
app=App(token=SLACK_BOT_TOKEN)


# Store conversation history by channel and thread
conversations={}

# Allow only one LLM request at a time
llm_lock=threading.Lock()

#get sender name so it understands what name to remove/add if someone makes a request for themselves (e.g. I am unavailable... etc.)
def sender_name(user_id):
    """Return the Slack user's real name, falling back to their ID."""

    try:
        profile = app.client.users_info(user=user_id)["user"]["profile"]
        return profile.get("real_name") or user_id
    except Exception:
        return(user_id)

#send the message to the LLM interface which should then run the python algorithm and send a response back
def handle(event, say, logger):
    """Pass a Slack message to the LLM and return its response."""

    #Ignore messages without text
    text=re.sub(r"<@[A-Z0-9]+>","",event.get("text", ""),).strip()

    if not text:
        return

    #Use threads in channels, but a single conversation in each DM
    #is_dm=event.get("channel_type") == "im"

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
        say(text="Sorry, something went wrong processing your request (start diagnostics from line 83 in slack_bot.py).",thread_ts=thread_ts)


#Handle messages that mention the bot in a channel
@app.event("app_mention")
def on_mention(event, say, logger):
    handle(event, say, logger)


#Handle direct messages to the bot
@app.event("message")
def on_message(event, say, logger):

    if (event.get("channel_type") == "im" and not event.get("bot_id") and not event.get("subtype")):
        handle(event, say, logger)


###BELOW: daily tasks which are scheduled without any user or LLM input
# These are needed to run the daily workflow once a day to check the following:
#   # if past provisional dates need to be saved to history
#   # if a new schedule needs to be generated and if so, then generate a new schedule


#set the time at which we want to run the daily workflow (see run_daily) and queue the job
def start_scheduler():
    """Run the daily job every morning at 09:00, and once immediately on startup (catches up if the bot was off)."""
    scheduler=BackgroundScheduler()
    scheduler.add_job(run_daily, "cron", hour=9, minute=0, id="daily_workflow",coalesce=True, misfire_grace_time=6*3600,next_run_time=dt.datetime.now())
    scheduler.start()
    return(scheduler)

#call the daily_workflow function from main.poy
def run_daily():
    """Archive past sessions and generate the next schedule if it is due (safe to run repeatedly)."""
    try:
        #same lock as the chat handler, so the csv files are never edited by two things at once
        with llm_lock:
            upcoming, generated = daily_workflow()
 
        if generated and SLACK_CHANNEL_ID:
            app.client.chat_postMessage(channel=SLACK_CHANNEL_ID, text=format_schedule(upcoming,title="*New journal club schedule generated:*"))
    except Exception:
        logging.exception("Daily workflow failed")


if __name__ == "__main__":
    print("Slack bot was previously offline but is now starting up and will begin by running the daily workflow...")
    start_scheduler()

    handler=SocketModeHandler(app, SLACK_APP_TOKEN)
    handler.start()
