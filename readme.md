# Journal Club automatic scheduling algorithm

## Main features
1. A Python algorithm which fairly and deterministically generates a provisional JC schedule each month, removes people from the schedule if unavailable, and allocates people who volunteer (to replace someone who is unavailable for example)

2. A wrapper for an LLM which acts as an interface between users (JC members) and the Python algorithm. This interprets users messages and is programmed to run the corresponding function on their behalf

3. Slack Bot integration which is the medium in which the JC members can interact with the algorithm via the LLM.



## Installation instructions (Python algorithm)

1. Clone the github repo to get a local copy 
```bash
git clone https://github.com/samuel-shilling/JC-Organiser.git JC_organiser/
cd JC_organiser
```

2. (recommended) Setup a conda environment using the pre-packaged configuration to manage the pre-requisites
```bash
conda create --name JC_organiser python=3.12
conda activate JC_organiser
```

3. Verify the pre-requisites and the python version (should be 3.12.13)
```bash
python -m pip install -r requirements.txt
python -m pip list
python --version 
```

4. Copy (or edit) the example .env file
```bash
cp .env.example .env
```

5. (skippable if supplied with this data) Create mandatory initial data files (part 1)
- Go to JC_Organiser/data/group/ (make the group folder if needed)
- Make a plain text file called 'group_names.csv' and enter 'name' as the header followed by the JC member names 
- e.g.:
name
Forename1 Surname1
Forename2 Surname2

6. (skippable if supplied with this data) Create mandatory initial data files (part 2)
- Go to JC_Organiser/data/group/ (make the group folder if needed)
- Make a plain text file called 'group_history.csv' and enter data in the following format:
```text
date,           name,               role
YYYY-MM-DD,     Forename1 Surname1, Example_role
YYYY-MM-DD,     Forename2 Surname2, Example_role
```
- Example_role must be either 'speaker, chair, co-chair'
- name column entries must match name column entries in group_names.csv



## Installation instructions (LLM interface)

1. Install Ollama (open source LLM) to locally host the LLM interface 
- I have provided a summary of instructions for macOS/Linux below (otherwise see https://docs.ollama.com/quickstart)
```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama pull gemma4:e2b
```

2. (optional) Test Ollama
```bash
ollama run gemma4:e2b 
ollama show gemma4:e2b 
```

3. (optional) Test local run
```bash
python -m src.llm_interface
```

## Installation instructions (slack bot)
Note: full instructions at https://docs.slack.dev/tools/bolt-python/creating-an-app/

1. Go to 'build' in the Slack API (https://api.slack.com/apps/) and select 'create new app'

2. Select 'blank app' then select a name and allocate to your chosen workspace

3. Add the following scopes:
```bash
chat:write
app_mentions:read
im:history
users:read
```

4. Proceed to create and install and it should appear in your slack workspace

5. Go back to 'build' in the Slack API (https://api.slack.com/apps/) and scroll to 'app level tokens' and ensure that the following scope is there:
```bash
connections:write
```

6. Go to 'socket mode' and select 'enable' then select 'event subscriptions' and press 'enable' and click on 'subscribe to bot events' and after adding the following events (below) and then select 'save':
```bash
app_mention
message.im
```

7. Go to 'OAuth and permissions' and select 'reinstall to workspace' and copy the 'Bot user oauth token' beginning with 'xoxb' and add to .env as follows (**do not share this elsewhere**):
```py
SLACK_BOT_TOKEN=xoxb-...
```

8. Go back to 'basic information' then scroll to 'app level tokens' and click on the token name (blue coloured) and copy the token code starting `xapp' then add to .env as follows (**do not share this elsewhere**):
```py
SLACK_APP_TOKEN=xapp-...
```

9. (Note: you will need to repeat steps 7 and 8 if you change the bot scopes)

10. Whichever channel you want the Slack bot to operate in, go to the channel details and copy the channel ID and add it to the .env as follows:
```py
SLACK_CHANNEL_ID=xxx...
```

11. Activate the bot so it can communicate with the LLM and the algorithm
```bash
cd JC_organiser
conda activate JC_organiser
python -m src.slack_bot
```


## How to restart the project if your host PC shuts down

1. You will need to run the LLM, and initiate the slack bot
```bash
cd JC_organiser
conda activate JC_organiser
ollama pull gemma4:e2b
python -m src.slack_bot
```


2. To test locally (without slack):
```bash
cd JC_organiser
conda activate JC_organiser
python -m src.llm_interface
```


## When a new member has joined JC or a current member leaves

1. You will need to add (or remove) their name in group_names.csv (JC_Organiser/data/group/) but only do this once they are ready to give a talk as the algorithm will prioritise new members in new schedules

2. No need to touch group_history.csv




