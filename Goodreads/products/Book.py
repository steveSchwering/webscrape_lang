import json
import pathlib
import logging

class Book():
	def __init__(self, *args, **kwargs):
		self.data = kwargs
		try:
			logging.debug(f'Generated Book object of {self.data["title"]} ({self.data["gr_book_id"]}) from <{self.data["source"]}>')
		except KeyError:
			logging.debug(f'Generated empty Book object')

	def __str__(self):
		return self.data['title']

	def add_similar(self, similar):
		"""
		Similar books are received at different times
		"""
		try:
			if self.data['similar_book_ids']:
				self.data['similar_book_ids'] += similar
				self.data['similar_book_ids'] = set(self.data['similar_book_ids'])
			else:
				self.data['similar_book_ids'] = similar
		except KeyError:
			self.data['similar_book_ids'] += similar

	def describe(self, 
				 excluded = ['title', 'gr_book_id', 'similar_book_ids', 'abridged_similar_book_links'],
				 max_list_elems = 5):
		"""
		Summarizes contents of book to console
		"""
		try:
			print(f'Book: {self.data["title"]} ({self.data["gr_book_id"]}) -- {self.data["authors"][0]["name"]}')
		except IndexError:
			print(f'Book: {self.data["title"]} ({self.data["gr_book_id"]})')

		for field in filter(lambda field: field not in excluded, self.data):
			if type(self.data[field]) == list:
				print(f'\t{field}: {self.data[field][:max_list_elems]}')
			else:
				print(f'\t{field}: {self.data[field]}')

		if 'similar_book_ids' in self.data:
			print(f'\tSimilar books ({len(self.data["similar_book_ids"])}):')
			for book in self.data["similar_book_ids"]:
				print(f'\t\t{book}')

	def get_cover_image(self,
						save_cover = False,
						cover_dir = './temp_covers'):
		"""
		Requests a cover image from server or returns None if no url reference exists
		"""
		if self.cover_url == None:
			return None

		cover_data = requests.get(self.cover_url, stream = True)

		if save_cover:
			cover_path = pathlib.Path(cover_dir).joinpath(f'{gr_book_id}.{self.cover_url[-3:]}')
			with open(cover_path, 'wb') as f:
				cover_data.raw.decode_content = True
				shutil.copyfileobj(cover_data.raw, f)

		return cover_data

	def save(self, directory, 
			 mkdir = True,
			 overwrite = False):
		"""
		Returns boolean of whether file was created or not
		"""
		# If directory does not exist and we want to make directory, create directory
		if not pathlib.Path(directory).exists() and mkdir:
			pathlib.Path(directory).mkdir(parents = True)

		filepath = pathlib.Path(directory).joinpath(self.data['gr_book_id']).with_suffix('.json')

		# If file exists and we do not want to overwrite, do not create file
		if filepath.exists() and not overwrite:
			logging.debug(f'Write Book failed: Book ({self.data["gr_book_id"]}) exists on disk in {directory}')
			return False
		# else, write the file
		else:
			logging.debug(f'Writing Book {self.data["title"]} ({self.data["gr_book_id"]}) to disk')
			with open(filepath, 'w') as f:
				json.dump(obj = self.data, fp = f, indent = 4, sort_keys = True)
			return True

	def load(self, filepath):
		"""
		Reads in json file to dictionary
		"""
		if self.data != {}:
			logging.debug(f'Load Book from {filepath} failed: Overwriting Book {self.data["title"]} ({self.data["gr_book_id"]}).')
			return False

		try:
			with open(filepath, 'r') as f:
				self.data = json.load(f)
				logging.debug(f'Loaded Book {self.data["title"]} ({self.data["gr_book_id"]}) from disk')
				return True
		except FileNotFoundError:
			logging.debug(f'Load Book failed: File {filepath} not found.')
			return False