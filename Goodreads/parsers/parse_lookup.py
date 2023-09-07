import re
import datetime
import logging

from bs4 import BeautifulSoup
from yarl import URL

def parse_lookup(response, logger = None):
	"""
	Get all info aboutbook, returning dictionary of info
	"""
	if logger:
		logger.debug(f'Parsing lookup <{response.url}>')
	else:
		logging.debug(f'Parsing lookup <{response.url}>')

	soup = BeautifulSoup(response.text, 'html.parser')

	book_info = {
		'source'             : response.url,
		'accesed_date'       : str(datetime.datetime.now()),
		'gr_book_id'         : _parse_gr_book_id(response.url),
		'title'              : _parse_lookup_title(soup),
		'authors'            : _parse_lookup_author(soup),
		'cover_url'          : _parse_lookup_cover_url(soup),
		'rating_avg'         : _parse_lookup_rating_avg(soup),
		'rating_count'       : _parse_lookup_rating_count(soup),
		'pages'              : _parse_lookup_pages(soup),
		'pub_date'           : _parse_lookup_pub_date(soup),
		'title_original'     : _parse_lookup_title_original(soup),
		'isbn'               : _parse_lookup_isbn(soup),
		'gr_series_id'       : _parse_lookup_series_id(soup),
		'series_name'        : _parse_lookup_series_name(soup),
		'series_book_num'    : _parse_lookup_series_book_num(soup),
		'characters'         : _parse_lookup_character(soup),
		'top_genres'         : _parse_lookup_genres(soup),
		'similar_book_ids'   : _parse_lookup_abridged_similar(soup),
		'full_similar_link'  : _parse_lookup_full_similar_link(soup),
	}

	return book_info

def _parse_gr_book_id(url):
	url = URL(url)
	try:
		gr_book_id = re.search("^[0-9]*(?=-)", url.parts[-1].replace('.', '-')).group(0)
		return gr_book_id
	except AttributeError:
		try:
			gr_book_id = re.search("^[0-9]*", url.parts[-1].replace('.', '-')).group(0)
			return gr_book_id
		except:
			return None

def _parse_lookup_title(soup):
	try:
		_ = soup.find(name = 'div', attrs = {'id' : 'topcol'})
		title = _.find(name = 'h1', attrs = {'id' : 'bookTitle'}).string.strip()
		return title
	except:
		return None

def _parse_lookup_author(soup):
	authors = {}
	try:
		all_author_html = soup.find_all(name = 'div', attrs = {'class' : 'authorName__container'})

		for author_num, author_html in enumerate(all_author_html):
			author = {}
			
			# ID number
			try:
				author_url = URL(author_html.find(name = 'a', attrs = {'class' : 'authorName'})['href'])
				author['gr_author_id'] = re.search("^[0-9]*(?=-)", author_url.parts[-1].replace('.', '-')).group(0)
			except:
				author['gr_author_id'] = None

			# Name
			try:
				author['name'] = author_html.find(name = 'span', attrs = {'itemprop' : 'name'}).string.strip()
			except:
				author['name'] = None

			# Role -- usually None
			try:
				author['role'] = author_html.find(name = 'span', attrs = {'class' : 'authorName greyText smallText role'}).string.strip()
				author['role'] = re.search(r'[\w]*', author['role']).group(0)
			except:
				author['role'] = None

			authors[author_num] = author
		return authors
	except:
		return authors

def _parse_lookup_cover_url(soup):
	try:
		_ = soup.find(name = 'div', attrs = {'id' : 'topcol'})
		cover = URL(_.find(name = 'img', attrs = {'id' : 'coverImage'})['src'])
		return str(cover)
	except:
		return None

def _parse_lookup_rating_avg(soup):
	try:
		_ = soup.find(name = 'div', attrs = {'id' : 'topcol'})
		rating_avg = _.find(name = 'span', attrs = {'itemprop' : 'ratingValue'}).string.strip()
		return float(rating_avg)
	except:
		return None

def _parse_lookup_rating_count(soup):
	try:
		_ = soup.find(name = 'div', attrs = {'id' : 'topcol'})
		rating_count = _.find(name = 'meta', attrs = {'itemprop' : 'ratingCount'})['content']
		return int(rating_count)
	except:
		return None

def _parse_lookup_pages(soup):
	try:
		page_str = soup.find(name = 'span', attrs = {'itemprop' : 'numberOfPages'}).string.strip()
		pages = re.search(r'^[\d]*', page_str).group(0)
		return int(pages)
	except:
		return None

