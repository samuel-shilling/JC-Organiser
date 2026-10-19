import random
from collections import deque
import pandas as pd
import calendar
import datetime as dt
import numpy as np
import os


#absolute variables
SPEAKERS_PER_SESSION=2
JC_DAYS='Thursday'
COLUMNS=['date','name','role']
ROLES=['chair','co-chair','speaker']
NUM_OF_SPEAKERS=2
WINDOW_DAYS=5

