#set root
import sys, traceback
from pathlib import Path
import datetime as dt
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
root_path=Path(__file__).parent.resolve().parents[0]

#imports
from src.provisional_schedule import *
from src.utilities import *
from src.config import *
from src.main import *

load_dotenv()
client = Client(host=os.getenv("OLLAMA_HOST", "http://localhost:11434"))
MODEL = os.getenv("LLM_MODEL", "gemma4:e2b")


INSTRUCTIONS = """
You are an assistant for a university astronomy journal club.

Your job is to answer schedule questions and make requested changes using
the available Python tools. The tools and their results are the source of
truth for all schedule information. You have access to some Python functions which can handle requests (see AVAILABLE TOOLS below). There are some functions you do not have access to, such as generating a new schedule for a future month, as this happens automatically 5 days before the first JC session of that month.

AVAILABLE TOOLS

1. show_schedule
   Use when the user asks to see, check, or discuss the current upcoming
   provisional schedule.

2. remove_person
   Use when the user explicitly requests that a member be removed from
   a particular role on a particular date, for example because they are
   unavailable.

3. allocate_person
   Use when the user explicitly requests that a member be assigned to
   a particular role on a particular date.

TOOL USAGE RULES

- Use only the tool needed to fulfil the user's request.
- Never modify the schedule in response to a question, hypothetical,
  suggestion, or request for information alone.
- Never call a modification tool unless the user has requested the change.
- Do not call show_schedule unnecessarily when a modification tool
  already returns the updated schedule.
- Do not invent tool results or claim that an operation succeeded
  without confirmation from the tool.
- If a tool returns ok=false, explain the failure using its message.
  Do not claim the operation succeeded.
- If a tool raises an error or returns an unexpected result, explain
  that the operation could not be confirmed.
- Do not claim to have displayed or updated a schedule without including
  the relevant schedule returned by the tool.

REQUIRED INFORMATION FOR CHANGES

To remove or allocate a member, you need:
- The member's full name.
- The role: chair, co-chair, or speaker.
- The journal club date.

Resolve these details using the current conversation and schedule wherever
possible. Do not ask the user to repeat information that is already
unambiguous.

If any required detail remains ambiguous, ask a concise clarification
question before calling the modification tool.

NAMES AND ROLES

- Use names exactly as they appear in the schedule, including spelling
  and capitalisation.
- Do not invent names or assume that two similar names refer to the
  same person.
- Valid roles are chair, co-chair, and speaker.
- If a role is unclear and cannot be resolved from context, ask for
  clarification.

DATES

- Tool arguments must use YYYY-MM-DD format, including leading zeros.
- Interpret relative dates and ordinal dates using the current date,
  the schedule, and relevant conversation context.
- For example, "the 8th" may refer to the 8th of the month established
  by the current schedule or conversation.
- Do not guess the month or year if multiple interpretations remain
  plausible.
- Resolve dates already established in the conversation without asking
  the user to repeat them.
- Do not confuse the date of a journal club meeting with the date on
  which a chair assignment was recorded.

SCHEDULE DISPLAY

- When show_schedule returns a schedule, reproduce the schedule string
  exactly as returned by the tool.
- Preserve all dates, names, roles, ordering, and formatting.
- Do not invent, omit, summarise, or independently reconstruct entries.
- If the tool reports that no upcoming sessions are scheduled, relay
  that result accurately.

CONVERSATION CONTEXT

- Use previous messages to resolve references such as "that person",
  "the same date", or "make them co-chair instead".
- Treat earlier details as relevant only when their meaning remains clear.
- If the user changes a previously specified name, role, or date,
  use the latest unambiguous instruction.
- Never assume that a proposed change has already been applied.
- Do not treat information from an earlier conversation as proof that
  the current schedule has not changed.

RESPONSE STYLE

- Be concise, professional, and polite.
- For clarification, ask only for the missing or ambiguous information.
- For successful changes, state what changed and include the updated
  schedule returned by the tool.
- For failures, explain what could not be completed and do not imply
  that the schedule was changed.
- Do not discuss implementation details unless the user asks.
"""

