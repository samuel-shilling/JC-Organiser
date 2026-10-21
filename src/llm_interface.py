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
- The tools look names up in the group list, so pass the name exactly as
  the user typed it (a first name alone is fine). Do not ask the user for
  a full name and do not guess a surname, unless a tool says a name is ambiguous or not found, relay that message and ask the user to clarify.
- If a role is unclear and cannot be resolved from context, ask for
  clarification.
- Every user message starts with the sender's name in square brackets,
  for example "[John Smith]: I am not available".
- When the user says "I", "me", "my" or "myself" (for example "I am not
  available" or "put me down for the 12th"), the member is the sender. So
  use the name in the brackets as the member name. Never ask the user
  for their own name
- The bracketed name is not part of what the user typed. Do not repeat it
  in your replies.


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

AUTOMATED SCHEDULE GENERATION

- The journal club schedule is maintained automatically by a daily
background workflow in the Slack bot which generates the next provisional schedule.
- The workflow runs in Python every morning at 09:00 and once immediately
when the bot starts and only generates a future schedule if we are within 5 days
of the first session of the next month
- It also archives past sessions and generates a new provisional schedule
when required, normally near the end of the month.
- You cannot trigger this workflow manually. Do not attempt to run it
using another tool. And do not say you are capable of doing so.
- The slack bot will post this provisional schedule automatically once it has been generated, and you will then be able to interact with it as usual whenever users request that you do so
- If asked about future provisional schedules, explain that these are generated automatically 5 days before the first JC session of the new month so may not exist yet and will be posted automatically by the Slack bot
- Do not claim a new schedule has been generated unless you have
confirmation that the automated workflow completed successfully.

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
    """Get the upcoming provisional journal club schedule, including this month's chair and co-chair.

    The user cannot see this tool's output. Returns JSON where the "schedule" field is the finished Slack message. Paste it into your reply exactly as returned, without summarising or reformatting it.
    """
    provisional=get_provisional_schedule(root_path, "group")
    _, upcoming = filter_provisional_schedule(provisional)

    return(json.dumps({"ok": True, "schedule": format_schedule(upcoming)}))

def remove_person(removal_name: str, removal_role: str, removal_date: str) -> str:
    """Remove a speaker from a journal club date in the provisional schedule. Good to use if someone is unavailable!

    The user cannot see this tool's output. Returns JSON with ok, a message, and (if ok) the updated "schedule", which is the finished Slack message. Reply with the message, then paste the schedule exactly as returned.
    If ok is false, explain the failure and do not claim anything changed.

    Args:
        removal_name: Full name as it appears in the schedule, with capitalised Forename and Surname
        removal_role: Only "speaker" is supported (chairs cannot be removed)
        removal_date: The journal club date in YYYY-MM-DD format
    """
    #run the removal function, which will fail if the role is invalid (chairs not supported)
    try:

        #call the helper for the name matching first
        removal_name=resolve_member(removal_name,root_path)

        #run the function (which also checks the name again - slightly circular but doesnt matter)
        upcoming=main_revisions_removal(removal_name,removal_role,removal_date)
        return(json.dumps({"ok": True,"message": f"Removed {removal_name} from {removal_role} on {removal_date}.","schedule": format_schedule(upcoming)}))
    except Exception as e:
        traceback.print_exc()
        return(json.dumps({"ok": False,"message": str(e)}))


def allocate_person(allocation_name: str, allocation_role: str, allocation_date: str) -> str:
    """Allocate a member to a role on a date.

    The user cannot see this tool's output. Returns JSON with ok, a message, and (if ok) the updated "schedule", which is the finished Slack message. Reply with the message, then paste the schedule exactly as returned. If ok is false, explain the failure and do not claim anything changed.

    Args:
        allocation_name: Full name of the member as it appears in the schedule with capitalised first characters on Forename and Surname
        allocation_role: Currently only supported for one role, the speaker
        allocation_date: Date in YYYY-MM-DD format.

    Returns:
        JSON with ok (true/false) and a message
    """
    #run the allocation function, which will fail if the role is invalid (chairs not supported)
    try:
        #call the helper for the name matching first
        allocation_name=resolve_member(allocation_name,root_path)

        #run the function (which also checks the name again - slightly circular but doesnt matter)
        upcoming=main_revisions_allocation(allocation_name,allocation_role,allocation_date)
        return(json.dumps({"ok": True,"message": f"Allocated {allocation_name} as {allocation_role} on {allocation_date}.","schedule": format_schedule(upcoming)}))
    except Exception as e:
        traceback.print_exc()
        return(json.dumps({"ok": False,"message": str(e)}))



TOOLS = {f.__name__: f for f in (show_schedule, remove_person,allocate_person)}


#chat messages and prompts passed here (improved version which does not reply on the LLM to copy the function outputs, instead the function outputs which are structured are pasted directly and the llm only responds otherwise)
def ask_llm(messages, max_steps=5):
    """messages: per-thread list of chat messages (system prompt added here)."""

    #isolate messages individually in loops
    for _ in range(max_steps):

        #ask the model for a response (system prompt is added here on every call but is not stored in messages)
        response=client.chat(model=MODEL,messages=[{"role": "system", "content": INSTRUCTIONS}]+messages,tools=list(TOOLS.values()))

        #save the LLM reply to the thread history
        messages.append(response.message)

        #if the model didn't ask for any tools then it has just answered in text (e.g. a clarification question) so we are done
        if not response.message.tool_calls:
            return(response.message.content)

        #this will hold the finished message if a tool succeeds and returns a schedule 
        direct_reply=None

        #run each tool the model asked for
        for call in response.message.tool_calls:

            #call the matching python function from TOOLS with the arguments the model gave
            try:
                result=TOOLS[call.function.name](**call.function.arguments)

            #if the tool crashes, turn the error into an ok=false result so the model still gets told what happened
            except Exception as e:
                traceback.print_exc()
                result=json.dumps({"ok": False,"message": str(e)})

            #give the result back to the model as a tool message (this is how it learns what happened if it gets another turn)
            messages.append({"role": "tool", "tool_name": call.function.name, "content": str(result)})

            #convert the json string back into a dictionary so we can check it
            try:
                data=json.loads(result)

            #if the result isn't valid json then skip the shortcut for this tool call
            except (TypeError, ValueError):
                continue

            #if the tool succeeded and returned a schedule then build the reply ourselves instead of trusting the model to copy it
            #(remove/allocate return a message and a schedule, show_schedule only returns a schedule so the message is dropped by filter(None,...))
            if data.get("ok") and data.get("schedule"):
                direct_reply="\n\n".join(filter(None,[data.get("message"),data["schedule"]]))

        #if we built a reply then return it straight away so the model never writes the final message
        if direct_reply:

            #save what the user actually saw to the history, otherwise the thread would end on a tool result and confuse the model next turn
            messages.append({"role": "assistant", "content": direct_reply})
            return(direct_reply)

        #if we get here a tool failed (ok=false) so there is no schedule so direct_reply is None, the loop goes round until client.chat which will see the full message list (including the error in the tool message), this will prompt the model (as ok=false) to explain the failure message 

    #if all the steps are used up without an answer then give up
    return("Sorry, I couldn't complete that request.")

if __name__ == "__main__":
    history = []
    while True:
        history.append({"role": "user", "content": input("you> ")})
        print(ask_llm(history))