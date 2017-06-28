import argparse
import json
import os.path
import re
import sys

REPOSITORY_FILTER_REGEXP = re.compile(r'^[*/A-Za-z0-9_.-]+$')

MANDATORY_CONFIG_KEY_SET = {'auth_token','repository_type'}
CONFIG_FILE = '{0}/{1}'.format(
	os.path.dirname(os.path.realpath(__file__)),
	'config.json'
)

GITHUB_AUTH_TOKEN_REGEXP = re.compile(r'^[a-f0-9]{40}$')


def exit_error(message):
	sys.stderr.write('Error: {0}\n'.format(message))
	sys.exit(1)

def github_api_exit_error(message,api_request_error):
	exit_error('{0} Code: {1}'.format(
		message,
		api_request_error.http_code
	))

def read_arguments():
	parser = argparse.ArgumentParser()

	parser.add_argument(
		'--commit',
		action = 'store_true',
		help = 'apply changes back to GitHub, otherwise dry run only'
	)

	parser.add_argument(
		'--include',
		help = 'repository include filter - defaults to \'everything\'',
		nargs = '*'
	)

	parser.add_argument(
		'--exclude',
		help = 'repository exclude filter',
		nargs = '*'
	)

	arg_list = parser.parse_args()

	# validate repository include/exclude filters
	def validate_filter_list(filter_type,filter_list):
		if (filter_list is None):
			# no work
			return

		for filter_item in filter_list:
			if (not REPOSITORY_FILTER_REGEXP.search(filter_item)):
				# invalid filter characters
				exit_error('Invalid {0} filter of [{1}]'.format(filter_type,filter_item))

	validate_filter_list('include',arg_list.include)
	validate_filter_list('exclude',arg_list.exclude)

	# return arguments
	return (
		not arg_list.commit, # 'dry run' mode
		# if no include filters, add the default of 'everything'
		['*'] if (arg_list.include is None) else arg_list.include,
		[] if (arg_list.exclude is None) else arg_list.exclude
	)

def load_config(config_key_addition_set = set()):
	config_key_set = MANDATORY_CONFIG_KEY_SET.union(config_key_addition_set)

	# does config exist?
	if (not os.path.isfile(CONFIG_FILE)):
		exit_error('Unable to load {0}'.format(CONFIG_FILE))

	# open and parse JSON config
	fp = open(CONFIG_FILE,'rb')
	config_data = json.load(fp)
	fp.close()

	for config_key in config_key_set:
		# config keys exist?
		if (config_key not in config_data):
			exit_error('Unable to find [{0}] config key in [{1}]'.format(config_key,CONFIG_FILE))

		# ensure value is not empty
		if (not config_data[config_key].strip()):
			exit_error('Config key [{0}] cannot be empty'.format(config_key))

	# validate auth token format
	if (not GITHUB_AUTH_TOKEN_REGEXP.search(config_data['auth_token'])):
		exit_error('Invalid GitHub authorization token specified in config')

	# return expected config items from config data
	return {
		str(extract_key): str(config_data[extract_key]).strip()
		for extract_key in config_key_set
	}

class RepositoryFilter:
	def __init__(self,include_list,exclude_list):
		# convert include/exclude filters to regular expressions
		self.include_list = RepositoryFilter._build(self,include_list)
		self.exclude_list = RepositoryFilter._build(self,exclude_list)

	def accept(self,name):
		# if exclude match - reject
		if (RepositoryFilter._is_match(self,self.exclude_list,name)):
			return False

		# if include match - accept
		if (RepositoryFilter._is_match(self,self.include_list,name)):
			return True

		# otherwise reject
		return False

	def _build(self,source_list):
		build_list = []
		for filter_item in source_list:
			# escape meta characters, set wildcard/start/end metas
			build_list.append(
				re.compile('^{0}$'.format(
					re.escape(filter_item)
						.replace('\*','.+?')
				))
			)

		return build_list

	def _is_match(self,filter_list,name):
		for item in filter_list:
			if (item.search(name)):
				# matched
				return True

		# no match
		return False