def _parse_lookup_pub_date(soup):
	pubs = {}
	try:
		details = soup.find(name = 'div', attrs = {'id' : 'details'})
		pub_details = details.find_all(name = 'div', attrs = {'class' : 'row'})[1] # Second row
	except:
		return None

	"""
	Publication date of the current edition
	Converted from: https://stackoverflow.com/questions/35413746/regex-to-match-date-like-month-name-day-comma-and-year
	"""
	reg = r"(Jan(uary)?|Feb(ruary)?|Mar(ch)?|Apr(il)?|May|Jun(e)?|Jul(y)?|Aug(ust)?|Sep(tember)?|Oct(ober)?|Nov(ember)?|Dec(ember)?)\s+\d{1,2}[a-z]{2}\s+\d{4}"
	try:
		pubs['edition'] = pub_details.contents[0].strip()
		dmy = re.search(reg, pubs['edition']).group(0)
		dmy = re.sub(r'(\d)(st|nd|rd|th)', r'\1', dmy)
		dmy = datetime.datetime.strptime(dmy, '%B %d %Y')
		pubs['edition'] = str(dmy)
	except AttributeError: # Likely due to only year being present for very old books
		pubs['edition'] = None
	except:
		pubs['edition'] = None

	# Original publication date
	try:
		pubs['original'] = pub_details.find(name = 'nobr', attrs = {'class' : 'greyText'}).string.strip()
		dmy = re.search(reg, pubs['original']).group(0)
		dmy = re.sub(r'(\d)(st|nd|rd|th)', r'\1', dmy)
		dmy = datetime.datetime.strptime(dmy, '%B %d %Y')
		pubs['original'] = str(dmy)
	except AttributeError: # Likely due to only year being present for very old books
		pubs['original'] = None
	except:
		pubs['original'] = None

	return pubs

def __parse_lookup_detail_row(soup, target_name, 
							  return_item = True):
	"""
	Returns the section of html that contains a target row name (e.g. 'ISBN')
	"""
	try:
		segments = soup.find_all(name = 'div', attrs = {'class' : 'clearFloats'})
		for segment in segments:
			if segment.find(name = 'div', attrs = {'class' : 'infoBoxRowTitle'}).string == target_name:
				if return_item:
					return segment.find(name = 'div', attrs = {'class' : 'infoBoxRowItem'})
				else:
					return segment
	except:
		return None

def _parse_lookup_title_original(soup):
	try:
		title_original_info = __parse_lookup_detail_row(soup, target_name = 'Original Title')
		title_original = title_original_info.string.strip()
		return title_original
	except:
		return None

def _parse_lookup_isbn(soup):
	isbns = {}
	try:
		isbn_info = __parse_lookup_detail_row(soup, target_name = 'ISBN')
	except:
		return None
	try:
		isbns['isbn'] = isbn_info.contents[0].strip()
	except:
		isbns['isbn'] = None
	try:	
		isbns['isbn13'] = isbn_info.find('span', attrs = {'itemprop' : 'isbn'}).string.strip()
		return isbns
	except:
		isbns['isbn13'] = None
		return isbns

def _parse_lookup_series_id(soup):
	try:
		series_info = __parse_lookup_detail_row(soup, target_name = 'Series')
		href = series_info.find(name = 'a')['href']
		series_id = re.search(r'^(\d)*', href.split('/')[-1].replace('.', '-')).group(0)
		return series_id
	except:
		return None

def _parse_lookup_series_name(soup):
	try:

		series_info = __parse_lookup_detail_row(soup, target_name = 'Series')
		series_string = series_info.find(name = 'a').string
		series_name = re.search(r'([^#]+)', series_string).group(0)
		return series_name
	except:
		return None

def _parse_lookup_series_book_num(soup):
	try:
		series_info = __parse_lookup_detail_row(soup, target_name = 'Series')
		series_string = series_info.find(name = 'a').string
		series_book_num = re.findall(r'(?<=\#).*', series_string)[-1]
		return series_book_num
	except:
		return None

def _parse_lookup_character(soup):
	try:
		chars_segment = __parse_lookup_detail_row(soup, target_name = 'Characters', return_item = False)
		all_a_rows = chars_segment.find_all(name = 'a')
		all_chars = [row.string.strip() for row in all_a_rows if not row.has_attr('onclick')]
		return all_chars
	except:
		return None

def _parse_lookup_genres(soup):
	"""
	More genres are shown in the sidebar when logged in
	"""
	try:
		genres = soup.find_all(name = 'a', attrs = {'class' : 'actionLinkLite bookPageGenreLink'})
		genres = [genre.string.strip() for genre in genres]
		return genres
	except:
		return None

def _parse_lookup_abridged_similar(soup,
						  		   url_scheme = 'https',
								   url_host = 'www.goodreads.com'):
	"""
	Abridged only accesses the similar books on the page of the current book
	Usually around 18 books
	"""
	abridged_similar_book_ids = []
	try:
		carousel = soup.find(name = 'div', attrs = {'class' : 'bookCarousel'})
		for book in carousel.find_all(name = 'a'):
			book = URL(book['href'])
			book = re.search("^[0-9]*(?=-)", book.parts[-1].replace('.', '-')).group(0)
			abridged_similar_book_ids.append(int(book))
		return abridged_similar_book_ids
	except:
		return abridged_similar_book_ids

def _parse_lookup_full_similar_link(soup):
	"""
	There is a larger list on a different page
	Usually around 30 books
	Oddly, the similar link does not follow the same goodreads book ID as the rest of the site
	"""
	try:
		full_similar_link = soup.find(text = "See similar books…").parent['href']
		return full_similar_link
	except:
		return None