import re
import datetime
import logging

from bs4 import BeautifulSoup
from yarl import URL

def parse_shelf(response, logger = None):
	if logger:
		logger.debug(f'Parsing shelf <{response.url}>')
	else:
		logging.debug(f'Parsing shelf <{response.url}>')
		
	soup = BeautifulSoup(response.text, 'html.parser')

	page_num = int(URL(response.url).query['page'])
	shelf = {
		'genre'    : _parse_shelf_genre(soup),
		'pages' : {
			page_num : {   
				'source'            : response.url,
				'accessed_datetime' : str(datetime.datetime.now())
			}
		}
	}

	books = []
	for book_soup in soup.find_all(name = 'div', attrs = {'class' : 'elementList', 'style' : 'padding-top: 10px;'}):
		books.append({
			'title'       : _parse_shelf_title(book_soup),
			'author'      : _parse_shelf_author(book_soup),
			'gr_book_id'  : _parse_shelf_id(book_soup),
			'topic_count' : _parse_shelf_topic_count(book_soup)
		})

	shelf['pages'][page_num].update({'books' : books})

	return shelf

def _parse_shelf_genre(soup):
	try:
		_ = str(soup.find(name = 'div', attrs = {'class' : 'genreHeader'}))
		genre = re.search(r"(?=Popular ).*(?<= Books)", _).group(0).replace('Popular ', '').replace(' Books', '')
		return genre
	except:
		return None

def _parse_shelf_title(soup):
	try:
		title = soup.find(name = 'a', attrs = {'class' : 'bookTitle'}).string
		return title
	except:
		return None

def _parse_shelf_author(soup):
	try:
		author = soup.find(name = 'a', attrs = {'class' : 'authorName'}).string.strip()
		return author
	except:
		return None

def _parse_shelf_id(soup):
	try:
		_ = soup.find(name = 'a', attrs = {'class' : 'bookTitle'})['href']
		_ = _.split('/')[-1].replace('.', '-')
		gr_book_id = re.search(r"^[0-9]*(?=-)", _).group(0)
		return gr_book_id
	except:
		return None

def _parse_shelf_topic_count(soup):
	try:
		_ = str(soup.find(name = 'a', attrs = {'class' : 'smallText'}))
		_ = re.search(r"(?=\().*(?<=\))", _).group(0)
		count = re.search(r"[\d]+", _).group(0)
		return int(count)
	except:
		return None