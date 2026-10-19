#set root
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
root_path=Path(__file__).parent.resolve().parents[0]

#imports
from schedule_generation import *
from src.config import *
from utilities import *

#need to do:
# add name typo detection
# test for list of JC members and raise error if it doesnt exist
# test what happens if there is no speaker history


#which test to run? enter 'group' or 'dummy'
WHICH='group'

#get core data objects
# meeting_dates,people,history,days_since_last_role=data_retrieval(root_path,WHICH,JC_DAYS)

###first run all the absolute variables

#test the group directory exists
ensure_directory_exists(root_path)

#get the meeting dates for this month
meeting_dates_this_month=get_meeting_dates_this_month(JC_DAYS)

#get the meeting dates for next month
meeting_dates_next_month=get_meeting_dates_next_month(JC_DAYS)

#get list of JC members
people=get_current_JC_members('{}/data/{}/{}_names.csv'.format(root_path,WHICH,WHICH))

#get speaker history
history=get_speaker_histories('{}/data/{}/{}_history.csv'.format(root_path,WHICH,WHICH))

#get statistics
days_since_last_role=compute_statistics(history, people, ROLES)

#read in the provisional schedule (which may not yet exist for this month)
provisional_full=get_provisional_schedule(root_path,meeting_dates,WHICH)

#if the provisional does not yet exist (None type), generate one
if provisional_full is None:
    provisional_full=optimise_allocations(root_path,days_since_last_role, meeting_dates, ROLES, NUM_OF_SPEAKERS,WHICH)

#test print
print(provisional_full)

#make revisions (for removals) 
removal_info=provisional_full.sample()
removal_name,removal_role,removal_date=removal_info['name'].unique()[0],removal_info['role'].unique()[0],removal_info['date'].unique()[0]
if removal_name is not None:
    revised_provisional_full=make_removals(provisional_full,root_path,removal_name,removal_role,removal_date,WHICH)
print('removal: {}, new schedule: {}'.format(removal_info,revised_provisional_full))

#make revisions (for manual allocations)
allocation_name=np.random.choice(np.setdiff1d(people,revised_provisional_full['name'].unique()))
allocation_role,allocation_date=removal_role,removal_date
if allocation_name is not None:
    revised_provisional_full=manual_role_allocation(revised_provisional_full,root_path,allocation_name,allocation_role,allocation_date,WHICH)
print('manual allocation: {}, new schedule: {}'.format((allocation_name,allocation_role,allocation_date),revised_provisional_full))

#for dates that have passed and been confirmed: update the history (needs to run on a weekly basis)
history_updated=save_confirmed_provisionals_to_history(root_path,provisional_full,history,meeting_dates,WHICH)
#this is saving everytime!


