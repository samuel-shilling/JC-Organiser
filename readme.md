This project is essentially a Python scheduling algorithm for LU Astro. JC. 

**Main features**
1. Deterministically fairly allocate each JC role to each member automatically and generate a rolling schedule

2. Make revisions to the schedule (currently semi-automatic as it requires someone to volunteer to cover if someone else is unavailable)

3. Use a separately installed LLM interface (currently tested with Ollama) to liaise between the algorithm and the JC group members



**Installation instructions (including LLM)**

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

5. Separately install Ollama (open source LLM) to locally host the LLM interface 
- I have provided a summary of instructions for macOS/Linux below (otherwise see https://docs.ollama.com/quickstart)
```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama pull gemma4:e2b
```


6. (optional) Test Ollama
```bash
ollama run gemma4:e2b 
ollama show gemma4:e2b 
```

7. (skippable if supplied with this data) Create mandatory initial data files (part 1)
- Go to JC_Organiser/data/group/ (make the group folder if needed)
- Make a plain text file called 'group_names.csv' and enter 'name' as the header followed by the JC member names 
- e.g.:
name
Forename1 Surname1
Forename2 Surname2

8. (skippable if supplied with this data) Create mandatory initial data files (part 2)
- Go to JC_Organiser/data/group/ (make the group folder if needed)
- Make a plain text file called 'group_history.csv' and enter data in the following format:
```text
date,           name,               role
YYYY-MM-DD,     Forename1 Surname1, Example_role
YYYY-MM-DD,     Forename2 Surname2, Example_role
```
- Example_role must be either 'speaker, chair, co-chair'
- name column entries must match name column entries in group_names.csv


9. Run locally
```bash
python -m src.llm_interface
```

**Slack bot setup instructions**
Note: full instructions at https://docs.slack.dev/tools/bolt-python/creating-an-app/

1. 



**How to re-active the project (if local machine is restarted for example)**
 1. Activate the virtual environment
 ```bash
 cd JC_organiser
 conda activate JC_organiser
 ```

 2. Restart the LLM interface
 ```bash
 python -m src.llm_interface
 ```





**Temporary notes to self (not useful to anyone else)**

1. CV notes
- Developing my first LLM application for task allocation and scheduling 
- Skill: Wrapping LLMs to automate daily tasks for humans
- Skill: Processing AI generated data into structured formats

2. Project startup commands
[make empty repo on git]
conda create --name JC_organiser python=3.12
conda activate JC_organiser
pip install numpy pandas dill openai 
pip freeze > requirements.txt
