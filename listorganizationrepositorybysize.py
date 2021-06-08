#!/usr/bin/env python3

from lib import common, githubapi

ORGANIZATION_CONFIG_KEY = "ORGANIZATION"


def organization_repository_size_sorted_list(
    auth_token, organization_name, repository_type
):
    repository_list = []

    try:
        for repository_item in githubapi.organization_repository_list(
            auth_token, organization_name, repository_type
        ):
            repository_list.append(
                (str(repository_item["git_url"]), int(repository_item["size"]))
            )

    except githubapi.APIRequestError as e:
        common.github_api_exit_error(
            f"Unable to fetch repository list for organization {organization_name}, type {repository_type}.",
            e,
        )

    # sort list by repository size descending
    return sorted(repository_list, key=lambda item: item[1], reverse=True)


def main():
    # load config from file
    config_data = common.load_config(config_key_addition_set={ORGANIZATION_CONFIG_KEY})
    config_auth_token = config_data["AUTH_TOKEN"]

    # fetch repository names/sizes of the specified type
    print("Building repository list ordered by size:")
    repository_list = organization_repository_size_sorted_list(
        config_auth_token,
        config_data[ORGANIZATION_CONFIG_KEY],
        config_data["REPOSITORY_TYPE"],
    )

    # output list, repository URI/size - tab separated
    for repository_uri, repository_size in repository_list:
        print(f"{repository_uri}\t{repository_size}")


if __name__ == "__main__":
    main()
