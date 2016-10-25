#!/usr/bin/env python

import common
import githubapi


def get_repository_name_set(auth_token,repository_type):
	repository_set = set()

	try:
		for repository_item in githubapi.get_user_repository_list(auth_token,repository_type):
			# display repository name and add to set
			print(repository_item['full_name'])
			repository_set.add(repository_item['full_name'])

	except githubapi.APIRequestError as e:
		common.github_exit_error('Unable to fetch repository list for type {0}.'.format(repository_type),e)

	return repository_set

def get_repository_subscription_name_set(auth_token):
	subscription_set = set()

	try:
		for subscription_item in githubapi.get_user_subscription_list(auth_token):
			# display subscription name & add to set
			print(subscription_item['full_name'])
			subscription_set.add(subscription_item['full_name'])

	except githubapi.APIRequestError as e:
		common.github_exit_error('Unable to fetch subscription list.',e)

	return subscription_set

def set_respository_subscription(auth_token,repository_full_name):
	# split repository into owner/repository parts
	owner,repository = tuple(repository_full_name.split('/'))

	try:
		githubapi.set_user_repository_subscription(
			auth_token,
			owner,repository,
			subscribed = True
		)

	except githubapi.APIRequestError as e:
		common.github_exit_error('Unable to set subscription for repository {0}/{1}.'.format(owner,repository),e)

def main():
	# load config from file
	config_data = common.load_config()
	config_auth_token = config_data['auth_token']

	# fetch repository names of the specified type
	print('Fetching repository list:')
	all_repository_set = get_repository_name_set(
		config_auth_token,
		config_data['repository_type']
	)

	print('Total repositories: {0}\n'.format(len(all_repository_set)))

	# fetch repository watch details (subscriptions)
	print('Fetching currently watched repositories:')
	subscription_set = get_repository_subscription_name_set(config_auth_token)

	print('Total subscriptions: {0}\n'.format(len(subscription_set)))

	# intersect repository set against current subscriptions - report difference
	unsubscribed_repository_set = all_repository_set.difference(subscription_set)

	if (len(unsubscribed_repository_set) == 0):
		# all repositories subscribed - no work
		print('All repositories subscribed')
		return

	# list unsubscribed
	print('Unsubscribed repositories:')
	for repository_name in unsubscribed_repository_set:
		print(repository_name)

	# add subscriptions if not in "dry run" mode
	if (not config_data['dry_run']):
		print('\nAdding {0} subscriptions:'.format(len(unsubscribed_repository_set)))

		for repository_name in unsubscribed_repository_set:
			# add subscription to repository
			set_respository_subscription(config_auth_token,repository_name)
			print(repository_name)


if (__name__ == '__main__'):
	main()
