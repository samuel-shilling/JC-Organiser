# Changelog

All notable changes to this project are documented in this file.

This project follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] alpha - 2026-10-20

### The core Python scheduling workflow

#### Added 
- Defensive coding checks that raise error messages if incompatible arguments are passed

### Changed
- 

### Fixed
- 

### Removed
- 

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


