#set root
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
root_path=Path(__file__).parent.resolve().parents[0]

#imports
from src.optimise_schedule import *
from src.config import *
from src.utilities import *

#which test to run? enter 'group' or 'dummy'
WHICH='group'

#test the group directory exists
ensure_directory_exists(root_path)

#need to add name typo detection


#need to simulate future months (IF THERE ARE LESS THAN 6 MONTHS)


#if dummy, generate the data
if WHICH=='group':
    generate_dummy_data(root_path,SPEAKERS_PER_SESSION,JC_DAYS,COLUMNS,ROLES,NUM_OF_SPEAKERS)

#get list of JC members
people=get_current_JC_members('{}/data/{}/{}_names.csv'.format(root_path,WHICH,WHICH))

#read in speaker histories
history=get_speaker_histories('{}/data/{}/{}_history.csv'.format(root_path,WHICH,WHICH))

#get the meeting dates this month
meeting_dates_int=get_meeting_dates_this_month(history, JC_DAYS)

#get statistics
days_since_last_role=compute_statistics(history, people, ROLES)

#optimise allocations
final=optimise_allocations(history, days_since_last_role, JC_DAYS, ROLES, NUM_OF_SPEAKERS)

#print
print(final)

#need to add provisional schedule file saving (and then eventually comitting to the rolling history)

