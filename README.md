# GitHub utilities
Random scripts for working with GitHub itself and repositories. All designed to work against Python 2.7+.

- [Utilities](#utilities)
	- [listorganizationrepositorybysize.py](#listorganizationrepositorybysizepy)
	- [removerepositorywiki.py](#removerepositorywikipy)
	- [subscriberepositories.py](#subscriberepositoriespy)
- [Configuration](#configuration)

## Utilities

### [listorganizationrepositorybysize.py](listorganizationrepositorybysize.py)
- Fetches all repositories for a given `organization`, ordered in descending size order.
- Emits results to the console as tab separated GitHub repository/size (kilobytes) lines.

### [removerepositorywiki.py](removerepositorywiki.py)
- Scans over a GitHub owners repositories and reports all with an enabled [GitHub Wiki](https://help.github.com/articles/about-github-wikis/) - which is the default setting.
- With `dry_run` mode disabled will actively remove each Wiki found.

### [subscriberepositories.py](subscriberepositories.py)
- By default GitHub [notification settings](https://github.com/settings/notifications) are configured to automatically watch all repositories to which you have push access - including your own personal repositories:
	- This default typically works well, until associated to active/busy organization(s) where you find you're automatically watching repositories which aren't of interest.
	- Disabling `Automatic watching` works, but you are then left with the situation of potentially forgetting to watch *your own* new personal repositories for new issues/PRs/etc.
- This script therefore will fetch all personal/owned repositories and current subscription list - reporting back any repositories that are not currently being watched.
- With `dry_run` mode disabled will actively subscribe you to each owned repository not currently watched.

## Configuration
All settings contained in a single [`config.json`](config.json). A breakdown of each setting follows - all of which are mandatory:
- `auth_token` - a valid GitHub token ID, generated via the [Personal access token](https://github.com/settings/tokens) page. Token requires full access to the `repo` scope and it's sub-scopes. For example:
	![Personal access token permissions](http://i.imgur.com/m12VszH.png)
- `dry_run` - boolean which determines if scripts should update/correct found issues where possible. If set `true` will only *report* issues without update or change.
- `organization` - where required, specifies the organization to use for repository fetch.
- `repository_type` - where a list of repositories is fetched - defines the context/association to to user. Valid options [are listed here](https://developer.github.com/v3/repos/#list-your-repositories) with the default of `owner` more than likely what you're after.
