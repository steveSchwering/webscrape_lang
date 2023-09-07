import json
import pathlib
import logging
import random

class Shelf():
	def __init__(self, *args, **kwargs):
		self.data = kwargs
		try:
			logging.debug(f'Generated Shelf object of topic {self.data["genre"]}')
		except:
			logging.debug(f'Generated empty Shelf object')

	def __str__(self):
		return self.data['genre']

	def describe(self,
				 num_shelves = 3):
		"""
		Summarizes contents of book
		"""
		page_nums = sorted([int(page) for page in self.data['pages']])

		for page_num in page_nums[:num_shelves]:
			print(f'Shelf: {self.data["genre"]} page {page_num}')
			print(f'\tSource: {self.data["pages"][page_num]["source"]}')
			print(f'\tAccessed: {self.data["pages"][page_num]["accessed_datetime"]}')
			print(f'\tBooks: ')

			for book in self.data["pages"][page_num]["books"]:
				print(f'\t\t{book["topic_count"]}: {book["title"]} ({book["gr_book_id"]}) -- {book["author"]}')

		remaining_pages = list(self.data['pages'].keys())[num_shelves:]
		remaining_pages = [str(page) for page in remaining_pages]
		print(f'\t...remaining pages that can be described in shelf {self.data["genre"]}: {", ".join(remaining_pages)}')

	def get_books(self, 
				  target_top_n_pages = None):
		"""
		Returns list of all books across all pages. Alternatively 
		"""
		books = []

		if not target_top_n_pages:
			target_top_n_pages = len(self.data['pages'])
		page_nums = sorted([page for page in self.data['pages']])[:target_top_n_pages]

		for page in page_nums:
			books += self.data['pages'][page]['books']

		return books

	def sample_books(self, target_pages):
		"""
		Generates random sample of books
		"""
		pass

	def save(self, directory, 
			 mkdir = True,
			 overwrite = False):
		"""
		Returns boolean of whether file was created or not
		"""
		# If directory does not exist and we want to make directory, create directory
		if not pathlib.Path(directory).exists() and mkdir:
			pathlib.Path(directory).mkdir(parents = True)

		filepath = pathlib.Path(directory).joinpath(self.data['genre']).with_suffix('.json')

		# If file exists and we do not want to overwrite, do not create file
		if filepath.exists() and not overwrite:
			logging.debug(f'Write Shef failed: Shelf ({self.data["genre"]}) exists on disk in {directory}')
			return False
		# else, write the file
		else:
			logging.debug(f'Writing Shelf {self.data["genre"]} to disk')
			with open(filepath, 'w') as f:
				json.dump(obj = self.data, fp = f, indent = 4, sort_keys = True)
			return True

	def load(self, filepath):
		"""
		Reads in json file to dictionary
		"""
		if self.data != {}:
			logging.debug(f'Load Shelf from {filepath} failed: Overwriting Shelf {self.data["genre"]}.')
			return False

		try:
			with open(filepath, 'r') as f:
				self.data = json.load(f)
				logging.debug(f'Loaded Shelf {self.data["genre"]} from disk')
				return True
		except FileNotFoundError:
			logging.debug(f'Load Shelf failed: File {filepath} not found.')
			return False