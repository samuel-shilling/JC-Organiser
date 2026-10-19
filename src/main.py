#set root
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
root_path=Path(__file__).parent.resolve().parents[0]

#imports
from schedule_generation import *
from utilities import *
from src.config import *

# #main function
# def main():

#     #get core data objects
#     meeting_dates,people,history,days_since_last_role=data_retrieval(root_path,'group',JC_DAYS)

#     #read in the provisional schedule (which may not yet exist for this month)
#     provisional_full=get_provisional_schedule(root_path,meeting_dates,WHICH)

#     #if the provisional does not yet exist (None type), generate one
#     if provisional_full is None:
#         provisional_full=optimise_allocations(root_path,days_since_last_role, meeting_dates, ROLES, NUM_OF_SPEAKERS,WHICH)
#     print(provisional_full)

#     prompt = f'''
#     This needs to be a prompt for the LLM to use to communicate between the algorithm (above code) and the group (it needs to send the algorithm output, re-run the code based on people in the group saying they are not available, add and remove people from the current JC member list)
#     {final}

#     '''

#     # client = OpenAI()
#     # response = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": prompt}])
#     # result=response.choices[0].message.content

#     #final='placeholder'
#     return(final)

# #run the main function
# if __name__ == "__main__":
#     main()
