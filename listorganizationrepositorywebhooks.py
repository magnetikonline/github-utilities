#!/usr/bin/env python3

from typing import List, Tuple

from lib import common, githubapi

ORGANIZATION_CONFIG_KEY = "ORGANIZATION"


def organization_repository_webhooks_list(
    auth_token: str, organization_name: str, repository_type: str
) -> List[Tuple[str, List[str]]]:
    repository_list: List[Tuple[str, List[str]]] = []

    try:
        for repository_item in githubapi.organization_repository_list(
            auth_token, organization_name, repository_type
        ):
            # split repository into owner/repository parts
            owner, repository = repository_item["full_name"].split("/")
            webhook_list: List[str] = []

            try:
                for item in githubapi.repository_webhook_list(
                    auth_token, owner, repository
                ):
                    webhook_list.append(item["config"]["url"])
            except githubapi.APIRequestError as err:
                common.github_api_exit_error(
                    f"Unable to fetch webhook list for repository {owner}/{repository}.",
                    err,
                )

            if webhook_list:
                repository_list.append((repository_item["git_url"], webhook_list))

    except githubapi.APIRequestError as err:
        common.github_api_exit_error(
            f"Unable to fetch repository list for organization {organization_name}, type {repository_type}.",
            err,
        )

    return repository_list


def main():
    # load config from file
    config_data = common.load_config(config_key_addition_set={ORGANIZATION_CONFIG_KEY})
    config_auth_token = config_data["AUTH_TOKEN"]

    # fetch repositories of the specified type and their defined webhooks
    print("Building repository list including webhooks:")
    repository_list = organization_repository_webhooks_list(
        config_auth_token,
        config_data[ORGANIZATION_CONFIG_KEY],
        config_data["REPOSITORY_TYPE"],
    )

    # output list, repository URL with webhooks defined
    for repository_url, webhook_list in repository_list:
        print(f"{repository_url}:")
        for hook_item in webhook_list:
            print(f"\t{hook_item}")


if __name__ == "__main__":
    main()
