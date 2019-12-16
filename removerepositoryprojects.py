#!/usr/bin/env python3

from lib import common, githubapi


def repository_name_projects_status_set(auth_token, repository_type, repository_filter):
    repository_set = set()

    try:
        for repository_item in githubapi.user_repository_list(
            auth_token, repository_type
        ):
            name = repository_item["full_name"]
            has_projects = repository_item["has_projects"]

            # include/exclude repository?
            if not repository_filter.accept(name):
                continue

            # display name and projects status
            print(name + (" - Projects enabled" if (has_projects) else ""))
            repository_set.add((name, has_projects))

    except githubapi.APIRequestError as e:
        common.github_api_exit_error(
            f"Unable to fetch repository list for type {repository_type}.", e
        )

    return repository_set


def filter_repository_projects_enabled(repository_set):
    return {name for name, has_projects in repository_set if has_projects}


def disable_repository_projects(auth_token, repository_name):
    # split repository into owner/repository parts
    owner, repository = repository_name.split("/")

    try:
        githubapi.update_repository_properties(
            auth_token, owner, repository, projects=False
        )

    except githubapi.APIRequestError as e:
        common.github_api_exit_error(
            f"Unable to disable projects for repository {owner}/{repository}.", e
        )


def main():
    # fetch CLI arguments
    (dry_run, filter_include_list, filter_exclude_list) = common.read_arguments()

    # load config from file
    config_data = common.load_config()
    config_auth_token = config_data["AUTH_TOKEN"]

    # fetch repository list and projects status of the specified repository type
    print("Building repository list:")
    all_repository_set = repository_name_projects_status_set(
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

    # determine project enabled count
    projects_enabled_repository_set = filter_repository_projects_enabled(
        all_repository_set
    )
    projects_enabled_count = len(projects_enabled_repository_set)

    if projects_enabled_count < 1:
        # no projects enabled - no work
        print("\nAll projects disabled")
        return

    # disable projects (only simulation if dry run mode)
    print(
        f"\n\nDisabling {projects_enabled_count} projects"
        + (" [DRY RUN]" if (dry_run) else "")
        + ":"
    )

    for repository_name in projects_enabled_repository_set:
        if not dry_run:
            disable_repository_projects(config_auth_token, repository_name)

        print(repository_name)


if __name__ == "__main__":
    main()
