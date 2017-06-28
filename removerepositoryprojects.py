#!/usr/bin/env python

import common
import githubapi


def get_repository_name_projects_status_set(auth_token,repository_type,repository_filter):
	repository_set = set()

	try:
		for repository_item in githubapi.get_user_repository_list(auth_token,repository_type):
			repository_name = repository_item['full_name']
			has_projects = repository_item['has_projects']

			# include/exclude repository?
			if (not repository_filter.accept(repository_name)):
				continue

			# display name and projects status
			print('{0}{1}'.format(
				repository_name,
				' - Projects enabled' if (has_projects) else ''
			))

			# add to set
			repository_set.add((
				repository_name,
				has_projects
			))

	except githubapi.APIRequestError as e:
		common.github_api_exit_error('Unable to fetch repository list for type {0}.'.format(repository_type),e)

	return repository_set

def filter_repository_projects_enabled(repository_set):
	def evaluator(filter_set,item):
		# add item to reduced set if projects enabled
		repository_name,has_projects = item
		if (has_projects):
			filter_set.add(repository_name)

		return filter_set

	return reduce(evaluator,repository_set,set())

def disable_repository_projects(auth_token,repository_name):
	# split repository into owner/repository parts
	owner,repository = repository_name.split('/')

	try:
		githubapi.update_repository_properties(
			auth_token,
			owner,repository,
			projects = False
		)

	except githubapi.APIRequestError as e:
		common.github_api_exit_error('Unable to disable projects for repository {0}/{1}.'.format(owner,repository),e)

def main():
	# fetch CLI arguments
	(
		dry_run,
		filter_list_include,
		filter_list_exclude
	) = common.read_arguments()

	# load config from file
	config_data = common.load_config()
	config_auth_token = config_data['auth_token']

	# fetch repository list and projects status of the specified repository type
	print('Building repository list:')
	all_repository_set = get_repository_name_projects_status_set(
		config_auth_token,
		config_data['repository_type'],
		common.RepositoryFilter(filter_list_include,filter_list_exclude)
	)

	# get total count, if zero then no work
	repository_count = len(all_repository_set)
	if (repository_count < 1):
		print('\nNo repositories for processing')
		return

	print('\nTotal repositories: {0}'.format(repository_count))

	# determine project enabled count
	projects_enabled_repository_set = filter_repository_projects_enabled(all_repository_set)
	projects_enabled_count = len(projects_enabled_repository_set)

	if (projects_enabled_count < 1):
		# no projects enabled - no work
		print('All projects disabled')
		return

	print('Projects enabled: {0}'.format(projects_enabled_count))

	# disable projects (only simulation if dry run mode)
	print('\n\nDisabling projects{0}:'.format(' [DRY RUN]' if (dry_run) else ''))

	for repository_name in projects_enabled_repository_set:
		if (not dry_run):
			disable_repository_projects(config_auth_token,repository_name)

		print(repository_name)


if (__name__ == '__main__'):
	main()
