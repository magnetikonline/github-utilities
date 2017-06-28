# GitHub utilities
Random scripts for working with GitHub itself and repositories. All designed to work against Python 2.7+.

- [Utilities](#utilities)
	- [listorganizationrepositorybysize.py](#listorganizationrepositorybysizepy)
	- [removerepositorywiki.py](#removerepositorywikipy)
	- [removerepositoryprojects.py](#removerepositoryprojectspy)
	- [subscriberepositories.py](#subscriberepositoriespy)
- [Configuration](#configuration)
- [Filter arguments](#filter-arguments)
	- [Examples](#examples)

## Utilities

### [listorganizationrepositorybysize.py](listorganizationrepositorybysize.py)
- Fetches all repositories for a given `ORGANIZATION`, ordered in descending size order.
- Emits results to the console as tab separated repository/size (kilobytes) lines.

### [removerepositorywiki.py](removerepositorywiki.py)
- Scans repositories and reports all with an enabled [Wiki](https://help.github.com/articles/about-github-wikis/).
- Repository checking scope can be set with the `--include` / `--exclude` [filter arguments](#filter-arguments).
- With `--commit` argument passed will actively disable each wiki found.

### [removerepositoryprojects.py](removerepositoryprojects.py)
- Scans repositories and reports all with an enabled [Projects](https://help.github.com/articles/about-project-boards/) board.
- Repository checking scope can be set with the `--include` / `--exclude` [filter arguments](#filter-arguments).
- With `--commit` argument passed will actively disable each project board found.

### [subscriberepositories.py](subscriberepositories.py)
- By default GitHub [notification settings](https://github.com/settings/notifications) are configured to automatically watch all repositories to which you have _push access_ - including your own personal repositories:
	- This state works well when running solo, but association to an active organization you soon find a watch list getting very noisy with notifications.
	- Disabling `Automatic watching` works, but you're now left in a situation of potentially forgetting to watch *your own* personal repositories after creation and update of issues/PRs.
- This script fetches all repositories in scope and compares to your subscription list - reporting back repositories that aren't currently watched.
- Repository checking scope can be set with the `--include` / `--exclude` [filter arguments](#filter-arguments).
- With `--commit` argument passed any repositories not watched will be subscribed to.

## Configuration
All settings contained in a single [`config.json`](config.json). A breakdown of each setting follows:
- `AUTH_TOKEN` - a valid GitHub token ID, generated via the [Personal access tokens](https://github.com/settings/tokens) page. Token requires full access to the `repo` scope and it's sub-scopes:

	![Personal access token permissions](http://i.imgur.com/m12VszH.png)
- `ORGANIZATION` - where required, specifies the organization to use for repository fetch.
- `REPOSITORY_TYPE` - when repositories are fetched - defines the context/association to to user to use.

	Valid options [are listed here](https://developer.github.com/v3/repos/#list-your-repositories) with the default of `owner` more than likely what you're after.

## Filter arguments
Certain scripts allow control of their repository scope via the `--include` and `--exclude` arguments. This provides the ability to skip over a subset of repositories from checks/updates.

- The valid character range for a filter is `[*/A-Za-z0-9_.-]` or a wildcard (`*`) for matching one or more characters.
- A filter will be tested against the full `user/repository_name` or `organization/repository_name` name.
- An `--exclude` match will negate an `--include` filter.
- If no `--include` filter is given, default will be "match all" (`*`).

### Examples

```sh
# matches "user/one" and "user/two" but not "user/one_two" or "user/three"
./script.py \
	--include "u*/one" \
	--include "u*/two"

# matches "organization/*" but not "organization/skip_me"
./script.py \
	--include "organization/*" \
	--exclude "*/skip_me"

# will match everything except "user/avoid"
./script.py \
	--exclude "user/avoid"
```
