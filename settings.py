import os,json
# import logging
# import tornado
# import tornado.template
# import os
# from tornado.options import define, options
#
# import environment
#
# # Make filepaths relative to settings.
# path = lambda root,*a: os.path.join(root, *a)
# ROOT = os.path.dirname(os.path.abspath(__file__))
#
# define("port", default=8888, help="run on the given port", type=int)
# define("config", default=None, help="tornado config file")
# define("debug", default=False, help="debug mode")
# tornado.options.parse_command_line()
#
# MEDIA_ROOT = path(ROOT, 'media')
# TEMPLATE_ROOT = path(ROOT, 'templates')
#
# # Deployment Configuration
#
# class DeploymentType:
#     PRODUCTION = "PRODUCTION"
#     DEV = "DEV"
#     SOLO = "SOLO"
#     STAGING = "STAGING"
#     dict = {
#         SOLO: 1,
#         PRODUCTION: 2,
#         DEV: 3,
#         STAGING: 4
#     }
#
# if 'DEPLOYMENT_TYPE' in os.environ:
#     DEPLOYMENT = os.environ['DEPLOYMENT_TYPE'].upper()
# else:
#     DEPLOYMENT = DeploymentType.SOLO
#
# settings = {}
# settings['debug'] = DEPLOYMENT != DeploymentType.PRODUCTION or options.debug
# settings['static_path'] = MEDIA_ROOT
# settings['cookie_secret'] = "your-cookie-secret"
# settings['xsrf_cookies'] = True
# settings['template_loader'] = tornado.template.Loader(TEMPLATE_ROOT)
#
# if options.config:
#     tornado.options.parse_config_file(options.config)

root = os.path.dirname(__file__) # needed for tornado
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