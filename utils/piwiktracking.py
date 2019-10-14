import json
import os,platform,requests

def logUse(action='launch'):
	payload = {'idsite': 3,  'rec': 1, 'send_image':0}
	payload['action_name'] = action
	cvar = {}
	cvar['1'] = ['OS', platform.system()]
	cvar['2'] = ['processor',platform.processor()]
	if cvar['1'][1] == 'Linux':
		cvar['1'][1] = platform.linux_distribution()[0]
		cvar['3'] = ['version', platform.linux_distribution()[1] ]
	else:
		cvar['3'] = ['version', platform.release() ]
	payload['_cvar'] = json.dumps(cvar)
	try:
		r = requests.get('http://nikhilvj.co.in/tracking/piwik.php', params=payload, verify=False, timeout=1)
	except requests.exceptions.RequestException as e:
		# print('exception',e)
		pass