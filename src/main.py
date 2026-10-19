#set root
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
root_path=Path(__file__).parent.resolve().parents[0]

#imports
from src.optimise_schedule import *
from src.utility_functions import *
from src.config import *

#main function
def main():

    #get core data objects
    meeting_dates,people,history,days_since_last_role=data_retrieval(root_path,'group',JC_DAYS)

    #try to read an existing provisional schedule (for this month), if it doesnt exist (for this month) generate a new one
    try:
        provisional_full=get_provisional_schedule(root_path,meeting_dates,'group')
    except:
        provisional_full=optimise_allocations(root_path,days_since_last_role, meeting_dates, ROLES, NUM_OF_SPEAKERS,'group')
    print(provisional_full)

    prompt = f'''
    This needs to be a prompt for the LLM to use to communicate between the algorithm (above code) and the group (it needs to send the algorithm output, re-run the code based on people in the group saying they are not available, add and remove people from the current JC member list)
    {final}

    '''

    # client = OpenAI()
    # response = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": prompt}])
    # result=response.choices[0].message.content

    #final='placeholder'
    return(final)

#run the main function
if __name__ == "__main__":
    main()
