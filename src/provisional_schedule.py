#set root
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
root_path=Path(__file__).parent.resolve().parents[0]

#imports
from src.utilities import *
from src.config import *


#retrieve the provisional schedule for this month and process if it is for this month or not
def get_provisional_schedule(root_path,WHICH):

    #set local path
    path="{}/data/{}/{}_provisional.csv".format(root_path, WHICH, WHICH)

    #read in attempt, make an empty provisional file if failure
    try:
        df=pd.read_csv(path)
        df['date']=pd.to_datetime(df['date'], format='%Y-%m-%d')
        df['name']=df['name'].str.strip()

    except FileNotFoundError:
        df = pd.DataFrame(columns=COLUMNS)
        df['date'] = pd.to_datetime(df['date'])

    return(df)

# #separate the current provisional schedule by dates which have passed and have not passed
# def filter_provisional_schedule(provisional,meeting_dates_this_month,meeting_dates_next_month):

#     #get todays date
#     today=pd.Timestamp.today().normalize()

#     #get the dates remaining this month
#     remaining_dates=[d for d in meeting_dates_this_month if d>=today]

#     #select only the confirmed dates (that have already passed)
#     df_confirmed_current_month=provisional[provisional['date'] < today]
#     #df_confirmed_current_month=provisional[~provisional['date'].isin(remaining_dates)]

#     #select remaining dates for this month
#     df_remaining_current_month=provisional[provisional['date'].isin(remaining_dates)]

#     #select remaining dates for next month
#     df_remaining_next_month=provisional[provisional['date'].isin(meeting_dates_next_month)]

#     #select all remaining provisional dates (across current month and next months)
#     df_updated_provisional=provisional[provisional['date'].isin(meeting_dates_next_month + remaining_dates)]
    
#     return(df_confirmed_current_month,df_remaining_current_month,df_remaining_next_month,df_updated_provisional)

#separate the provisional schedule based on past and future dates
def filter_provisional_schedule(provisional):
    today=pd.Timestamp.today().normalize()
    confirmed=provisional[provisional['date']<today]
    upcoming=provisional[provisional['date']>=today]
    return(confirmed, upcoming)

#run daily to save confirmed provisionals to history file
def save_confirmed_provisionals_to_history(root_path,confirmed,history,WHICH):

    #only select provisional dates that have not already been saved (there should be none)
    unsaved_dates=np.setdiff1d(confirmed['date'].unique(),history['date'].unique())

    #select confirmed dates for merging
    for_merging=confirmed[confirmed['date'].isin(unsaved_dates)]

    #merge if there are dates, if not then the history is already up to date
    if len(for_merging)>0:
        #save the confirmed provisional dates to history
        history_updated=pd.concat([history,for_merging],ignore_index=True)

        #save updated history
        history_updated.to_csv("{}/data/{}/{}_history.csv".format(root_path, WHICH, WHICH), index=False, date_format='%Y-%m-%d')
    else:
        history_updated=history.copy()

    #return
    return(history_updated)

#save the updated provisional schedule (overwriting the previous one)
def save_updated_provisionals(root_path,df_updated_provisional,WHICH):

    #save the provisional allocations
    df_updated_provisional['date']=pd.to_datetime(df_updated_provisional['date'])
    df_updated_provisional.to_csv("{}/data/{}/{}_provisional.csv".format(root_path, WHICH, WHICH), index=False, date_format='%Y-%m-%d')



#select people for each role this month (one chair and co-chair but multiple speakers), people already selected this month cannot be selected again - unless there are no other available people
def generate_and_save_provisional(provisional_full, days_since_last_role, target_dates, ROLES, NUM_OF_SPEAKERS, WHICH):

    #todays date
    today=pd.Timestamp.today().normalize()

    #test if we are within x days of the first JC for the next schedule (x=5 for now)
    days_until_first_jc=(target_dates[0]-today).days
    within_timeframe= days_until_first_jc <= WINDOW_DAYS

    #test if the provisional schedule already exists
    already_generated=provisional_full['date'].isin(target_dates).any()

    #now test both conditions together and skip the generation if data does already exists (already_generated) or not within 5 days (within_timeframe)
    if already_generated or not within_timeframe:
        return(provisional_full,False)

    #empty lists for the selections to be saved to
    allocations=[]
    already_used=[]
    chairs=[]
    
    #loop through each role
    for role in ROLES:  

        #set the selection criteria depending on the role
        if role=='chair' or role=='co-chair':
            num=1
            dates=[target_dates[0]]
        else:
            num=NUM_OF_SPEAKERS
            dates=target_dates

        for date in dates:
            #only consider people who haven't been given a role yet this month
            candidates=days_since_last_role[~days_since_last_role['name'].isin(already_used)]



            #if we've run out of people, start a new round (chairs stay excluded)
            if len(candidates)<num:
                already_used=chairs.copy()
                candidates=days_since_last_role[~days_since_last_role['name'].isin(already_used)]

            #shuffle first (so people with same days are re-ordered for sorting) then sort by role
            shuffled=candidates.sample(frac=1)
            sorted_candidates = shuffled.sort_values(by=role, ascending=False,kind='stable')

            #take the specified number of names required from the top of the list (the longest time since they last did this role)
            chosen_names = sorted_candidates['name'].head(num).tolist()

            #for the people chosen, put them into already used list so they cannot be chosen again this month
            #only need to do this for speakers as chairs are only selected once
            for name in chosen_names:

                #save
                allocations.append([date, name, role])
                already_used.append(name)

                if role=='chair' or role=='co-chair':
                    chairs.append(name)

        new_provisionals=pd.DataFrame(allocations, columns=['date', 'name', 'role'])

    #append new allocations to existing provisional schedule (for remainder of current month)
    new_provisionals=pd.DataFrame(allocations, columns=COLUMNS)
    updated=pd.concat([provisional_full, new_provisionals], ignore_index=True)

    #save to disk
    save_updated_provisionals(root_path, updated, WHICH)

    return(updated,True)




#remove manually specified people (for their role and date) from the provisional schedule 
def make_removals(provisional_full,name,role,date):

    #date needs to be in pd.Timestamp formats

    #just slice the dataframe to exclude where the person is selected on which date for which role
    revised_provisional_full=provisional_full[~ ( (provisional_full['name']==name) &(provisional_full['role']==role) &(provisional_full['date']==date) )]

    return(revised_provisional_full)

#manually allocate people to the provisional schedule (need to manually specify person, role, date)
def manual_role_allocation(provisional_full,name,role,date):

    #just slice the dataframe to exclude where the person is selected on which date for which role
    new_row={'name':name,'role':role,'date':date}

    #merge the new allocation
    revised_provisional_full=pd.concat([provisional_full,pd.DataFrame([new_row])],ignore_index=True)

    #sort by date
    revised_provisional_full = revised_provisional_full.sort_values(by='date').reset_index(drop=True)

    return(revised_provisional_full)

