#set root
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
root_path=Path(__file__).parent.resolve().parents[0]

#imports
from src.config import *


#top level function to retrieve all central data objects
def data_retrieval(root_path,WHICH):

    #test the group directory exists
    ensure_directory_exists(root_path)

    #get list of JC members
    people=get_current_JC_members('{}/data/{}/{}_names.csv'.format(root_path,WHICH,WHICH))

    #get speaker history
    history=get_speaker_histories('{}/data/{}/{}_history.csv'.format(root_path,WHICH,WHICH))

    return(people,history)


#check the /data/group/ directory exists as this is ignored in github
def ensure_directory_exists(path):
    os.makedirs("{}/data/group/".format(path),exist_ok=True)

#get the meeting dates in a target month (could be this month, or next month)
def get_meeting_dates(JC_DAYS, period):
    days=pd.date_range(period.start_time, period.end_time, freq='D').normalize()
    return([d for d in days if d.day_name()==JC_DAYS])

#get the target month to generate the next set of JC days over 
def get_target_month_dates(JC_DAYS, today):
    #get JC dates for 3 consecutive months, find which month corresponds to the next schedule
    for offset in range(3):
        dates = get_meeting_dates(JC_DAYS, today.to_period('M')+offset)

        #get the dates in the month we do NOT already have a schedule for (where dates[0] is not yet in the past)
        if dates and dates[0]>=today:
            return(dates)

# #get the meeting dates this month (writes dates in ISO format)
# def get_meeting_dates_this_month(JC_DAYS):

#     #get current year and month
#     today=pd.Timestamp.today()
#     year=today.normalize().year
#     month=today.normalize().month

#     #empty list to save meeting dates to
#     meeting_dates_int=[]

#     #loop through every day this month
#     for day in range(1, calendar.monthrange(year, month)[1]+1):

#         date=pd.Timestamp(year=year, month=month, day=day)

#         #check if this date is a Thursday (or whichever day is selected for JC)
#         if date.strftime('%A')==JC_DAYS:
#             meeting_dates_int.append(date)

#     return(meeting_dates_int)


# #get the meeting dates this month (writes dates in ISO format)
# def get_meeting_dates_next_month(JC_DAYS):

#     #get current year and month
#     today=pd.Timestamp.today()
#     year=today.normalize().year
#     month=today.normalize().month

#     if month==12:
#         next_month=1
#         year=year+1
#     else:
#         next_month=month+1
#         year=year

#     #empty list to save meeting dates to
#     meeting_dates_int=[]

#     #loop through every day this month
#     for day in range(1, calendar.monthrange(year, next_month)[1]+1):

#         date=pd.Timestamp(year=year, month=next_month, day=day)

#         #check if this date is a Thursday (or whichever day is selected for JC)
#         if date.strftime('%A')==JC_DAYS:
#             meeting_dates_int.append(date)

#     return(meeting_dates_int)

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


def randomly_select_people_dates_and_roles_for_testing_revisions(df_updated_provisional,people):
    removal_info=df_updated_provisional.sample()
    removal_name,removal_role,removal_date=removal_info['name'].unique()[0],removal_info['role'].unique()[0],removal_info['date'].unique()[0]

    allocation_name=np.random.choice(np.setdiff1d(people,df_updated_provisional['name'].unique()))
    return(removal_name,removal_role,removal_date,allocation_name)

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