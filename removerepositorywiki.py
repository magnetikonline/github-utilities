#!/usr/bin/env python3

from lib import common, githubapi


def repository_name_wiki_status_set(
    auth_token: str, repository_type: str, repository_filter: common.RepositoryFilter
) -> set[tuple[str, bool]]:
    repository_set: set[tuple[str, bool]] = set()

    try:
        for repository_item in githubapi.user_repository_list(
            auth_token, repository_type
        ):
            name = repository_item["full_name"]
            has_wiki = bool(repository_item["has_wiki"])

            # include/exclude repository?
            if not repository_filter.accept(name):
                continue

            # display name and wiki status
            print(name + (" - Wiki enabled" if (has_wiki) else ""))
            repository_set.add((name, has_wiki))

    except githubapi.APIRequestError as err:
        common.github_api_exit_error(
            f"Unable to fetch repository list for type {repository_type}.", err
        )

    return repository_set


def filter_repository_wiki_enabled(repository_set: set[tuple[str, bool]]) -> set[str]:
    return {name for name, has_wiki in repository_set if has_wiki}


def disable_repository_wiki(auth_token: str, repository_name: str) -> None:
    # split repository into owner/repository parts
    owner, repository = repository_name.split("/")

    try:
        githubapi.update_repository_properties(
            auth_token, owner, repository, wiki=False
        )

    except githubapi.APIRequestError as err:
        common.github_api_exit_error(
            f"Unable to disable wiki for repository {owner}/{repository}.", err
        )


def main():
    # fetch CLI arguments
    (dry_run, filter_include_list, filter_exclude_list) = common.read_arguments()

    # load config from file
    config_data = common.load_config()
    config_auth_token = config_data["AUTH_TOKEN"]

    # fetch repository list and wiki status of the specified repository type
    print("Building repository list:")
    all_repository_set = repository_name_wiki_status_set(
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

    # determine wiki enabled count
    wiki_enabled_repository_set = filter_repository_wiki_enabled(all_repository_set)
    wiki_enabled_count = len(wiki_enabled_repository_set)

    if wiki_enabled_count < 1:
        # no projects enabled - no work
        print("\nAll wikis disabled")
        return

    # disable wikis (only simulation if dry run mode)
    print(
        f"\n\nDisabling {wiki_enabled_count} wikis"
        + (" [DRY RUN]" if (dry_run) else "")
        + ":"
    )

    for repository_name in wiki_enabled_repository_set:
        if not dry_run:
            disable_repository_wiki(config_auth_token, repository_name)

        print(repository_name)


if __name__ == "__main__":
    main()
