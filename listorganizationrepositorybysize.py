#!/usr/bin/env python

import common
import githubapi

ORGANIZATION_CONFIG_KEY = 'organization'


def get_organization_repository_size_sorted_list(auth_token,organization_name,repository_type):
	repository_list = []

	try:
		for repository_item in githubapi.get_organization_repository_list(auth_token,organization_name,repository_type):
			repository_list.append((
				str(repository_item['git_url']),
				int(repository_item['size'])
			))

	except githubapi.APIRequestError as e:
		common.github_exit_error(
			'Unable to fetch repository list for organization {0}, type {1}.'.format(
				organization_name,
				repository_type
			),
			e
		)

	# sort list by repository size descending
	return sorted(
		repository_list,
		key = lambda item: item[1],
		reverse = True
	)

def main():
	# load config from file
	config_data = common.load_config(
		config_key_addition_set = { ORGANIZATION_CONFIG_KEY }
	)

	config_auth_token = config_data['auth_token']

	# fetch repository names/sizes of the specified type
	print('Fetching repository list by size:')
	repository_list = get_organization_repository_size_sorted_list(
		config_auth_token,
		config_data[ORGANIZATION_CONFIG_KEY],
		config_data['repository_type']
	)

	# output list, repository URI/size - tab separated
	for repository_uri,repository_size in repository_list:
		print('{0}\t{1}'.format(repository_uri,repository_size))


if (__name__ == '__main__'):
	main()
