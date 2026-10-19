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
meeting_dates_this_month,meeting_dates_next_month,people,history,days_since_last_role=data_retrieval(root_path,WHICH,JC_DAYS)

#read in the provisional schedule (which may not yet exist for this month)
provisional_full=get_provisional_schedule(root_path,WHICH)

#separate the provisional schedule by month (current/next)
df_confirmed_current_month,df_remaining_current_month,df_remaining_next_month,df_updated_provisional=filter_provisional_schedule(provisional_full,meeting_dates_this_month,meeting_dates_next_month)

#test print
print('\n all provisional dates (this month and next):', provisional_full)
print('\n past dates in current month:', df_confirmed_current_month)
print('\n remaining dates in current month:', df_remaining_current_month)
print('\n next month only:', df_remaining_next_month)
print('\n all remaining dates (this month and next):', df_updated_provisional)

#save any provisional dates that have already passed to the history
save_confirmed_provisionals_to_history(root_path,df_confirmed_current_month,history,WHICH)

#generate new provisional for next month only if we are within 5 days of the first JC of that month and it has not already been generated
generate_provisional(df_remaining_current_month,df_remaining_next_month,days_since_last_role, meeting_dates_next_month, ROLES, NUM_OF_SPEAKERS,WHICH)

#test removals and manual allocations (using hard coded random selections for testing purposes)
removal_name,removal_role,removal_date,allocation_name=randomly_select_people_dates_and_roles_for_testing_revisions(df_updated_provisional,people)
if removal_name is not None and allocation_name is not None:
    df_updated_provisional=make_removals(df_updated_provisional,removal_name,removal_role,removal_date)
    print('removal: {}, new schedule: {}'.format(removal_name,df_updated_provisional))

    df_updated_provisional=manual_role_allocation(df_updated_provisional,allocation_name,removal_role,removal_date)
    print('manual allocation: {}, new schedule: {}'.format((allocation_name,removal_role,removal_date),df_updated_provisional))

#save the updated provisionals
save_updated_provisionals(root_path,df_updated_provisional,WHICH)

# #for dates that have passed and been confirmed: update the history (needs to run on a weekly basis)
# history_updated=save_confirmed_provisionals_to_history(root_path,provisional_full,history,meeting_dates,WHICH)
# #this is saving everytime!


