#!/usr/bin/env python

import common
import githubapi


def get_repository_name_set(auth_token,repository_type,repository_filter):
	repository_set = set()

	try:
		for repository_item in githubapi.get_user_repository_list(auth_token,repository_type):
			repository_name = repository_item['full_name']

			# include/exclude repository?
			if (not repository_filter.accept(repository_name)):
				continue

			# display name and add to set
			print(repository_name)
			repository_set.add(repository_name)

	except githubapi.APIRequestError as e:
		common.github_api_exit_error('Unable to fetch repository list for type {0}.'.format(repository_type),e)

	return repository_set

def get_repository_subscription_name_set(auth_token):
	subscription_set = set()

	try:
		for subscription_item in githubapi.get_user_subscription_list(auth_token):
			repository_name = subscription_item['full_name']

			# display subscription name & add to set
			print(repository_name)
			subscription_set.add(repository_name)

	except githubapi.APIRequestError as e:
		common.github_api_exit_error('Unable to fetch subscription list.',e)

	return subscription_set

def set_respository_subscription(auth_token,repository_full_name):
	# split repository into owner/repository parts
	owner,repository = repository_full_name.split('/')

	try:
		githubapi.set_user_repository_subscription(
			auth_token,
			owner,repository,
			subscribed = True
		)

	except githubapi.APIRequestError as e:
		common.github_api_exit_error('Unable to set subscription for repository {0}/{1}.'.format(owner,repository),e)

def main():
	# fetch CLI arguments
	(
		dry_run,
		filter_list_include,
		filter_list_exclude
	) = common.read_arguments()

	# load config from file
	config_data = common.load_config()
	config_auth_token = config_data['AUTH_TOKEN']

	# fetch repository list of the specified type
	print('Building repository list:')
	all_repository_set = get_repository_name_set(
		config_auth_token,
		config_data['REPOSITORY_TYPE'],
		common.RepositoryFilter(filter_list_include,filter_list_exclude)
	)

	# get total count, if zero then no work
	repository_count = len(all_repository_set)
	if (repository_count < 1):
		print('\nNo repositories for processing')
		return

	print('\nTotal repositories: {0}'.format(repository_count))

	# fetch repository watch details (subscriptions)
	print('\n\nFetching currently watched repositories:')
	subscription_set = get_repository_subscription_name_set(config_auth_token)

	print('\nTotal subscriptions: {0}'.format(len(subscription_set)))

	# intersect repository set against current subscriptions - report difference
	unsubscribed_repository_set = all_repository_set.difference(subscription_set)
	unsubscribed_repository_set_count = len(unsubscribed_repository_set)

	if (unsubscribed_repository_set_count < 1):
		# all repositories subscribed - no work
		print('\nAll repositories subscribed')
		return

	# list unsubscribed
	print('\n\nUnsubscribed repositories:')
	for repository_name in unsubscribed_repository_set:
		print(repository_name)

	# add subscriptions (only simulation if dry run mode)
	print('\n\nAdding {0} subscriptions{1}:'.format(
		unsubscribed_repository_set_count,
		' [DRY RUN]' if (dry_run) else ''
	))

	for repository_name in unsubscribed_repository_set:
		if (not dry_run):
			set_respository_subscription(config_auth_token,repository_name)

		print(repository_name)


if (__name__ == '__main__'):
	main()
