import json
import urllib.error
import urllib.parse
import urllib.request

API_BASE_URL = 'https://api.github.com'
REQUEST_ACCEPT_VERSION = 'application/vnd.github.v3+json'
REQUEST_USER_AGENT = 'magnetikonline/githubutilities 1.0'
REQUEST_DATA_CONTENT_TYPE = 'application/json'
REQUEST_PAGE_SIZE = 20


class APIRequestError(Exception):
	def __init__(self,http_code = None,response = None):
		# error HTTP code and response body
		self.http_code = int(http_code)
		self.response = response

		super(APIRequestError,self).__init__()

def _make_request(
	auth_token,api_path,
	method = None,
	parameter_collection = None
):
	# build base request URL/headers
	request_url = f'{API_BASE_URL}/{api_path}'
	header_collection = {
		'Accept': REQUEST_ACCEPT_VERSION,
		'User-Agent': REQUEST_USER_AGENT
	}

	# API request has authorization token present?
	if (auth_token is not None):
		header_collection['Authorization'] = f'token {auth_token}'

	if (method is None):
		# GET method
		# add request parameters as URL querystring items
		if (parameter_collection is not None):
			request_url = f'{request_url}?{urllib.parse.urlencode(parameter_collection)}'

		request = urllib.request.Request(
			headers = header_collection,
			url = request_url
		)
	else:
		# other method types (POST/PATCH/PUT/DELETE)
		data_send = None
		if (parameter_collection is not None):
			# convert parameter collection to JSON - sent with request
			data_send = json.dumps(
				parameter_collection,
				separators = (',',':')
			)

			# set content type
			header_collection['Content-Type'] = REQUEST_DATA_CONTENT_TYPE

		request = urllib.request.Request(
			data = bytes(data_send,'ascii'),
			headers = header_collection,
			method = method,
			url = request_url
		)

	# make the request
	try:
		response = urllib.request.urlopen(request)
	except urllib.error.HTTPError as e:
		# re-raise as API error
		raise APIRequestError(
			e.code, # HTTP code
			e.read() # error message
		)
	else:
		# parse JSON response and return
		response_data = json.load(response)
		response.close()

		return response_data

def _make_request_paged(
	auth_token,api_path,
	parameter_collection = {},
	item_processor = None
):
	# init initial request page
	request_page = 1
	active = True

	# set a default item processor function, if none given
	def default_item_processor(response_data):
		for response_item in response_data:
			yield response_item

	if (item_processor is None):
		item_processor = default_item_processor

	while (active):
		# build paging parameters - merged with base request parameters
		parameter_paged_collection = parameter_collection.copy()
		parameter_paged_collection.update(
			page = request_page,
			per_page = REQUEST_PAGE_SIZE
		)

		# make API request
		response_data = _make_request(
			auth_token,api_path,
			parameter_collection = parameter_paged_collection
		)

		# process result items/rows - will exit when page returned with no further items
		active = False
		for response_item in item_processor(response_data):
			active = True
			yield response_item

		# increment current page for next call
		request_page = request_page + 1

# info: https://developer.github.com/v3/repos/#list-your-repositories
def get_user_repository_list(auth_token,repository_type):
	return _make_request_paged(
		auth_token,
		'user/repos',
		parameter_collection = {
			'type': repository_type
		}
	)

# info: https://developer.github.com/v3/repos/#list-organization-repositories
def get_organization_repository_list(auth_token,organization_name,repository_type):
	return _make_request_paged(
		auth_token,
		f'orgs/{organization_name}/repos',
		parameter_collection = {
			'type': repository_type
		}
	)

# info: https://developer.github.com/v3/repos/#edit
def update_repository_properties(
	auth_token,owner,repository,
	default_branch = None,
	description = None,
	homepage = None,
	issues = None,
	private = None,
	projects = None,
	wiki = None
):
	# build up request collection from given arguments
	patch_collection = {
		'name': repository
	}

	def add_property(param,key):
		if (param is not None):
			patch_collection[key] = param

	add_property(default_branch,'default_branch')
	add_property(description,'description')
	add_property(homepage,'homepage')
	add_property(issues,'has_issues')
	add_property(private,'private')
	add_property(projects,'has_projects')
	add_property(wiki,'has_wiki')

	# update repository
	return _make_request(
		auth_token,
		f'repos/{urllib.parse.quote(owner)}/{urllib.parse.quote(repository)}',
		method = 'PATCH',
		parameter_collection = patch_collection
	)

# info: https://developer.github.com/v3/activity/watching/#list-repositories-being-watched
def get_user_subscription_list(auth_token):
	return _make_request_paged(
		auth_token,
		'user/subscriptions'
	)

# info: https://developer.github.com/v3/activity/watching/#get-a-repository-subscription
def get_user_repository_subscription(auth_token,owner,repository):
	return _make_request(
		auth_token,
		f'repos/{urllib.parse.quote(owner)}/{urllib.parse.quote(repository)}/subscription'
	)

# info: https://developer.github.com/v3/activity/watching/#set-a-repository-subscription
def set_user_repository_subscription(
	auth_token,owner,repository,
	subscribed = False,
	ignored = False
):
	return _make_request(
		auth_token,
		f'repos/{urllib.parse.quote(owner)}/{urllib.parse.quote(repository)}/subscription',
		method = 'PUT',
		parameter_collection = {
			'subscribed': subscribed,
			'ignored': ignored
		}
	)
