#!/usr/bin/env python

import common
import githubapi


def get_repository_name_wiki_status_set(auth_token,repository_type):
	repository_set = set()

	try:
		for repository_item in githubapi.get_user_repository_list(auth_token,repository_type):
			# display repository name/wiki status
			print('{0}{1}'.format(
				repository_item['full_name'],
				' - Wiki enabled'
					if (repository_item['has_wiki'])
					else ''
			))

			# add as tuple to set
			repository_set.add((
				repository_item['full_name'],
				repository_item['has_wiki']
			))

	except githubapi.APIRequestError as e:
		common.github_exit_error('Unable to fetch repository list for type {0}.'.format(repository_type),e)

	return repository_set

def filter_repository_wiki_enabled(repository_set):

	def filter(filter_set,item):
		# add item to reduced set if wiki enabled
		repository_name,has_wiki = item
		if (has_wiki):
			filter_set.add(repository_name)

		return filter_set

	return reduce(filter,repository_set,set())

def disable_respository_wiki(auth_token,repository_full_name):
	# split repository into owner/repository parts
	owner,repository = tuple(repository_full_name.split('/'))

	try:
		githubapi.update_repository_properties(
			auth_token,
			owner,repository,
			wiki = False
		)

	except githubapi.APIRequestError as e:
		common.github_exit_error('Unable to disable wiki for repository {0}/{1}.'.format(owner,repository),e)

def main():
	# load config from file
	config_data = common.load_config()
	config_auth_token = config_data['auth_token']

	# fetch repository names and wiki status of the specified type
	print('Scanning repository list:')
	all_repository_set = get_repository_name_wiki_status_set(
		config_auth_token,
		config_data['repository_type']
	)

	print('Total repositories: {0}\n'.format(len(all_repository_set)))

	# determine how many Wiki's enabled
	wiki_enabled_repository_set = filter_repository_wiki_enabled(all_repository_set)

	if (len(wiki_enabled_repository_set) == 0):
		# no wiki's enabled - no work
		print('All wikis disabled')
		return

	print('Wikis enabled: {0}'.format(len(wiki_enabled_repository_set)))

	if (not config_data['dry_run']):
		print('\nDisabling wikis:')

		for repository_name in wiki_enabled_repository_set:
			# add subscription to repository
			disable_respository_wiki(config_auth_token,repository_name)
			print(repository_name)


if (__name__ == '__main__'):
	main()
