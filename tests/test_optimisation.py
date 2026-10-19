#set root
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
root_path=Path(__file__).parent.resolve().parents[0]

#imports
from src.optimise_schedule import *
from src.config import *
from src.utility_functions import *

#need to do:
# add name typo detection
# test for list of JC members and raise error if it doesnt exist
# test what happens if there is no speaker history


#which test to run? enter 'group' or 'dummy'
WHICH='group'

#get core data objects
meeting_dates,people,history,days_since_last_role=data_retrieval(root_path,WHICH,JC_DAYS)


#try for an existing provisional schedule, if it doesnt exist (for this month) generate a new one
try:
    provisional_full=get_provisional_schedule(root_path,meeting_dates,WHICH)
except:
    provisional_full=optimise_allocations(root_path,days_since_last_role, meeting_dates, ROLES, NUM_OF_SPEAKERS,WHICH)
print(provisional_full)

#update the history
save_confirmed_provisionals_to_history(root_path,provisional_full,history,meeting_dates,WHICH)


#make revisions
# provisional=get_provisional_schedule(path)




#if someone needs to reschedule then make sure the function does not overwrite allocations for previous meeting dates in this month which have already passed!