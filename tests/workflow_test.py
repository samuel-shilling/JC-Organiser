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
# add name typo detection
# test for list of JC members and raise error if it doesnt exist
# test what happens if there is no speaker history


#which test to run? enter 'group' or 'dummy'
WHICH='group'

#get core data objects
people,history=data_retrieval(root_path,WHICH)

#get the provisional schedule (will return empty if it doesnt exist)
provisional=get_provisional_schedule(root_path, WHICH)
print('\n full provisional:',provisional)

#separate into past (confirmed) and future (upcoming) dates
confirmed,upcoming=filter_provisional_schedule(provisional)
print('\n confirmed so far:',upcoming)
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


# #test removals and manual allocations (using hard coded random selections for testing purposes)
# removal_name,removal_role,removal_date,allocation_name=randomly_select_people_dates_and_roles_for_testing_revisions(df_updated_provisional,people)
# if removal_name is not None and allocation_name is not None:
#     df_updated_provisional=make_removals(df_updated_provisional,removal_name,removal_role,removal_date)
#     print('removal: {}, new schedule: {}'.format(removal_name,df_updated_provisional))

#     df_updated_provisional=manual_role_allocation(df_updated_provisional,allocation_name,removal_role,removal_date)
#     print('manual allocation: {}, new schedule: {}'.format((allocation_name,removal_role,removal_date),df_updated_provisional))

#save the updated provisionals
# save_updated_provisionals(root_path,df_updated_provisional,WHICH)

# #for dates that have passed and been confirmed: update the history (needs to run on a weekly basis)
# history_updated=save_confirmed_provisionals_to_history(root_path,provisional_full,history,meeting_dates,WHICH)
# #this is saving everytime!


