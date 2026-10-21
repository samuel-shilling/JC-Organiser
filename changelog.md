# Changelog

All notable changes to this project are documented in this file and dates are formatted: YYYY-MM-DD

This changelog roughly follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.0] alpha - 2026-10-21

### Added
- Name matching function ```resolve_member``` which helps the LLM connect peoples names to peoples messages (i.e. 'I am not available' = 'Forename Surname is not available') and is wrapped in ```remove_person``` and ```allocate_person``` 
- ```utilities.build_schedule_message_for_slack_bot``` which is a wrapper of ```format_schedule``` and is accecssible to the slack bot (previously only the LLM can access formatted data output)

### Changed
- ```run_daily``` now calls the new ```build_schedule_message_for_slack_bot``` from ```utilities.py``` in order to structure the schedule message in a similar fashion to how the LLM does (via ```format_schedule```)
- ```ask_llm``` modified so that the LLM does not interpret function outputs, which are already structured, and it will return the function output directly. The LLM will only produce a reply if there is no viable function output (i.e. ask for more information)
- Improved traceback messages on errors

### Fixed
- A bug in ```build_schedule_message_for_slack_bot``` where a dependency was not carried over to the call in ```run_daily```

## [0.2.0] alpha - 2026-10-20

### Added
- Automated daily workflow in the Slack bot (APScheduler): runs every morning at 09:00 and once on startup (to catch up if the bot was offline). This basically calls the main workflow function from v0.1.0 (which was already there but just not implemented). It archives past sessions to history and generates the next provisional schedule when it is within 5 days of the first JC session
- New environment (.venv.example) variable `SLACK_CHANNEL_ID` so the bot posts a start-up message and posts the new schedule whenever one is generated
- Added a utility function `format_schedule()` to structure content so they are returned as nicely formatted Slack text 
- Conversation history is cleared once it exceeds 40 messages, so the LLM does not get overloaded

### Changed
- `main_allocations()` renamed to `daily_workflow()`, which now returns `(upcoming, generated)` so new generations can be checked and confirmed
- Can now show the chair and co-chair in `show_schedule` as these are taken from history instead of relying on the provisional dates
- LLM system prompt replaced (with help of an LLM) and is now more concise and accurate about capabilities and understands that the schedule generation is automated and cannot be triggered by the LLM (only show schedule, remove, and manually allocate can)
- Tool errors are flagged with an `ok: false` return with a message, and tracebacks are printed to the terminal 
- Failed function calls now show diagnostic messages in the slack channel 
- Provisional schedule generation now excludes anyone already in the existing provisional schedule 
- Readme restructured into separate Python, LLM and Slack setup sections, with new sections on restarting the bot and on adding or removing members
- `apscheduler` in requirements.txt capped at version `<4` to prevent API changes affecting this project

### Fixed
- `.env.example` now uses `OLLAMA_HOST` (previously `LLM_BASE_URL`, which the code never read)
- Multiple bugs in functions fixed throughout the various scripts

### Known limitations
- (low priority) Chair and co-chair changes are not supported
- (low priority) Schedule generation runs only via the daily job. This is intended, but is rigid and not changeable
- (mid priority) No way to cancel a JC session yet (the daily workflow may also regenerate this session?)



## [0.1.0] prototype - 2026-10-20

### The core Python scheduling workflow
- An end-to-end scheduling workflow capable of the following core functionalities: archive past sessions, update role-allocation based on fairness statistics, generate new provisional schedules when required (within 5 days of the first JC session for the next/current month), and apply manual schedule revisions (manual removals and allocations)

### The LLM
- Integrated a locally hosted LLM (Ollama) interpret natural-language requests from users and calls 'tools' to engage with the scheduling engine functions (which requires data in specific formats) with access to tools which show the schedule, remove someone, and allocate someone

### The Slack bot
- Integrated LLM interface with Slack using socket mode (no public URL needed), with interaction possible via tagging the bot in the channel

### Known limitations
- Only a handful of the core functions of the Python algorithm are implemented in the LLM and Slack bot (show schedule, remove someone, and allocate someone) 
- Some of these tools require an existing provisional schedule. Although automated schedule generation is implemented in the Python workflow, it is not yet callable as an LLM tool or run as a scheduled background task by the Slack bot 
- Provisional schedules are constantly updated so any past dates are removed and saved into a separate file, which means show schedule (which only loads the provisional schedule) does not show previous plans (i.e. who spoke last week)



