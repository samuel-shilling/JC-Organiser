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

2. remove_speaker_from_date
   Use when the user explicitly requests that a member be removed from
   the schedule, for example because they are
   unavailable. This only works for the speaker role so you do not need to ask for clarification on which role

3. add_speaker_to_date
   Use when the user explicitly requests that a member be assigned as a speaker on a particular date. This only works for the speaker role so you do not need to ask for clarification on which role

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

- The member's name, exactly as the user typed it (a first name or surname alone is fine; the tool matches it against the group list).
- The journal club date.

Resolve these details using the current conversation and schedule wherever
possible. Do not ask the user to repeat information that is already
unambiguous. The only role that can be changed is speaker.

If any required detail remains ambiguous, ask a concise clarification
question before calling the modification tool.

NAMES AND ROLES

- Use names exactly as they appear from a user, including spelling and capitalisation, as name matching to the schedule or member list will be handled within the tools
- Do not invent names or assume that two similar names refer to the
  same person.
- Valid roles are chair, co-chair, and speaker. However the valid roles depend on which specific function you need to call (some only accept speakers for example)
- The tools look names up in the group list, so pass the name exactly as
  the user typed it (a first name alone is fine). Do not ask the user for
  a full name and do not guess a surname, unless a tool says a name is ambiguous or not found, relay that message and ask the user to clarify.
- If a role is unclear and cannot be resolved from context, ask for
  clarification, however if you are calling a function where the role is fixed then do not ask for clarification on the role
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
- If the user gives only a day number or a weekday ("the 29th", "next
  Thursday"), match it to one of the upcoming JC dates in CURRENT CONTEXT.
  Do not ask for the month or year when exactly one of them fits. Only ask
  if none or more than one fits.
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

AUTOMATED SCHEDULE GENERATION (INCLUDING THE NEXT SCHEDULE)

- You cannot generate new (or future) schedules. A background job in the Slack bot does it automatically at 07:00 each morning, once the next month's first JC is 5 days away or less, and posts the result in the channel. 
- If asked when the next schedule will be generated, explain this happens automatically when we are within 5 days of the next month's first JC session. Also emphasize that you can't manually run this workflow and that it happens automatically.


CANCELLING JOURNAL CLUB SESSIONS

- If someone asks to cancel a journal club session, you must say that this feature is not yet supported. Suggest that the person removes the speakers from that session instead (noting that this must be done for one speaker at a time as separate tasks)

SCHEDULE CHANGES VS CLUB MEMBERSHIP

- There are two different kinds of request:

A. Schedule change: a person is added to or removed from a talk slot on a
   specific date. These always involve a date (or "this week", "next JC", '29th',...). Use the tools for these. Examples include "I can't make the 29th", "put Sam down for the 5th", "swap John out of next week".

B. Membership change: a person joins or leaves the journal club itself.
   These involve words like new member and
   usually no date. You cannot do these. Reply briefly that membership is
   managed by the person who locally hosts the files for this project and suggest they contact them. Never call a tool for these. Examples: "add Anna to the journal club", "Tom is no longer part of journal club",
   "can you put a new student on the member list?"

- If a request mentions a person but it is unclear whether it is A or B
(for example "remove Tom" or "add Anna" with no date), do not call a tool.
Ask one short question: "Do you mean a talk on a specific date, or
joining/leaving the journal club itself?"

- Never treat a membership request as a schedule change, or the other way round.

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

def remove_speaker_from_date(removal_name: str, removal_date: str) -> str:
    """Remove a speaker from a journal club date in the provisional schedule. Good to use if someone is unavailable!

    The user cannot see this tool's output. Returns JSON with ok, a message, and (if ok) the updated "schedule", which is the finished Slack message. Reply with the message, then paste the schedule exactly as returned.
    If ok is false, explain the failure and do not claim anything changed.

    Args:
        removal_name: The member's name exactly as the user typed it (e.g. "Steve"). A first name alone is fine. Do not ask for a full name; the tool resolves it.
        removal_date: The journal club date in YYYY-MM-DD format
    """
    #hard coded for now as chairs cannot be changed yet due to saving into history quickly into the schedule whereas changes are only made to provisioanl
    removal_role='speaker'

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


def add_speaker_to_date(allocation_name: str, allocation_date: str) -> str:
    """Allocate a member to a role on a date.

    The user cannot see this tool's output. Returns JSON with ok, a message, and (if ok) the updated "schedule", which is the finished Slack message. Reply with the message, then paste the schedule exactly as returned. If ok is false, explain the failure and do not claim anything changed.

    Args:
        allocation_name: The member's name exactly as the user typed it (e.g. "Melzie"). A first name alone is fine. Do not ask for a full name; the tool resolves it.
        allocation_date: Date in YYYY-MM-DD format.

    Returns:
        JSON with ok (true/false) and a message
    """
    #hard coded for now as chairs cannot be changed yet due to saving into history quickly into the schedule whereas changes are only made to provisioanl
    allocation_role='speaker'

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



TOOLS = {f.__name__: f for f in (show_schedule, remove_speaker_from_date,add_speaker_to_date)}

#a function that wraps the prompt instructions and also adds the scheduled JC dates and todays JC dates to the prompt so the LLM does not get confused about dates and ask for clarificatoin when it is obvious what date someone might mean
def build_system_prompt():
    """Instructions plus today's date and the next few JC dates (so 'the 29th' always resolves)."""
    today=pd.Timestamp.today().normalize()
    days=pd.date_range(today,periods=60,freq='D')
    jc_dates=[d.strftime('%Y-%m-%d') for d in days if d.day_name()==JC_DAYS][:8]
    return(INSTRUCTIONS+f"\n\nCURRENT CONTEXT\n- Today is {today:%A %Y-%m-%d}.\n- Journal club is held on {JC_DAYS}s. Upcoming JC dates: {', '.join(jc_dates)}.\n")

#chat messages and prompts passed here (improved version which does not reply on the LLM to copy the function outputs, instead the function outputs which are structured are pasted directly and the llm only responds otherwise)
def ask_llm(messages, max_steps=5):
    """messages: per-thread list of chat messages (system prompt added here)."""

    #isolate messages individually in loops
    for _ in range(max_steps):

        #ask the model for a response (system prompt is added here on every call but is not stored in messages)
        response=client.chat(model=MODEL,messages=[{"role": "system", "content": build_system_prompt()}]+messages,tools=list(TOOLS.values()))

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