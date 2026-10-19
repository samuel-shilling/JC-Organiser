#set root
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
root_path=Path(__file__).parent.resolve().parents[0]

#imports
from src.utility_functions import *
from src.config import *

# #can handle the revisions here
# def make_removals(path,name,date,WHICH,JC_DAYS):

#     #get the provisional schedule for this month
#     provisional_full=get_provisional_schedule("{}/data/{}/{}_provisional.csv".format(path, WHICH, WHICH))

#     #filter 
#     provisional_full,provisional_remaining=filter_provisional_schedule(provisional_full,JC_DAYS)

#     #handle removals



#main also needs updating