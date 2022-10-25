#!/usr/bin/env python3

from lib import common, githubapi

ORGANIZATION_CONFIG_KEY = "ORGANIZATION"


def organization_repository_size_sorted_list(
    auth_token: str, organization_name: str, repository_type: str
) -> list[tuple[str, int]]:
    repository_list: list[tuple[str, int]] = []

    try:
        for repository_item in githubapi.organization_repository_list(
            auth_token, organization_name, repository_type
        ):
            repository_list.append(
                (repository_item["git_url"], int(repository_item["size"]))
            )

    except githubapi.APIRequestError as err:
        common.github_api_exit_error(
            f"Unable to fetch repository list for organization {organization_name}, type {repository_type}.",
            err,
        )

    # sort by repository size descending
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

    # output list, repository URL/size - tab separated
    for repository_url, repository_size in repository_list:
        print(f"{repository_url}\t{repository_size}")


if __name__ == "__main__":
    main()
