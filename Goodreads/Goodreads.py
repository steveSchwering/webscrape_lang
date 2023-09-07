import requests
import pathlib
import logging

from yarl import URL # OO URLsfrom github
from bs4 import BeautifulSoup

# Parsers
from parsers.parse_login      import parse_login
from parsers.parse_search_api import parse_search_api
from parsers.parse_lookup     import parse_lookup
from parsers.parse_similar    import parse_similar
from parsers.parse_shelf      import parse_shelf

from products.Book  import Book
from products.Shelf import Shelf

class Goodreads():
	def __init__(self, 
				 client_id:str = 'default', 
				 headers:dict = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.14; rv:74.0) Gecko/20100101 Firefox/74.0'}, 
				 cookies:dict = {},
				 **kwargs):
		# Participant ID used to track responses
		self.client_id = client_id
		self.other = kwargs

		# Recording defaults to file in logging_dir
		self.initialize_logger()

		# Set info about the client
		self.sess = requests.Session()
		self.set_headers(headers)
		self.set_cookies(cookies)

		# OAuth key is found if file if not provided
		self.oauth_key = self.get_oauth_key()

	def initialize_logger(self,
						  logging_dir:str = './logs',
						  filename_root:str = 'bsl'):
		"""
		Logger tracks requests and behavior of API wrapper
		+ filename_root defaults to bsl for "book survey log"
		"""
		# Path of log
		pathlib.Path(logging_dir).mkdir(parents = True, exist_ok = True)
		if "log" in self.other:
			filename = f'{filename_root}_{self.other["log"]}.txt'
		else:
			filename = f'{filename_root}_{self.client_id}.txt'
		log_path = pathlib.Path(logging_dir).joinpath(filename)
		handler = logging.FileHandler(filename = log_path, mode = 'a')

		# Formatting log
		fh = logging.Formatter(fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
		handler.setFormatter(fh)

		# Creating log
		self.logger = logging.getLogger(name = self.client_id)
		self.logger.setLevel(logging.DEBUG)
		self.logger.addHandler(handler)

		self.logger.debug(f'Initialized client {self.client_id}')

	def get_login_cred(self,
					  login_dir:str = './login',
					  login_file:str = 'test.txt'):
		"""
		Default searches
		"""
		login_path = pathlib.Path(login_dir).joinpath(login_file)

		with open(login_path, 'r') as f:
			username = f.readline().strip()
			password = f.readline().strip()

		return username, password

	def get_oauth_key(self, 
					  key_dir:str = './keys', 
					  key_file:str = 'steve_key.txt'):
		"""
		Accesses OAuth key
		+ OAuth key was set up manually and saved to disk for later use
		"""
		oauth_path = pathlib.Path(key_dir).joinpath(key_file)

		self.logger.debug(f'Accessing OAuth key for GoodReads client from file {oauth_path}')
		
		try:
			with open(oauth_path, 'r') as f:
				return f.readline()
		except FileNotFoundError:
			self.logger.debug(f'Key in {oauth_path} not found.')
			print(f'Key search: {oauth_path} not found.')
			return None

	def set_cookies(self, cookies:dict):
		"""
		Sets cookie to the current request session
		"""
		self.logger.debug(f'Manually adding new cookie {cookies.keys()} to session')
		for cookie in cookies:
			cookie_obj = requests.cookies.create_cookie(cookie, cookies[cookie])
			self.sess.cookies.set_cookie(cookie_obj)

	def set_headers(self, headers:dict):
		"""
		Sets header to the current request session
		"""
		self.logger.debug(f'Manually adding new header {headers.keys()} to session')
		self.sess.headers.update(headers)

	def build_url(self, url_scheme:str, url_host:str, url_path:str, url_query:dict = None):
		"""
		Generic url maker
		"""
		return URL.build(
			scheme = url_scheme,
			host = url_host,
			path = url_path,
			query = url_query
		)

	def request(self, url,
				method = 'GET',
				data = None,
				callback = None):
		"""
		Generic request
		"""
		# Make request
		if method == 'GET':
			response = self.sess.get(url = url, data = data)
		elif method == 'POST':
			response = self.sess.post(url = url, data = data)
		else:
			self.logger.debug(f'Request method {method} for url {url} not recognized.')
			return None, None

		# Log request
		self.logger.debug(
			f'{url.host} \"{method} {url.raw_path}?{url.query_string}\" {response.status_code}'
		)

		# Check response code
		try:
			assert response.status_code == 200
		except AssertionError:
			self.logger.debug(f'Request {method} returned non-200 status code. Cannot parse search results.')
			return None, response.status_code

		# Get callback
		if callback:
			parsed = callback(response = response, logger = self.logger)
			return parsed, response.status_code
		else:
			return response, response.status_code

	def login(self, 
			  url = 'https://www.goodreads.com/user/sign_in', 
			  userfield = 'user[email]',
			  passfield = 'user[password]'):
		"""
		GETs and POSTs to login page using username and password
		credentials. Cookies verifying login for further queries are
		stored in the current session.
		+ Some cookies are set before GET request. These values are
		based on my login attempts.
		"""
		self.logger.debug(f'Logging in to <{url}>')

		username, password = self.get_login_cred()

		#self.sess.cookies.set_cookie(_client_id2)
		# COOKIE INFORMATION EXCLUDED

		# GET request to login page to set some cookies and get back some login information
		payload, _ = self.request(url = url, callback = parse_login)
		payload.update({
			userfield : username,
			passfield : password
		})

		# POST login credentials
		return self.request(url = url, data = payload, method = 'POST')

	def search_api(self, search_term,
				   search_field = 'all',
				   page = 1,
				   url_scheme = 'https',
				   url_host = 'www.goodreads.com',
				   url_path = '/search.xml'):
		"""
		Search GoodReads API by book title, author, or ISBN
		"""
		url_query = {
			'q' : search_term,
			'page' : page,
			'key' : self.oauth_key,
			'search[field]' : search_field
		}

		url = self.build_url(
			url_scheme = url_scheme,
			url_host = url_host,
			url_path = url_path,
			url_query = url_query
		)

		return self.request(url = url, callback = parse_search_api)

	def lookup(self, gr_book_id,
			   url_scheme = 'https',
			   url_host = 'www.goodreads.com',
			   url_path = '/book/show'):
		"""
		Accesses page of a book given its goodreads book id
		+ Some more information about book genres is returned when logged
		in. A more limited list of genres is returned when not logged in.
		Otherwise, everything else should be the same.
		"""
		url = self.build_url(
			url_scheme = url_scheme,
			url_host = url_host,
			url_path = f'{url_path}/{gr_book_id}'
		)

		return self.request(url = url, callback = parse_lookup)

	def similar(self, similar_url,
				url_scheme = 'https',
				url_host = 'www.goodreads.com',
				url_path = '/book/similar'):
		"""
		Accesses similar books and returns ids
		+ Note a url is requested as input, not a goodreads id number
		+ The similar id for the book is different from the book id
		+ The similar id can only be found on the show page of the book,
		accessed in this script through the lookup() function
		"""
		url = URL(similar_url)

		return self.request(url = url, callback = parse_similar)

	def shelf(self, genre, 
			  page = 1,
			  url_scheme = 'https',
			  url_host = 'www.goodreads.com',
			  url_path = '/shelf/show'):
		"""
		Accesses single page of shelf
		+ Note to access pages beyond the first, the client must be logged
		in to a Goodreads account with the cookies stored in the current
		browsing session
		"""
		url = self.build_url(
			url_scheme = url_scheme,
			url_host = url_host,
			url_path = f'{url_path}/{genre}',
			url_query = {'page' : str(page)}
		)

		shelf, status_code = self.request(url = url, callback = parse_shelf)

		return shelf, status_code

	def shelf_iterative(self, genre,
						start_page = 1,
						max_page = 25,
						url_scheme = 'https',
						url_host = 'www.goodreads.com',
						url_path = '/shelf/show'):
		"""
		Loop through shelf pages and return one big shelf
		"""
		shelves = None
		status_codes = []

		for page_num in range(start_page, max_page+1):

			shelf, status_code = self.shelf(genre = genre, page = page_num)

			if not shelves:
				shelves = shelf
			else:
				shelves['pages'][page_num] = shelf['pages'][page_num]
			status_codes.append(status_code)

		return shelves, status_codes