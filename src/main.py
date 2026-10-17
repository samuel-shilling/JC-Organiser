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

    #test the group directory exists
    ensure_directory_exists(root_path)

    #get list of JC members
    people=get_current_JC_members('{}/data/{}/{}_names.csv'.format(root_path,'group','group'))

    #read in speaker histories
    history=get_speaker_histories('{}/data/{}/{}_history.csv'.format(root_path,'group','group'))

    #get statistics
    days_since_last_role=compute_statistics(history, people, ROLES)

    #optimise allocations
    final=optimise_allocations(days_since_last_role, JC_DAYS, ROLES, NUM_OF_SPEAKERS,'group')
    print(final)

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
