#set root
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
root_path=Path(__file__).parent.resolve().parents[0]

#imports
from schedule_generation import *
from utilities import *
from src.config import *

#main function
def main():

    #get core data objects
    people,history=data_retrieval(root_path,'group')

    #get the provisional schedule (will return empty if it doesnt exist)
    provisional=get_provisional_schedule(root_path, 'group')
    print('\n full provisional:',provisional)

    #separate into past (confirmed) and future (upcoming) dates
    confirmed,upcoming=filter_provisional_schedule(provisional)
    print('\n upcoming:',upcoming)

    #save the confirmed dates (past dates) to history (does nothing if history already up to date)
    history=save_confirmed_provisionals_to_history(root_path, confirmed, history, 'group')

    #compute statistics after history is updated (number of days since each people last did each role)
    days_since_last_role=compute_statistics(history, people, ROLES)   

    #finds the next month whose first JC is today or later (this is the month to schedule for)
    target_dates=get_target_month_dates(JC_DAYS, pd.Timestamp.today().normalize())

    #pick a chair, co-chair, and speakers for every JC date in the next schedule based on the fairest allocation (longest number of days since last time)
    #note, this is conditional! It will not generate a schedule unless we are within 5 days of the first scheduled JC, and if this schedule does not already exist (from a previous run for instance)
    upcoming,bool=generate_and_save_provisional(upcoming, days_since_last_role, target_dates, ROLES, NUM_OF_SPEAKERS, 'group')
    print('\n newly generated upcoming:',upcoming) if bool==True else print('\n no new provisional generated')

    #save the updated provisional schedule
    save_updated_provisionals(root_path,upcoming,'group')




    prompt = f'''
    This needs to be a prompt for the LLM to use to communicate between the algorithm (above code) and the group (it needs to send the algorithm output, re-run the code based on people in the group saying they are not available, add and remove people from the current JC member list)
    {final}

    '''

    # client = OpenAI()
    # response = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": prompt}])
    # result=response.choices[0].message.content

    #final='placeholder'

    #make removals and allocations (these need to be user input from the group to the LLM then into these variables)
    removal_name=None 
    allocation_name=None
    if removal_name is not None and allocation_name is not None:
        upcoming=make_removals(upcoming,removal_name,removal_role,removal_date)
        print('removal: {}, new schedule: {}'.format(removal_name,upcoming))

        upcoming=manual_role_allocation(upcoming,allocation_name,removal_role,removal_date)
        print('manual allocation: {}, new schedule: {}'.format((allocation_name,removal_role,removal_date),upcoming))

        #save the updated provisionals
        save_updated_provisionals(root_path,upcoming,'group')

    return(final)

#run the main function
if __name__ == "__main__":
    main()
