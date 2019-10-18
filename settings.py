import os,json
# Pyinstaller fix.
import sys
if getattr(sys, 'frozen', False):
    # https://pythonhosted.org/PyInstaller/runtime-information.html
    root = os.path.dirname(sys.executable)
else:
    root = os.path.dirname(__file__) # needed for tornado

STATIC_ROOT = os.path.join(root, 'website')
logFolder = os.path.join(root,'logs/')
uploadFolder = os.path.join(root,'uploads/')
xmlFolder = os.path.join(root,'xml_related/')
logFolder = os.path.join(root,'logs/')
configFolder = os.path.join(root,'config/')
dbFolder = os.path.join(root,'db/') # 12.5.18 new pandas DB storage
exportFolder = os.path.join(root,'export/') # 4.9.18 putting exports here now
sequenceDBfile = os.path.join(root,'db/sequence.json')
passwordFile = os.path.join(root,'pw/rsa_key.bin')
configFile = 'config.json'
chunkRulesFile = 'chunkRules.json'

debugMode = False # using this flag at various places to do or not do things based on whether we're in development or production

requiredFeeds = ['agency.txt','calendar.txt','stops.txt','routes.txt','trips.txt','stop_times.txt']
optionalFeeds = ['calendar_dates.txt','fare_attributes.txt','fare_rules.txt','shapes.txt','frequencies.txt','transfers.txt','feed_info.txt']
# load parameters from config folder
with open(configFolder + chunkRulesFile) as f:
    chunkRules = json.load(f)
with open(configFolder + configFile) as f:
    configRules = json.load(f)