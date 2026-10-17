#set root
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
root_path=Path(__file__).parent.resolve().parents[0]

#imports
from src.utilities import *
from src.config import *

#get a list of current JC members 
def get_current_JC_members(path):
    """
    must be a .csv which only consists of the folliwing:

    name
    Forename1 Surname1
    Forename2 Surname2
    Forename3 Surname3

    etc...
    
    """
    

    try:
        df=pd.read_csv(path)
    except:
        raise ValueError('Need injection list of members! This should be a .csv file with one column: name/ A/ B/ etc...')

    #convert to list
    result=df['name'].str.strip().tolist()
    return(result)

#get the speaker histories in the last 12 months and write file if it doesn't exist (this is the core dataframe of this algorithm)
def get_speaker_histories(path):
    """
    This is a history file that should already exist (but will be generated if not) in the form:

    date,name,role
    2025-10-02,Forename1 Surname1,chair
    2025-10-02,Forename2 Surname2,co-chair
    2025-10-02,Forename3 Surname3,speaker

    etc...

    """

    #it should exist and be able to read in
    #if it doesnt exist, make it
    try:
        df=pd.read_csv(path,parse_dates=['date'])
        df['name']=df['name'].str.strip()
    except FileNotFoundError:
        df=pd.DataFrame(columns=COLUMNS)
        df["date"]=pd.to_datetime(df["date"])


    return(df)


#get a dataframe containing the number of days since each person has last done each role
def compute_statistics(history, people,ROLES):

    #Todays date
    today=pd.Timestamp.today()

    #make an empty list to collect peoples stats under
    rows=[]

    #loop through everyone and get their statistics individually
    for name in people:

        #rolling dictionary to collate individual peoples stats under
        new_row={'name': name}

        #isolate the data for each person
        individual_history=history[history['name']==name]            

        #get stats for each role individually
        for role in ROLES:

            #all dates this person has done this role
            individual_history_per_role=individual_history[individual_history['role']==role]

            #compute days since they last did this role (if someone has never had this role give 1e6 days)
            if len(individual_history_per_role)==0:                         
                days_passed=1e6
            else:
                #get the most recent date
                most_recent_date=individual_history_per_role['date'].max()

                #find the time since then (we need to convert Today from series to a single value and normalize most recent date)
                days_passed=(today.normalize() - most_recent_date.normalize()).days

            #save the minimum number of days passed for this person
            new_row[role]=days_passed
            
        #save to the total set of rows
        rows.append(new_row)

    #convert to a dataframe for all people
    results=pd.DataFrame(rows)

    return(results)



#select people for each role this month (one chair and co-chair but multiple speakers), people already selected this month cannot be selected again - unless there are no other available people
def optimise_allocations(history, days_since_last_role, JC_DAYS, ROLES, NUM_OF_SPEAKERS):

    #get the meeting dates for this month
    meeting_dates_int=get_meeting_dates_this_month(history, JC_DAYS)

    #empty lists for the selections to be saved to
    allocations=[]
    already_used=[]
    chairs=[]

    #loop through each role
    for role in ROLES:  

        #set the selection criteria depending on the role
        if role=='chair' or role=='co-chair':
            num=1
            dates=['whole month']
        else:
            num=NUM_OF_SPEAKERS
            dates=meeting_dates_int

        for date in dates:
            #only consider people who haven't been given a role yet this month
            candidates=days_since_last_role[~days_since_last_role['name'].isin(already_used)]

            #if we've run out of people, start a new round (chairs stay excluded)
            if len(candidates)<num:
                already_used=chairs.copy()
                candidates=days_since_last_role[~days_since_last_role['name'].isin(already_used)]

            #shuffle first (so people with same days are re-ordered for sorting) then sort by role
            shuffled=candidates.sample(frac=1)
            sorted_candidates = shuffled.sort_values(by=role, ascending=False)

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

        results=pd.DataFrame(allocations, columns=['date', 'name', 'role'])


    return(results)

