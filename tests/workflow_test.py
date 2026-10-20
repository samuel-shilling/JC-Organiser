#set root
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
root_path=Path(__file__).parent.resolve().parents[0]

#imports
from src.provisional_schedule import *
from src.config import *
from src.utilities import *

#need to do:
# test the workflow generation (end of month)
# need to add a function to cancel a JC session (wrapped by LLM) and ensure this does not re-generate when the daily workflow is ran!
# need to thoroughly docstring the code 





#which test to run? enter 'group' or 'dummy'
WHICH='group'

#get core data objects
people,history=data_retrieval(root_path,WHICH)

#get the provisional schedule (will return empty if it doesnt exist)
provisional=get_provisional_schedule(root_path, WHICH)
print('\n full provisional:',provisional)

#separate into past (confirmed) and future (upcoming) dates
confirmed,upcoming=filter_provisional_schedule(provisional)
print('\n upcoming:',upcoming)

#save the confirmed dates (past dates) to history
history=save_confirmed_provisionals_to_history(root_path, confirmed, history, WHICH)

#compute statistics after history is updated
days_since_last_role=compute_statistics(history, people, ROLES)   

#get the month where we do not yet have a schedule for
target_dates=get_target_month_dates(JC_DAYS, pd.Timestamp.today().normalize())

#if we are within 5 days of the first JC of the above month (and provisional data does not yet exist), generate provisional data
upcoming,bool=generate_and_save_provisional(upcoming, days_since_last_role, target_dates, ROLES, NUM_OF_SPEAKERS, WHICH)
print('\n newly generated upcoming:',upcoming) if bool==True else print('\n no new provisional generated')

#not needed in real workflow: test removals and manual allocations (using hard coded random selections for testing purposes)
removal_name,removal_role,removal_date,allocation_name=randomly_select_people_dates_and_roles_for_testing_revisions(upcoming,people)

#make removals and allocations
if removal_name is not None and allocation_name is not None:
    upcoming=make_removals(upcoming,removal_name,removal_role,removal_date)
    print('removal: {}, new schedule: {}'.format(removal_name,upcoming))

    upcoming=manual_role_allocation(upcoming,allocation_name,removal_role,removal_date)
    print('manual allocation: {}, new schedule: {}'.format((allocation_name,removal_role,removal_date),upcoming))

    #save the updated provisionals
    save_updated_provisionals(root_path,upcoming,WHICH)