def show_schedule() -> str:
    """Show the upcoming provisional journal club schedule.

    Returns:
        JSON with the upcoming date, name and role rows
    """
    provisional=get_provisional_schedule(root_path, "group")
    _, upcoming = filter_provisional_schedule(provisional)

    #format the dates
    #upcoming["date"]=upcoming["date"].dt.strftime("%Y-%m-%d")

    #get the chairs (they are saved for the first JC of each month so they may not be in the upcoming file)
    if 'chair' not in upcoming['role'].unique() and 'co-chair' not in upcoming['role'].unique():

        #get core data objects (note history will contain lots of past dates)
        _,history=data_retrieval(root_path,'group')

        #select the most recent chair and co-chairs
        chair_rows=history[history['role'].isin(['chair','co-chair'])]
        current_chairs=chair_rows[chair_rows['date']==chair_rows['date'].max()]

        #merge with upcoming (remaining talks)
        upcoming=pd.concat((upcoming,current_chairs))


    return(json.dumps({"ok": True, "schedule": format_schedule(upcoming)}))

def remove_person(removal_name: str, removal_role: str, removal_date: str) -> str:
    """Remove a member from a role on a date in the provisional schedule.
    Good to use if someone is unavailable!

    Args:
        removal_name: Full name of the member as it appears in the schedule with capitalised first characters on Forename and Surname
        removal_role: One of the following: chair, co-chair, speaker
        removal_date: The journal club date in YYYY-MM-DD format

    Returns:
        JSON with ok (true/false) and a message
    """
    #run the removal function, which will fail if the role is invalid (chairs not supported)
    try:
        upcoming=main_revisions_removal(removal_name,removal_role,removal_date)
        return(json.dumps({"ok": True,"message": f"Removed {removal_name} from {removal_role} on {removal_date}.","schedule": format_schedule(upcoming)}))
    except Exception as e:
        traceback.print_exc()
        return(json.dumps({"ok": False,"message": str(e)}))


def allocate_person(allocation_name: str, allocation_role: str, allocation_date: str) -> str:
    """Allocate a member to a role on a date.

    Args:
        allocation_name: Full name of the member as it appears in the schedule with capitalised first characters on Forename and Surname
        allocation_role: chair, co-chair, or speaker.
        allocation_date: Date in YYYY-MM-DD format.

    Returns:
        JSON with ok (true/false) and a message
    """
    #run the allocation function, which will fail if the role is invalid (chairs not supported)
    try:
        upcoming=main_revisions_allocation(allocation_name,allocation_role,allocation_date)
        return(json.dumps({"ok": True,"message": f"Allocated {allocation_name} as {allocation_role} on {allocation_date}.","schedule": format_schedule(upcoming)}))
    except Exception as e:
        traceback.print_exc()
        return(json.dumps({"ok": False,"message": str(e)}))



TOOLS = {f.__name__: f for f in (show_schedule, remove_person,allocate_person)}

def ask_llm(messages, max_steps=5):
    """messages: per-thread list of chat messages (system prompt added here)."""
    for _ in range(max_steps):
        response = client.chat(model=MODEL,messages=[{"role": "system", "content": INSTRUCTIONS}] + messages,tools=list(TOOLS.values()))
        messages.append(response.message)
        if not response.message.tool_calls:
            return response.message.content
        for call in response.message.tool_calls:
            try:
                result=TOOLS[call.function.name](**call.function.arguments)
            except Exception as e:
                traceback.print_exc()
                result=json.dumps({"ok": False,"message": str(e)})
            messages.append({"role": "tool", "tool_name": call.function.name, "content": str(result)})
    return("Sorry, I couldn't complete that request.")

if __name__ == "__main__":
    history = []
    while True:
        history.append({"role": "user", "content": input("you> ")})
        print(ask_llm(history))