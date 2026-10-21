import random
from collections import deque
import pandas as pd
import calendar
import datetime as dt
import numpy as np
import difflib
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from apscheduler.schedulers.background import BackgroundScheduler
import os, json
from dotenv import load_dotenv
from ollama import Client

#absolute variables
SPEAKERS_PER_SESSION=2
JC_DAYS='Thursday'
COLUMNS=['date','name','role']
ROLES=['chair','co-chair','speaker']
NUM_OF_SPEAKERS=2
WINDOW_DAYS=7



