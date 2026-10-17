#set root
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
root_path=Path(__file__).parent.resolve().parents[0]

#imports
from src.config import *

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

        date = dt.date(year, month, day)

        #check if this date is a Thursday (or whichever day is selected for JC)
        if date.strftime('%A')==JC_DAYS:
            meeting_dates_int.append(date)

    return(meeting_dates_int)







#retrieve the provisional schedule for this month and process if it is for this month or not
def get_and_process_provisional_schedule(path):
    #get todays date
    today = pd.Timestamp.today()

    #read in attempt
    try:
        df=pd.read_csv(path)
        df['date']=pd.to_datetime(df['date'], format='%Y-%m-%d')
        df['name']=df['name'].str.strip()

    except FileNotFoundError:
        df = pd.DataFrame(columns=COLUMNS)
        df['date'] = pd.to_datetime(df['date'])

    #localize ISO date objects only
    dates=df.loc[df['date']!='whole month', 'date']

    #set boolean to flag if the provisional dates are for the current month or not
    current_month_exists = False
    for date in dates:
        if date.year==today.year and date.month==today.month:
            current_month_exists = True
            break

    #If no dates match, empty the dataframe
    if not current_month_exists:
        df==df.iloc[0:0].copy()

    return(df)



#simulate dummy data
def generate_dummy_data(path,SPEAKERS_PER_SESSION,JC_DAYS,COLUMNS,ROLES,NUM_OF_SPEAKERS):
    """Writes data/history.csv in the same format the real monthly file will use:

        date,name,role
        02/10/2025,C,chair
        02/10/2025,D,co-chair
        02/10/2025,E,speaker
        ... etc.

    - dates are DD/MM/YYYY, one row per person per role per date
    - chair and co-chair rows are dated on the first Thursday of their month
    - speaker rows are dated on the Thursday they spoke (2 per session)
    - covers the 12 months BEFORE the current month
    - two people (S and T) are "new members" with no history at all
    """

    #seed
    random.seed(42)

    #alphabetic letters as placeholders for peoples names
    people_with_history=list('ABCDEFGHIJKLMNOPQRST')
    JC_members=list('ABCDEFGHIJKLMNOPQRSTUVWXYZ')
    
    #sampling period over the last 12 months
    months_back=12
    
    queue=deque(random.sample(people_with_history, len(people_with_history)))
    this_month=pd.Timestamp.today().to_period('M')
    rows=[]

    for months_ago in range(months_back, 0, -1):
        period = this_month - months_ago
        meeting_days = pd.date_range(period.start_time, period.end_time, freq='W-{}'.format(JC_DAYS[:3]))

        #list to remove people from the pool if they have already had a role in a month
        used = []

        def next_person():
            while True:
                name = queue.popleft()
                queue.append(name)
                if name not in used:
                    used.append(name)
                    return name

        rows.append([meeting_days[0], next_person(), 'chair'])
        rows.append([meeting_days[0], next_person(), 'co-chair'])

        for days in meeting_days:
            for _ in range(SPEAKERS_PER_SESSION):
                rows.append([days, next_person(), 'speaker'])

    history = pd.DataFrame(rows, columns=['date', 'name', 'role'])
    history.to_csv('{}/data/dummy/dummy_history.csv'.format(path), index=False)

    print(history.head(12).to_string(index=False))
    print(f"\n{len(history)} rows written to data/dummy/dummy_history.csv")

    dummy_names=pd.DataFrame(JC_members, columns=['name'])
    dummy_names.to_csv('{}/data/dummy/dummy_names.csv'.format(path), index=False)