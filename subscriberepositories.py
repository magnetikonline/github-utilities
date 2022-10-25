#!/usr/bin/env python3

from lib import common, githubapi


def repository_name_set(
    auth_token: str, repository_type: str, repository_filter: common.RepositoryFilter
) -> set[str]:
    repository_set: set[str] = set()

    try:
        for repository_item in githubapi.user_repository_list(
            auth_token, repository_type
        ):
            repository_name = repository_item["full_name"]

            # include/exclude repository?
            if not repository_filter.accept(repository_name):
                continue

            # display name and add to set
            print(repository_name)
            repository_set.add(repository_name)

    except githubapi.APIRequestError as err:
        common.github_api_exit_error(
            f"Unable to fetch repository list for type {repository_type}.", err
        )

    return repository_set


def repository_subscription_name_set(auth_token: str) -> set[str]:
    subscription_set: set[str] = set()

    try:
        for subscription_item in githubapi.user_subscription_list(auth_token):
            repository_name = subscription_item["full_name"]

            # display subscription name & add to set
            print(repository_name)
            subscription_set.add(repository_name)

    except githubapi.APIRequestError as err:
        common.github_api_exit_error("Unable to fetch subscription list.", err)

    return subscription_set


def set_respository_subscription(auth_token: str, repository_name: str) -> None:
    # split repository into owner/repository parts
    owner, repository = repository_name.split("/")

    try:
        githubapi.set_user_repository_subscription(
            auth_token, owner, repository, subscribed=True
        )

    except githubapi.APIRequestError as err:
        common.github_api_exit_error(
            f"Unable to set subscription for repository {owner}/{repository}.", err
        )


def main():
    # fetch CLI arguments
    (dry_run, filter_include_list, filter_exclude_list) = common.read_arguments()

    # load config from file
    config_data = common.load_config()
    config_auth_token = config_data["AUTH_TOKEN"]

    # fetch repository list of the specified type
    print("Building repository list:")
    all_repository_set = repository_name_set(
        config_auth_token,
        config_data["REPOSITORY_TYPE"],
        common.RepositoryFilter(filter_include_list, filter_exclude_list),
    )

    # get total count, if zero then no work
    repository_count = len(all_repository_set)
    if repository_count < 1:
        print("\nNo repositories for processing")
        return

    print(f"\nTotal repositories: {repository_count}")

    # fetch repository watch details (subscriptions)
    print("\n\nFetching currently watched repositories:")
    subscription_set = repository_subscription_name_set(config_auth_token)

    print(f"\nTotal subscriptions: {len(subscription_set)}")

    # intersect repository set against current subscriptions - report difference
    unsubscribed_repository_set = all_repository_set.difference(subscription_set)
    unsubscribed_repository_set_count = len(unsubscribed_repository_set)

    if unsubscribed_repository_set_count < 1:
        # all repositories subscribed - no work
        print("\nAll repositories subscribed")
        return

    # list unsubscribed
    print("\n\nUnsubscribed repositories:")
    for repository_name in unsubscribed_repository_set:
        print(repository_name)

    # add subscriptions (only simulation if dry run mode)
    print(
        f"\n\nAdding {unsubscribed_repository_set_count} subscriptions"
        + (" [DRY RUN]" if (dry_run) else "")
        + ":"
    )

    for repository_name in unsubscribed_repository_set:
        if not dry_run:
            set_respository_subscription(config_auth_token, repository_name)

        print(repository_name)


if __name__ == "__main__":
    main()
