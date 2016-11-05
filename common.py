import json
import os.path
import re
import sys

CONFIG_FILE = '{0}/{1}'.format(
	os.path.dirname(os.path.realpath(__file__)),
	'config.json'
)

MANDATORY_CONFIG_KEY_SET = {'auth_token','dry_run','repository_type'}
GITHUB_AUTH_TOKEN_REGEXP = r'^[a-f0-9]{40}$'


def exit_error(message):
	sys.stderr.write('Error: {0}\n'.format(message))
	sys.exit(1)

def github_exit_error(message,api_request_error):
	exit_error('{0} Code: {1}'.format(
		message,
		api_request_error.http_code
	))

def load_config(config_key_addition_set = set()):
	# does config exist?
	if (not os.path.isfile(CONFIG_FILE)):
		exit_error('Unable to load {0}'.format(CONFIG_FILE))

	# open and parse JSON
	fp = open(CONFIG_FILE,'rb')
	config_data = json.load(fp)
	fp.close()

	# all config keys exist?
	for config_key in MANDATORY_CONFIG_KEY_SET.union(config_key_addition_set):
		if (config_key not in config_data):
			exit_error('Unable to find [{0}] config key in [{1}]'.format(config_key,CONFIG_FILE))

	# valid auth token value?
	if (not re.search(GITHUB_AUTH_TOKEN_REGEXP,config_data['auth_token'])):
		exit_error('Invalid GitHub authorization token specified in config')

	config_data_return = {}
	for config_key,config_value in config_data.items():
		config_key = str(config_key)

		if (config_key in {'dry_run'}):
			config_value = bool(config_value)

		else:
			config_value = str(config_value)

		config_data_return[config_key] = config_value

	# return config values
	return config_data_return
