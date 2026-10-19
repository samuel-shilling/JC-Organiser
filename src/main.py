#set root
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
root_path=Path(__file__).parent.resolve().parents[0]

#imports
from src.provisional_schedule import *
from src.utilities import *
from src.config import *

#main function for generating the allocations (run daily)
def main_allocations():

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
    upcoming,executed=generate_and_save_provisional(upcoming, days_since_last_role, target_dates, ROLES, NUM_OF_SPEAKERS, 'group')
    print('\n newly generated upcoming:',upcoming) if executed==True else print('\n no new provisional generated')

    #save the updated provisional schedule
    save_updated_provisionals(root_path,upcoming,'group')

    return(upcoming)


#main function for removing people from the schedule if they are unavailable
def main_revisions_removal(removal_name,removal_role,removal_date):

    #get core data objects
    people,_=data_retrieval(root_path,'group')

    #get the provisional schedule (will return empty if it doesnt exist)
    provisional=get_provisional_schedule(root_path, 'group')

    #separate into past (confirmed) and future (upcoming) dates
    _,upcoming=filter_provisional_schedule(provisional)

    #ensure correct format
    check_member(removal_name,people)
    removal_role=check_role(removal_role)
    removal_date=clean_date(removal_date)

    #make changes
    upcoming=make_removals(upcoming,removal_name,removal_role,removal_date)
    #print('removal: {}, new schedule: {}'.format(removal_name,upcoming))

    #save the updated provisionals
    save_updated_provisionals(root_path,upcoming,'group')

    return(upcoming)

#main function for adding people from the schedule if they volunteer to take a role on a date
def main_revisions_removal(allocation_name,allocation_role,allocation_date):

    #get core data objects
    people,_=data_retrieval(root_path,'group')

    #get the provisional schedule (will return empty if it doesnt exist)
    provisional=get_provisional_schedule(root_path, 'group')

    #separate into past (confirmed) and future (upcoming) dates
    _,upcoming=filter_provisional_schedule(provisional)

    #ensure correct format
    check_member(allocation_name,people)
    removal_role=check_role(allocation_role)
    removal_date=clean_date(allocation_date)

    #make changes
    upcoming=manual_role_allocation(upcoming,allocation_name,allocation_role,allocation_date)
    print('manual allocation: {}, new schedule: {}'.format((allocation_name,allocation_role,allocation_date),upcoming))

    #save the updated provisionals
    save_updated_provisionals(root_path,upcoming,'group')

    return(upcoming)



#run the main function
if __name__ == "__main__":
    main()
