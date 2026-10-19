#set root
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
root_path=Path(__file__).parent.resolve().parents[0]

#imports
from src.config import *

#get a list of current JC members 
def get_current_JC_members(path):
    try:
        df=pd.read_csv(path)
    except:
        raise ValueError('Need injection list of members! Please refer to readme for instructions')

    #convert to list
    result=df['name'].str.strip().tolist()
    return(result)

#get the speaker histories in the last 12 months and write file if it doesn't exist (this is the core dataframe of this algorithm)
def get_speaker_histories(path):
    try:
        df=pd.read_csv(path)
        df['date']=pd.to_datetime(df['date'], format='%Y-%m-%d')
        df['name']=df['name'].str.strip()
    except FileNotFoundError:
        df=pd.DataFrame(columns=COLUMNS)
        df["date"]=pd.to_datetime(df["date"])
    return(df)


#check the /data/group/ directory exists as this is ignored in github
def ensure_directory_exists(path):
    os.makedirs("{}/data/group/".format(path),exist_ok=True)

#get the meeting dates this month (writes dates in ISO format)
def get_meeting_dates_this_month(JC_DAYS):

    #get current year and month
    today=pd.Timestamp.today()
    year=today.normalize().year
    month=today.normalize().month

    #empty list to save meeting dates to
    meeting_dates_int=[]

    #loop through every day this month
    for day in range(1, calendar.monthrange(year, month)[1]+1):

        date=pd.Timestamp(year=year, month=month, day=day)

        #check if this date is a Thursday (or whichever day is selected for JC)
        if date.strftime('%A')==JC_DAYS:
            meeting_dates_int.append(date)

    return(meeting_dates_int)


#retrieve the provisional schedule for this month and process if it is for this month or not
def get_provisional_schedule(root_path,dates_this_month,WHICH):

    #set local path
    path="{}/data/{}/{}_provisional.csv".format(root_path, WHICH, WHICH)

    #get todays date
    today = pd.Timestamp.today().normalize()

    #read in attempt
    try:
        df=pd.read_csv(path)
        df['date']=pd.to_datetime(df['date'], format='%Y-%m-%d')
        df['name']=df['name'].str.strip()

    except FileNotFoundError:
        df = pd.DataFrame(columns=COLUMNS)
        df['date'] = pd.to_datetime(df['date'])

    #set boolean to flag if the provisional dates are for the current month or not
    this_month=df[(df['date'].dt.year==today.year)&(df['date'].dt.month==today.month)]
    if len(this_month)==0:
        return(None)
    return(this_month)


def filter_provisional_schedule(df,dates_this_month):

    #get todays date
    today = pd.Timestamp.today().normalize()

    #get the dates remaining this month
    remaining_dates=[d for d in dates_this_month if d>=today]

    #reduce provisional schedule to only contain future dates
    df_historical=df[~df['date'].isin(remaining_dates)]
    df_remaining=df[df['date'].isin(remaining_dates)]

    return(df_historical,df_remaining)


def save_confirmed_provisionals_to_history(root_path,provisional,history,dates_this_month,WHICH):

    #filter privisional to get the confirmed dates and the remaining provisional dates (not needed here)
    confirmed_provisional_dates,_=filter_provisional_schedule(provisional,dates_this_month)

    #get the confirmed dates which have not already been saved to history (to prevent duplicate merges and saves)
    unsaved_dates=np.setdiff1d(confirmed_provisional_dates['date'].unique(),history['date'].unique())

    #select confirmed dates for merging
    for_merging=confirmed_provisional_dates[confirmed_provisional_dates['date'].isin(unsaved_dates)]

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


