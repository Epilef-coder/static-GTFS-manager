'''
GTFSserverfunctions.py
this file is to be inline included in the main script. Seriously, I do not want to keep declaring import statements everywhere.


import tornado.web
import tornado.ioloop
import json
import os
import time, datetime

import xmltodict
import pandas as pd
from collections import OrderedDict
import zipfile, zlib
from tinydb import TinyDB, Query
from tinydb.operations import delete
import webbrowser
from Cryptodome.PublicKey import RSA #uses pycryptodomex package.. disambiguates from pycrypto, pycryptodome
import shutil # used in fareChartUpload to fix header if changed
import pathlib
from math import sin, cos, sqrt, atan2, radians # for lat-long distance calculations
# import requests # nope, not needed for now
from json.decoder import JSONDecodeError # used to catch corrupted DB file when tinyDB loads it.
import signal, sys # for catching Ctrl+C and exiting gracefully.
import gc # garbage collector, from https://stackoverflow.com/a/1316793/4355695
import csv
import numpy as np
import io # used in hyd csv import

# to do: how to get these variables declared in the other file to be recognized here?

global uploadFolder
global xmlFolder
global logFolder
global configFolder
global dbFolder
global exportFolder

global sequenceDBfile
global passwordFile
global chunkRulesFile
global configFile

if __name__ == "__main__":
	print("Don't run this, run GTFSManager.py.")

'''
import pandas as pd

from settings import xmlFolder


###########################

##############################

def readStationsCSV(csvfile = xmlFolder + 'stations.csv'):
	'''
	This is for KMRL Metro file import
	'''
	stations = pd.read_csv(csvfile)
	
	# load up_id and down_id columns, but removing blank/null values. From https://stackoverflow.com/a/22553757/4355695
	upList = stations[stations['up_id'].notnull()]['up_id']
	downList = stations[stations['down_id'].notnull()]['down_id']

	mappedStopsList = set() # non-repeating list. Silently drops any repeating values getting added.
	mappedStopsList.update( upList )
	mappedStopsList.update( downList )
	return mappedStopsList

##############################

##############################

def get_sec(time_str):
	h, m, s = time_str.split(':')
	return int(h) * 3600 + int(m) * 60 + int(s)


def intcheck(s):
	s = s.strip()
	return int(s) if s else ''

#################################################3

######################


###################


##########################
# Redo the delete functions to accommodate multiple values. 
# For pandas it doesn't make any difference whether its one value or multiple

##########################

