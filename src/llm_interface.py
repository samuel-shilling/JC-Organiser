import os, json
from dotenv import load_dotenv
from ollama import Client
from src.provisional_schedule import * 

load_dotenv()
client = Client(host=os.getenv("OLLAMA_HOST", "http://localhost:11434"))
MODEL = os.getenv("LLM_MODEL", "gemma4:e2b")

INSTRUCTIONS = """You are an assistant for a university astronomy journal club.
Use the tools to read or change the schedule. You may call several tools in a row.
Never claim a change happened unless a tool result has ok=true.
If a name, date or role is ambiguous, ask the user. Dates are YYYY-MM-DD."""

def show_schedule() -> str:
    """Show the upcoming provisional journal club schedule.

    Returns:
        JSON with the upcoming date, name and role rows
    """
    prov = get_provisional_schedule(root_path, "group")
    _, up = filter_provisional_schedule(prov)
    up = up.assign(date=up["date"].dt.strftime("%Y-%m-%d"))
    return json.dumps({"ok": True, "schedule": up.to_dict("records")})

def remove_person(name: str, role: str, date: str) -> str:
    """Remove a member from a role on a date in the provisional schedule.

    Args:
        name: Full name of the member as it appears in the schedule
        role: One of chair, co-chair, speaker
        date: The journal club date in YYYY-MM-DD format

    Returns:
        JSON with ok (true/false) and a message
    """
    return json.dumps({"ok": False, "message": "not implemented yet"})  #swap in remove_person_safe

TOOLS = {f.__name__: f for f in (show_schedule, remove_person)}

def ask_llm(messages, max_steps=5):
    """messages: per-thread list of chat messages (system prompt added here)."""
    for _ in range(max_steps):
        response = client.chat(
            model=MODEL,
            messages=[{"role": "system", "content": INSTRUCTIONS}] + messages,
            tools=list(TOOLS.values()),
        )
        messages.append(response.message)
        if not response.message.tool_calls:
            return response.message.content
        for call in response.message.tool_calls:
            try:
                result = TOOLS[call.function.name](**call.function.arguments)
            except Exception as e:
                result = json.dumps({"ok": False, "message": str(e)})
            messages.append({"role": "tool", "tool_name": call.function.name,
                             "content": str(result)})
    return "Sorry, I couldn't complete that request."

if __name__ == "__main__":
    history = []
    while True:
        history.append({"role": "user", "content": input("you> ")})
        print(ask_llm(history))