import os, json
from dotenv import load_dotenv
from ollama import Client
from src.provisional_schedule import * 

load_dotenv()
client = Client(host=os.getenv("OLLAMA_HOST", "http://localhost:11434"))
MODEL = os.getenv("LLM_MODEL", "gemma4:e2b")

INSTRUCTIONS ="""
You are an assistant for a university astronomy journal club.

You can:
- Show the upcoming provisional schedule.
- Run the normal schedule-maintenance workflow.
- Remove a member from a role on a date.
- Allocate a member to a role on a date.

Rules:
- Use show_schedule when asked about the current schedule
- Only run functions that correspond to what the user is explicitly 
    requesting (for example, only run remove_member if someone says they are unavailable)
- Never claim that a change succeeded unless the relevant tool
  confirms success.
- Ask for clarification if a member gives a name, date or role that is ambiguous
    (names should be spelt correctly in the format of Forename Surname)
- Dates must be in YYYY-MM-DD format.
- Valid roles are chair, co-chair and speaker.
- Do not invent member names, dates or roles.
- Do not change a schedule merely because someone asks a question.
- Explain when a requested operation cannot be completed.
- Do not chat beyond the scope of a user request.
- Always message formally and politely and do not say anything that could be considered rude.
"""

def show_schedule() -> str:
    """Show the upcoming provisional journal club schedule.

    Returns:
        JSON with the upcoming date, name and role rows
    """
    prov = get_provisional_schedule(root_path, "group")
    _, up = filter_provisional_schedule(prov)
    display=up.copy()
    display= display.assign(date=display["date"].dt.strftime("%Y-%m-%d"))
    return(json.dumps({"ok": True, "schedule": display.to_dict("records")}))

def remove_person(removal_name: str, removal_role: str, removal_date: str) -> str:
    """Remove a member from a role on a date in the provisional schedule.
    Good to use if someone is unavailable!

    Args:
        name: Full name of the member as it appears in the schedule with capitalised first characters on Forename and Surname
        role: One of the following: chair, co-chair, speaker
        date: The journal club date in YYYY-MM-DD format

    Returns:
        JSON with ok (true/false) and a message
    """
    upcoming=main_revisions_removal(removal_name,removal_role,removal_date)
    return(json.dumps({"ok": True,"message": f"Removed {removal_name} from {removal_role} on {removal_date}.","schedule": upcoming.astype(str).to_dict("records")}))

def allocate_person(allocation_name: str, allocation_role: str, allocation_date: str) -> str:
    """Allocate a member to a role on a date.

    Args:
        allocation_name: Full name of the member as it appears in the schedule with capitalised first characters on Forename and Surname
        allocation_role: chair, co-chair, or speaker.
        allocation_date: Date in YYYY-MM-DD format.

    Returns:
        JSON with ok (true/false) and a message
    """

    upcoming=main_revisions_allocation(allocation_name,allocation_role,allocation_date)
    return(json.dumps({"ok": True,"message": f"Removed {allocation_name} from {allocation_role} on {allocation_role}.","schedule": upcoming.astype(str).to_dict("records")}))


TOOLS = {f.__name__: f for f in (show_schedule, remove_person,allocate_person)}

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