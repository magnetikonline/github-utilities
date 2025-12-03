import json
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Generator
from typing import Any, Callable

API_BASE_URL = "https://api.github.com"
REQUEST_ACCEPT_VERSION = "application/vnd.github+json"
REQUEST_API_VERSION = "2022-11-28"
REQUEST_USER_AGENT = "magnetikonline/githubutilities 1.0"
REQUEST_DATA_CONTENT_TYPE = "application/json"
REQUEST_PAGE_SIZE = 20


class APIRequestError(Exception):
    def __init__(self, http_code: int, response: str):
        # error HTTP code and response body
        self.http_code = http_code
        self.response = response

        super().__init__()


def _request(
    auth_token: str | None,
    api_path: str,
    method: str | None = None,
    parameter_collection: dict[str, bool | str] = {},
) -> Any:
    # build base request URL/headers
    request_url = f"{API_BASE_URL}/{api_path}"
    header_collection = {
        "Accept": REQUEST_ACCEPT_VERSION,
        "User-Agent": REQUEST_USER_AGENT,
        "X-GitHub-Api-Version": REQUEST_API_VERSION,
    }

    # API request has authorization token present?
    if auth_token is not None:
        header_collection["Authorization"] = f"Bearer {auth_token}"

    if method is None:
        # GET method
        # add request parameters as URL querystring items
        if parameter_collection:
            request_url = (
                f"{request_url}?{urllib.parse.urlencode(parameter_collection)}"
            )

        request = urllib.request.Request(headers=header_collection, url=request_url)
    else:
        # other method types (POST/PATCH/PUT/DELETE)
        data_send = ""
        if parameter_collection:
            # convert parameter collection to JSON - sent as request payload
            data_send = json.dumps(parameter_collection, separators=(",", ":"))

            # set content type
            header_collection["Content-Type"] = REQUEST_DATA_CONTENT_TYPE

        request = urllib.request.Request(
            data=None if (data_send == "") else bytes(data_send, "ascii"),
            headers=header_collection,
            method=method,
            url=request_url,
        )

    # make the request
    try:
        response = urllib.request.urlopen(request)
    except urllib.error.HTTPError as err:
        # re-raise as API error
        raise APIRequestError(err.code, str(err.read()))  # HTTP code and error message
    else:
        # parse JSON response and return
        response_data = json.load(response)
        response.close()

        return response_data


def _request_paged(
    auth_token: str,
    api_path: str,
    parameter_collection: dict[str, bool | str] = {},
    item_processor: Callable[[list[Any]], Generator[Any]] | None = None,
) -> Generator[Any]:
    # init a default item processor function, if none given
    def default_item_processor(response_data: list[Any]) -> Generator[Any]:
        for response_item in response_data:
            yield response_item

    if item_processor is None:
        item_processor = default_item_processor

    # init initial request page
    request_page = 1
    active = True

    while active:
        # build paging parameters - merged with base request parameters
        parameter_paged_collection = parameter_collection.copy()
        parameter_paged_collection.update(
            page=str(request_page), per_page=str(REQUEST_PAGE_SIZE)
        )

        # make API request
        response_data = _request(
            auth_token, api_path, parameter_collection=parameter_paged_collection
        )

        # process result items/rows - will exit when page returned with no further items
        active = False
        for response_item in item_processor(response_data):
            active = True
            yield response_item

        # increment page for next API call
        request_page += 1


def _urlquote(value: str) -> str:
    return urllib.parse.quote(value)


# info: https://docs.github.com/en/rest/repos/repos#list-repositories-for-the-authenticated-user
def user_repository_list(
    auth_token: str, repository_type: str
) -> Generator[dict[str, Any]]:
    return _request_paged(
        auth_token, "user/repos", parameter_collection={"type": repository_type}
    )


# info: https://docs.github.com/en/rest/repos/repos#list-organization-repositories
def organization_repository_list(
    auth_token: str, organization_name: str, repository_type: str
) -> Generator[dict[str, Any]]:
    return _request_paged(
        auth_token,
        f"orgs/{_urlquote(organization_name)}/repos",
        parameter_collection={"type": repository_type},
    )


# info: https://docs.github.com/en/rest/repos/repos#update-a-repository
def update_repository_properties(
    auth_token: str,
    owner: str,
    repository: str,
    default_branch: str | None = None,
    description: str | None = None,
    homepage: str | None = None,
    issues: str | None = None,
    private: str | None = None,
    projects: bool | None = None,
    wiki: bool | None = None,
) -> Any:
    # build up request collection from given arguments
    patch_collection: dict[str, bool | str] = {"name": repository}

    def add_property(param: bool | str | None, key: str):
        if param is not None:
            patch_collection[key] = param

    add_property(default_branch, "default_branch")
    add_property(description, "description")
    add_property(homepage, "homepage")
    add_property(issues, "has_issues")
    add_property(private, "private")
    add_property(projects, "has_projects")
    add_property(wiki, "has_wiki")

    # update repository
    return _request(
        auth_token,
        f"repos/{_urlquote(owner)}/{_urlquote(repository)}",
        method="PATCH",
        parameter_collection=patch_collection,
    )


# info: https://docs.github.com/en/rest/activity/watching#list-repositories-watched-by-the-authenticated-user
def user_subscription_list(auth_token: str) -> Generator[dict[str, Any]]:
    return _request_paged(auth_token, "user/subscriptions")


# info: https://docs.github.com/en/rest/activity/watching#get-a-repository-subscription
def repository_subscription(auth_token: str, owner: str, repository: str) -> Any:
    return _request(
        auth_token,
        f"repos/{_urlquote(owner)}/{_urlquote(repository)}/subscription",
    )


# info: https://docs.github.com/en/rest/activity/watching#set-a-repository-subscription
def set_user_repository_subscription(
    auth_token: str,
    owner: str,
    repository: str,
    subscribed: bool = False,
    ignored: bool = False,
) -> Any:
    return _request(
        auth_token,
        f"repos/{_urlquote(owner)}/{_urlquote(repository)}/subscription",
        method="PUT",
        parameter_collection={"subscribed": subscribed, "ignored": ignored},
    )


# info: https://docs.github.com/en/rest/webhooks/repos#list-repository-webhooks
def repository_webhook_list(
    auth_token: str, owner: str, repository: str
) -> list[dict[str, Any]]:
    return _request(
        auth_token,
        f"repos/{_urlquote(owner)}/{_urlquote(repository)}/hooks",
    )
