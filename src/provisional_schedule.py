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


#separate the provisional schedule based on past and future dates
def filter_provisional_schedule(provisional):
    today=pd.Timestamp.today().normalize()
    confirmed=provisional[provisional['date']<today]
    upcoming=provisional[provisional['date']>=today]
    # for testing:
    # confirmed=provisional.copy()
    return(confirmed, upcoming)

#run daily to save confirmed provisionals to history file
def save_confirmed_provisionals_to_history(root_path,confirmed,history,WHICH):

    #ensure consistent date formats (to be safe)
    confirmed['date']=pd.to_datetime(confirmed['date']).dt.normalize()
    history['date']=pd.to_datetime(history['date']).dt.normalize()

    #Start with the existing history
    history_updated = history.copy()

    #loop through each confirmed row, if any is NOT in history, append it (use a boolean to indicate if we need to save the results)
    confirm_merge=False
    for _, row in confirmed.iterrows():
        exists=( (history_updated['date']==row['date']) &(history_updated['name']==row['name']) & (history_updated['role']==row['role']) ).any()
        if not exists:
            history_updated.loc[len(history_updated)]=row 
            confirm_merge=True

    #merge if there are dates, if not then the history is already up to date
    if confirm_merge:
        #save updated history
        history_updated.to_csv("{}/data/{}/{}_history.csv".format(root_path, WHICH, WHICH), index=False, date_format='%Y-%m-%d')
    else:
        pass

    #return
    return(history_updated)

#save the updated provisional schedule (overwriting the previous one)
def save_updated_provisionals(root_path,df_updated_provisional,WHICH):

    #save the provisional allocations
    df_updated_provisional['date']=pd.to_datetime(df_updated_provisional['date'])
    df_updated_provisional.to_csv("{}/data/{}/{}_provisional.csv".format(root_path, WHICH, WHICH), index=False, date_format='%Y-%m-%d')



#select people for each role this month (one chair and co-chair but multiple speakers), people already selected this month cannot be selected again - unless there are no other available people
def generate_and_save_provisional(provisional_full, days_since_last_role, target_dates, ROLES, NUM_OF_SPEAKERS, WHICH):

    #for diagnostics
    print(days_since_last_role)
    
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

    #empty lists for the selections to be saved to (making sure people already scheduled provisionally this month cannot be used again)
    allocations=[]
    already_used=provisional_full['name'].unique().tolist() 
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
    date=pd.Timestamp(date).normalize()

    # #temp
    # print(repr(name), repr(role), repr(date), type(date))
    # print(provisional_full.dtypes)
    # print(provisional_full.assign(n=provisional_full['name']==name,r=provisional_full['role']==role,d=provisional_full['date']==date))

    #mask
    mask=( (provisional_full['name']==name) &(provisional_full['role']==role) &(provisional_full['date']==date) )

    #check
    if not mask.any():
        raise ValueError(f"No entry found for {name} as {role} on {date.date()}")

    #just slice the dataframe to exclude where the person is selected on which date for which role
    revised_provisional_full=provisional_full[~mask]


    
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

