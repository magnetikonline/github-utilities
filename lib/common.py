import argparse
import json
import os
import re
import sys
from typing import Any

from lib import githubapi

GITHUB_AUTH_TOKEN_KEY_NAME = "AUTH_TOKEN"
GITHUB_AUTH_TOKEN_REGEXP = re.compile(
    r"^(ghp_[a-zA-Z0-9]{36}|github_pat_[a-zA-Z0-9]{22}_[a-zA-Z0-9]{59})$"
)

REPOSITORY_FILTER_REGEXP = re.compile(r"^[*/A-Za-z0-9_.-]+$")
MANDATORY_CONFIG_KEY_SET = {GITHUB_AUTH_TOKEN_KEY_NAME, "REPOSITORY_TYPE"}
CONFIG_FILE = (
    os.path.dirname(os.path.dirname(os.path.realpath(__file__))) + "/config.json"
)


def _exit_error(message: str) -> None:
    print(f"Error: {message}", file=sys.stderr)
    sys.exit(1)


def github_api_exit_error(message: str, api_request_error: githubapi.APIRequestError):
    _exit_error(f"{message} HTTP code: {api_request_error.http_code}")


def read_arguments() -> tuple[bool, list[str], list[str]]:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--commit", action="store_true", help="apply changes, otherwise dry run"
    )

    parser.add_argument(
        "--include",
        help="repository include filter - defaults to '*'",
        nargs="*",
    )

    parser.add_argument("--exclude", help="repository exclude filter", nargs="*")

    arg_list = parser.parse_args()

    # validate repository include/exclude filters
    def validate_filter_list(filter_type: str, filter_list: list[str] | None):
        if filter_list is None:
            # no work
            return

        for filter_item in filter_list:
            if not REPOSITORY_FILTER_REGEXP.search(filter_item):
                # invalid filter characters
                _exit_error(f"Invalid {filter_type} filter of [{filter_item}]")

    validate_filter_list("include", arg_list.include)
    validate_filter_list("exclude", arg_list.exclude)

    # return arguments
    return (
        not arg_list.commit,  # 'dry run' mode?
        [] if (arg_list.include is None) else arg_list.include,
        [] if (arg_list.exclude is None) else arg_list.exclude,
    )


def load_config(config_key_addition_set: set[str] = set()) -> dict[str, str]:
    # build full config key set - attempt to pull auth token from env var
    config_key_set = MANDATORY_CONFIG_KEY_SET.union(config_key_addition_set)
    env_auth_token = os.environ.get(GITHUB_AUTH_TOKEN_KEY_NAME)

    # open and parse JSON config
    config_data: dict[Any, Any] = {}
    try:
        fp = open(CONFIG_FILE, "rb")
        config_data = json.load(fp)
        fp.close()
    except FileNotFoundError:
        # config file not found
        _exit_error(f"Unable to load {CONFIG_FILE}")

    for config_key in config_key_set:
        if (config_key == GITHUB_AUTH_TOKEN_KEY_NAME) and (env_auth_token is not None):
            # GitHub auth token from environment variable, not config file - skip check
            continue

        # config keys exist?
        if config_key not in config_data:
            _exit_error(
                f"Unable to locate [{config_key}] config key in [{CONFIG_FILE}]"
            )

        # ensure value is not empty
        if not config_data[config_key].strip():
            _exit_error(f"Config key [{config_key}] is empty")

    # validate auth token format
    if env_auth_token is not None:
        config_data[GITHUB_AUTH_TOKEN_KEY_NAME] = env_auth_token

    if not GITHUB_AUTH_TOKEN_REGEXP.search(config_data[GITHUB_AUTH_TOKEN_KEY_NAME]):
        _exit_error(
            "Invalid GitHub authorization token specified in config or environment variable"
        )

    # return expected config items from config data
    return {
        str(extract_key): str(config_data[extract_key]).strip()
        for extract_key in config_key_set
    }


class RepositoryFilter:
    def __init__(self, include_list: list[str], exclude_list: list[str]):
        # convert include/exclude filters to regular expressions
        self.include_list = RepositoryFilter._build(self, include_list)
        self.exclude_list = RepositoryFilter._build(self, exclude_list)

    def accept(self, name: str) -> bool:
        # if exclude match - reject
        if RepositoryFilter._is_match(self, self.exclude_list, name):
            return False

        # if include match - accept
        if len(self.include_list) < 1:
            # if no include filters defined then always accept by default
            return True

        return RepositoryFilter._is_match(self, self.include_list, name)

    def _build(self, source_list: list[str]) -> list[re.Pattern]:
        build_list: list[re.Pattern] = []
        for filter_item in source_list:
            # escape meta characters, set wildcard/start/end metas
            re_filter = re.escape(filter_item).replace("\\*", ".+?")
            build_list.append(re.compile(f"^{re_filter}$"))

        return build_list

    def _is_match(self, filter_list: list[re.Pattern], name: str) -> bool:
        for item in filter_list:
            if item.search(name):
                # matched
                return True

        # no match
        return False