#can handle the revisions here
def make_removals(provisional_full,path,name,role,date,WHICH):

    #date needs to be in pd.Timestamp formats

    #just slice the dataframe to exclude where the person is selected on which date for which role
    revised_provisional_full=provisional_full[~ ( (provisional_full['name']==name) &(provisional_full['role']==role) &(provisional_full['date']==date) )]

    #save the provisional allocations
    revised_provisional_full['date']=pd.to_datetime(revised_provisional_full['date'])
    revised_provisional_full.to_csv("{}/data/{}/{}_provisional.csv".format(path, WHICH, WHICH), index=False, date_format='%Y-%m-%d')

    return(revised_provisional_full)


def manual_role_allocation(provisional_full,path,name,role,date,WHICH):

    #just slice the dataframe to exclude where the person is selected on which date for which role
    new_row={'name':name,'role':role,'date':date}

    #merge the new allocation
    revised_provisional_full=pd.concat([provisional_full,pd.DataFrame([new_row])],ignore_index=True)

    #sort by date
    revised_provisional_full = revised_provisional_full.sort_values(by='date').reset_index(drop=True)

    #save the provisional allocations
    revised_provisional_full['date']=pd.to_datetime(revised_provisional_full['date'])
    revised_provisional_full.to_csv("{}/data/{}/{}_provisional.csv".format(path, WHICH, WHICH), index=False, date_format='%Y-%m-%d')

    return(revised_provisional_full)



# #outdated- simulate dummy data
#if dummy, generate the data
# if WHICH!='group':
#     generate_dummy_data(root_path,SPEAKERS_PER_SESSION,JC_DAYS,COLUMNS,ROLES,NUM_OF_SPEAKERS)
# def generate_dummy_data(path,SPEAKERS_PER_SESSION,JC_DAYS,COLUMNS,ROLES,NUM_OF_SPEAKERS):
#     """Writes data/history.csv in the same format the real monthly file will use:

#         date,name,role
#         02/10/2025,C,chair
#         02/10/2025,D,co-chair
#         02/10/2025,E,speaker
#         ... etc.

#     - dates are DD/MM/YYYY, one row per person per role per date
#     - chair and co-chair rows are dated on the first Thursday of their month
#     - speaker rows are dated on the Thursday they spoke (2 per session)
#     - covers the 12 months BEFORE the current month
#     - two people (S and T) are "new members" with no history at all
#     """

#     #seed
#     random.seed(42)

#     #alphabetic letters as placeholders for peoples names
#     people_with_history=list('ABCDEFGHIJKLMNOPQRST')
#     JC_members=list('ABCDEFGHIJKLMNOPQRSTUVWXYZ')
    
#     #sampling period over the last 12 months
#     months_back=12
    
#     queue=deque(random.sample(people_with_history, len(people_with_history)))
#     this_month=pd.Timestamp.today().to_period('M')
#     rows=[]

#     for months_ago in range(months_back, 0, -1):
#         period = this_month - months_ago
#         meeting_days = pd.date_range(period.start_time, period.end_time, freq='W-{}'.format(JC_DAYS[:3]))

#         #list to remove people from the pool if they have already had a role in a month
#         used = []

#         def next_person():
#             while True:
#                 name = queue.popleft()
#                 queue.append(name)
#                 if name not in used:
#                     used.append(name)
#                     return name

#         rows.append([meeting_days[0], next_person(), 'chair'])
#         rows.append([meeting_days[0], next_person(), 'co-chair'])

#         for days in meeting_days:
#             for _ in range(SPEAKERS_PER_SESSION):
#                 rows.append([days, next_person(), 'speaker'])

#     history = pd.DataFrame(rows, columns=['date', 'name', 'role'])
#     history.to_csv('{}/data/dummy/dummy_history.csv'.format(path), index=False, date_format='%Y-%m-%d')

#     print(history.head(12).to_string(index=False))
#     print(f"\n{len(history)} rows written to data/dummy/dummy_history.csv")

#     dummy_names=pd.DataFrame(JC_members, columns=['name'])
#     dummy_names.to_csv('{}/data/dummy/dummy_names.csv'.format(path), index=False)