import logging
from bs4 import BeautifulSoup

def parse_login(response, logger = None):
	"""
	Get arguments for POST from the GET request
	"""
	if logger:
		logger.debug(f'Parsing login <{response.url}>')
	else:
		logging.debug(f'Parsing login <{response.url}>')

	soup = BeautifulSoup(response.text, 'html.parser')

	return {
		'authenticity_token' : soup.find('input', {'name' : 'authenticity_token'})['value'],
		'n' : soup.find('input', {'name' : 'n', 'type' : 'hidden'})['value']
	}