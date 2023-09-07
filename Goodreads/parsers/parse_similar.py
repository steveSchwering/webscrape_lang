import re
import logging

from bs4 import BeautifulSoup

def parse_similar(response, logger = None):
	"""
	Get a list of similar book ids
	"""
	if logger:
		logger.debug(f'Parsing similar <{response.url}>')
	else:
		logging.debug(f'Parsing similar <{response.url}>')

	soup = BeautifulSoup(response.text, 'html.parser')

	similar_book_ids = []

	# Get list of books
	similar_books = soup.find_all(name = 'a', attrs = {'class' : 'gr-h3 gr-h3--serif gr-h3--noMargin', 'itemprop' : 'url'})
	for book in similar_books[1:]: # First book is identity
		try:
			last_part = book['href'].split('/')[-1].replace('.', '-')
			gr_book_id = re.search(r"^[0-9]*(?=-)", last_part).group(0)
			similar_book_ids.append(gr_book_id)
		except:
			continue

	return similar_book_ids