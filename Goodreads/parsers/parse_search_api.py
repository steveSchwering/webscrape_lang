import logging
import datetime
import xml.etree.ElementTree as ET # Core library

from yarl import URL

def parse_search_api(response, logger = None):
	"""
	Parse XML of search response
	Returns list of Book objects returned by search
	"""
	if logger:
		logger.debug(f'Parsing search API <{response.url}>')
	else:
		logging.debug(f'Parsing search API <{response.url}>')

	# Generate XML object and find books, which are stored as 'work' elements
	root = ET.fromstring(response.content)
	works = root.findall('.//work')

	# Generate Book object for each book
	books = []
	for work in works:
		books.append({
			'source'      : response.url,
			'accessed_datetime' : str(datetime.datetime.now()),
			'gr_book_id'  : _parse_search_api_id(work),
			'title'       : _parse_search_api_title(work),
			'author'      : _parse_search_api_author(work),
			'cover_url'   : _parse_search_api_cover_url(work),
			'pub_date'    : _parse_search_api_pub_date(work),
			'rating_count': _parse_search_api_rating_count(work),
			'rating_avg'  : _parse_search_api_rating_avg(work)
		})
	return books

def _parse_search_api_id(work):
	try:
		return work.find('./best_book/id').text
	except:
		return None

def _parse_search_api_title(work):
	try:
		return work.find('./best_book/title').text
	except:
		return None

def _parse_search_api_author(work):
	try:
		return work.find('./best_book/author/name').text
	except:
		return None

def _parse_search_api_cover_url(work):
	try:
		return URL(work.find('./best_book/image_url').text)
	except:
		return None

def _parse_search_api_pub_date(work):
	try:
		y = int(work.find('original_publication_year').text)
	except:
		return None
	try:
		m = int(work.find('original_publication_month').text)
	except:
		return None
	try:
		d = int(work.find('original_publication_day').text)
	except:
		return None
	return str(datetime.date(y, m, d))

def _parse_search_api_rating_count(work):
	try:
		rating_count = work.find('ratings_count').text
		return int(rating_count)
	except:
		return None

def _parse_search_api_rating_avg(work):
	try:
		rating_avg = work.find('average_rating').text
		return float(rating_avg)
	except:
		return None