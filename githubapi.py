import json
import urllib
import urllib2

API_BASE_URL = 'https://api.github.com'
REQUEST_ACCEPT_VERSION = 'application/vnd.github.v3+json'
REQUEST_USER_AGENT = 'magnetikonline/githubutilities 1.0'
REQUEST_TOKEN = 'token {0}'
REQUEST_DATA_CONTENT_TYPE = 'application/json'
REQUEST_PAGE_SIZE = 20


class APIRequestError(Exception):
	def __init__(self,http_code = None,response = None):
		# error HTTP code and response body
		self.http_code = int(http_code)
		self.response = response

		super(APIRequestError,self).__init__()

class RequestMethod(urllib2.Request):
	def __init__(self,method,**kwargs):
		self.http_method = method
		urllib2.Request.__init__(self,**kwargs) # note: you can't super() old style Python classes

	def get_method(self):
		return self.http_method

def _make_request(
	auth_token,api_path,
	method = None,
	parameter_collection = None
):
	# build base request URL/headers
	request_url = '{0}/{1}'.format(API_BASE_URL,api_path)
	request_header_collection = {
		'Accept': REQUEST_ACCEPT_VERSION,
		'User-Agent': REQUEST_USER_AGENT
	}

	# API request has authorization token present?
	if (auth_token is not None):
		request_header_collection['Authorization'] = REQUEST_TOKEN.format(auth_token)

	if (method is None):
		# GET method
		# add request parameters as URL querystring items
		if (parameter_collection is not None):
			request_url = '{0}?{1}'.format(
				request_url,
				urllib.urlencode(parameter_collection)
			)

		request = urllib2.Request(
			url = request_url,
			headers = request_header_collection
		)

	else:
		# other methods (POST/PATCH/PUT/DELETE)
		data_send = None
		if (parameter_collection is not None):
			# convert parameter collection to JSON - sent with request
			data_send = json.dumps(
				parameter_collection,
				separators = (',',':')
			)

			# set content type
			request_header_collection['Content-Type'] = REQUEST_DATA_CONTENT_TYPE

		request = RequestMethod(
			method = method,
			url = request_url,
			data = data_send,
			headers = request_header_collection
		)

	# make the request
	try:
		response = urllib2.urlopen(request)

	except urllib2.HTTPError as e:
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
		parameter_paging_list = parameter_collection.copy()
		parameter_paging_list.update(
			page = request_page,
			per_page = REQUEST_PAGE_SIZE
		)

		# make API request
		response_data = _make_request(
			auth_token,api_path,
			parameter_collection = parameter_paging_list
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
		'orgs/{0}/repos'.format(organization_name),
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
		'repos/{0}/{1}'.format(
			urllib.quote(owner),
			urllib.quote(repository)
		),
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
		'repos/{0}/{1}/subscription'.format(
			urllib.quote(owner),
			urllib.quote(repository)
		)
	)

# info: https://developer.github.com/v3/activity/watching/#set-a-repository-subscription
def set_user_repository_subscription(
	auth_token,owner,repository,
	subscribed = False,
	ignored = False
):
	return _make_request(
		auth_token,
		'repos/{0}/{1}/subscription'.format(
			urllib.quote(owner),
			urllib.quote(repository)
		),
		method = 'PUT',
		parameter_collection = {
			'subscribed': subscribed,
			'ignored': ignored
		}
	)
