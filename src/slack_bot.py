import os, re, sys, threading
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from src.llm_interface import ask_llm

load_dotenv()
app = App(token=os.environ["SLACK_BOT_TOKEN"])

#channel, thread -> chat history
conversations = {}          

#the CSV files and local LLM handle one request at a time
llm_lock = threading.Lock()  

def sender_name(user_id):
    try:
        profile = app.client.users_info(user=user_id)["user"]["profile"]
        return profile.get("real_name") or user_id
    except Exception:
        return user_id  # works without users:read, just less helpful

def handle(event, say):
    text = re.sub(r"<@[A-Z0-9]+>", "", event.get("text", "")).strip()
    if not text:
        return
    is_dm = event.get("channel_type") == "im"
    thread_ts = None if is_dm else (event.get("thread_ts") or event["ts"])
    key = (event["channel"], thread_ts)

    with llm_lock:
        history = conversations.setdefault(key, [])
        history.append({"role": "user",
                        "content": f"[{sender_name(event['user'])}]: {text}"})
        answer = ask_llm(history)
    say(text=answer, thread_ts=thread_ts)

@app.event("app_mention")
def on_mention(event, say):
    handle(event, say)

@app.event("message")
def on_message(event, say):
    # DMs only; channels are handled through @mentions
    if event.get("channel_type") == "im" and not event.get("bot_id") and not event.get("subtype"):
        handle(event, say)

if __name__ == "__main__":
    SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"]).start()