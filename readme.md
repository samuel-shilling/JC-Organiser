**A tool to automate LU Astro JC**

This project is essentially a Python wrapper for an LLM and a Python scheduling algorithm integrated in Slack. The LLM acts as an interface between the group and the Python algorithm which handles the scheduling and optimization.


**Manual steps for first time usage**
1. Create injection member list
- Go to JC_Organiser/data/group/ (make the group folder if needed)
- Make a plain text file called 'group_names.csv' and enter 'name' as the header followed by the JC member names 
- e.g.:
name
Forename1 Surname1
Forename2 Surname2

2. Create injection speaker history list
- Go to JC_Organiser/data/group/ (make the group folder if needed)
- Make a plain text file called 'group_history.csv' and enter 'date,name,role' as the header row 
- Following rows must have dates in ISO format 'YYYY-MM-DD', names must be spelt the same as in group_names.csv, roles must be either 'speaker, chair, co-chair'

3. Run main


**How does it work**
1. The core Python scheduling algorithm
- This assigns roles (chairs, co-chairs, speakers) and optimises the schedule (ensure allocations are fair and balanced per person per role)
- This produces a standardised monthly schedule
- Provisional schedules for each month are saved in a temporary file and can be re-made if someone is unavailable
- Speaker and chair histories are saved to a permanent rolling file at the end of each month (when the provisional monthly schedules are confirmed)

2. The LLM interface
- This is supposed to interpret user requests, ask for more information (if necessary), and pass these into the Python algorithm. 
- This is wrapped inside Python functions which structure the AI generated content

3. The Slack Bot
- This is simply where the LLM interface is deployed so it can liaise between the group and the algorithms 





**Instructions for other users to edit the project**
1. Clone the github repo to get a local copy 
- git clone https://github.com/samuel-shilling/JC-Organiser.git JC_organiser/
- cd JC_organiser

2. (recommended) Setup a conda environment using the pre-packaged configuration to manage the pre-requisites
- conda create --name JC_organiser python=3.12
- conda activate JC_organiser

3. Verify the pre-requisites and the python version (should be 3.12.13)
- python -m pip install -r requirements.txt
- python -m pip list
- python --version 

4. Make changes 
- Note, if you use the conda environment (step 2), you will need to activate the environment everytime you revisit the project



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
