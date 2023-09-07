"""
Written by Steve Schwering @ UW-Madison
+ Useful resource: http://cs.wellesley.edu/~srosassm/cs234/google/sql_chrome_srosassm.html
				   https://www.forensicswiki.org/wiki/Google_Chrome
"""
import os
import re
import sys
import glob
import sqlite3
import operator
import datetime
import collections
import helperfunctions as hf

class BrowserHistoryExtractor():
	def __init__(self, browser, user_id = None, select_statement = None, browser_path_db = None):
		self.browser = browser
		self.user_id = user_id
		self.set_statement_db(select_statement = select_statement)
		self.set_browser_path_db(browser_db_path = browser_path_db)

	def set_statement_db(self, 
						 select_statement = None):
		"""
		Returns select statement for database query and returns their indices
		"""
		if select_statement == None:
			if self.browser == 'chrome':
				select_statement = "SELECT urls.url, urls.title, urls.visit_count, urls.last_visit_time, visits.visit_time, visits.visit_duration FROM urls, visits WHERE urls.id = visits.url;"
			elif self.browser == 'safari':
				select_statement = None
			elif self.browser == 'edge':
				select_statement = None
			elif self.browser == 'firefox':
				select_statement = "SELECT moz_places.url, moz_places.title, moz_places.visit_count, moz_places.last_visit_date FROM moz_places;"
			elif self.browser == 'opera':
				select_statement = None
			elif self.browser == 'brave':
				select_statement = None
			else:
				print('No default select statement for {}. Must specify.'.format(self.browser.upper()))
				return
			self.select_statement = select_statement
		else:
			self.select_statement = select_statement

	def set_browser_path_db(self, 
							browser_db_path = None):
		"""
		Checks and returns location of browser history path. Can handle some default locations
		+ TODO: HANDLE WINDOWS FORMATTING
		"""
		if browser_db_path == None:
			if self.browser == 'chrome':
				path = os.path.expanduser('~') + '/Library/Application Support/Google/Chrome/Default/History'
			elif self.browser == 'safari':
				path = os.path.expanduser('~') + '/Library/Safari/History'
			elif self.browser == 'edge':
				path = os.path.expanduser('~') + '/Library/Application Support/Edge/History'
			elif self.browser == 'firefox':
				# Firefox may have multiple .default histories in its directory
				path = os.path.expanduser('~') + '/Library/Application Support/Firefox/Profiles/'
				possible_paths = glob.glob(path + '*.*/places.sqlite')
				if len(possible_paths) > 1:
					print('Multiple {} histories; default and otherwise. Selecting largest.'.format(self.browser))
					largest = None
					for hist in possible_paths:
						if largest == None:
							largest = hist
							continue
						if os.path.getsize(largest) < os.path.getsize(hist):
							largest = hist
					path = hist
				else:
					path = possible_paths[0]
			elif self.browser == 'opera':
				path = os.path.expanduser('~') + '/Library/Application Support/Opera/History'
			elif self.browser == 'brave':
				path = os.path.expanduser('~') + '/Library/Application Support/Brave/Default/History'
			# Check if the path exists on this computer
			try:
				assert os.path.exists(path)
			except AssertionError:
				print('Default {} history database not found: {}'.format(self.browser.upper(), str(path)))
				return
			except UnboundLocalError:
				print('No default path for {}. Must provide.'.format(self.browser.upper()))
				return
			self.browser_db_path = path
		else:
			path = os.path.expanduser('~') + browser_db_path
			try:
				assert os.path.exists(browser_db_path)
			except AssertionError:
				print('User-generated {} history database not found: {}'.format(self.browser.upper(), str(path)))
				return
			self.browser_db_path = path

	def get_parameter_indices(self,
							  elem_separator = ', ', 
						 	  elem_identifier = '.'):
		"""
		Gets indices of parameters that will be generated for pulled urls
		"""
		if not hasattr(self, 'select_statement'):
			print('Cannot find select statement. No parameters.'.format(self.browser.upper()))
			return None
		pulled_parameter_indices = {}
		history_elements = re.match(r"SELECT\ (.*) FROM\ ", str(self.select_statement)) # Python 2
		history_elements = history_elements.group(1).split(elem_separator)
		history_elements = [elem.split(elem_identifier)[1].strip() for elem in history_elements]
		for index, elem in enumerate(history_elements):
			pulled_parameter_indices[elem] = index
		return pulled_parameter_indices

	def pull_browser_history_db(self,
								convert_date_time = True):
		"""
		Returns browser history, with the number of times each url was visited. Defaults to getting Chrome history
		+ select_statement -- defines the query to the history database
		+ browser_history_dir -- location of browser history
		+ domains -- True value shrinks urls to just get counts of each domain visit, ignoring specific page on website
		+ convert_date_time -- True if you want to convert time last accessed to human-readable format
		"""
		try:
			# Set up connection to DB and query history
			c_history = sqlite3.connect(self.browser_db_path)
			cursor_history = c_history.cursor()
			cursor_history.execute(self.select_statement)
			browser_history = cursor_history.fetchall()
			cursor_history.close()
			# Convert to list
			self.browser_history = [list(url) for url in browser_history]
			self.pull_date = datetime.datetime.now().strftime('%Y-%m-%d')
		except sqlite3.OperationalError:
			print("Cannot access {} history".format(self.browser.upper()))
		except AttributeError:
			print('Missing attribute for {}. Cannot pull history.'.format(self.browser.upper()))

	def check_permissions_db(self):
		"""
		List of functions to check browser history database permissions
		"""
		if not hasattr(self, 'browser_db_path'):
			print('Cannot check {} database. No path set.'.format(self.browser.upper()))
			return
		print("Checking {}".format(self.browser_db_path))
		print("\tExists: {}".format(os.path.exists(self.browser_db_path)))
		print("\tReadable: {}".format(os.access(self.browser_db_path, os.R_OK)))
		original_mode = oct(os.stat(self.browser_db_path).st_mode)
		print("\tMode: {}".format(oct(os.stat(self.browser_db_path).st_mode)))
		# DO NOT UNCOMMENT # #os.chmod(self.browser_db_path, 0o444) # NO PERMISSION TO CHANGE. NEED OT CHANGE PERMISSIONS WITHIN PYTHON
		#print("\tNew mode: {}".format(oct(os.stat(self.browser_db_path).st_mode)))
		#print("\tNow readable: {}".format(os.access(self.browser_db_path, os.R_OK)))
		# DO NOT UNCOMMENT # #os.chmod(self.browser_db_path, original_mode)
		#print("\tFinal mode: {}".format(oct(os.stat(self.browser_db_path).st_mode)))

	def summarize_urls(self,
					   url_key = 'url',
					   max_sites = None):
		"""
		Shrinks down full url to domain name. Useful for summarizing browsing history.
		+ Pulled from: https://geekswipe.net/technology/computing/analyze-chromes-browsing-history-with-python/
		"""
		if not hasattr(self, 'browser_history'):
			print('Cannot summarize {} history. Does not exist.'.format(self.browser.upper()))
			return
		sites_count = {}
		for site_info in self.browser_history:
			url = hf.get_domain(url = site_info[self.get_parameter_indices()[url_key]])
			if url in sites_count:
				sites_count[url] += 1
			else:
				sites_count[url] = 1
		sites_count_sorted = collections.OrderedDict(sorted(sites_count.items(), key=operator.itemgetter(1), reverse=True))
		if max_sites != None:
			sites_count_sorted = collections.Counter(sites_count_sorted).most_common(max_sites)
		return sites_count_sorted

	def change_datetime(self, time_col = 'visit_time'):
		"""
		Wrapper to call clean_time. Spread to two lines for ease of reading
		"""
		if not hasattr(self, 'browser_history'):
			print('Cannot change timestamps of {} history. Does not exist.'.format(self.browser.upper()))
			return
		pulled_parameter_indices = self.get_parameter_indices()
		if time_col not in pulled_parameter_indices.keys():
			print('{} is not a current parameter pulled from {}. Cannot change time.'.format(time_col, self.browser.upper()))
			return
		for entrynum, entry in enumerate(self.browser_history):
			self.browser_history[entrynum][pulled_parameter_indices[time_col]] = hf.clean_time(self.browser_history[entrynum][pulled_parameter_indices[time_col]])

	def expand_structure_db(self,
							select_statement = "SELECT name FROM sqlite_master WHERE type='table';",
							column_select_statement = "SELECT * FROM",
							max_cols = 10):
		"""
		Helper function to look at structure of SQL database
		"""
		if not hasattr(self, 'browser_db_path'):
			print('Cannot expand {} database. No path set.'.format(self.browser.upper()))
			return
		# Prepare to access history
		print(self.browser_db_path)
		# Begin querying the history
		try:
			c_history = sqlite3.connect(self.browser_db_path)
			cursor= c_history.cursor()
			cursor.execute(select_statement)
			table_names = cursor.fetchall()
			print("Expanding tables {} database:".format(self.browser))
			# First go through all the table names
			for table in table_names:
				print("\t{}".format(table[0].strip()))
				column_statement = column_select_statement + " {}".format(table[0])
				# Then start getting all the sub columns
				try:
					column_names = cursor.execute(column_statement)
					column_names = [title for title in cursor.description]
				except sqlite3.OperationalError:
					print('\t\tError decoding column name'.upper())
				for index, column in enumerate(column_names):
					print("\t\t{}".format(column[0]))
					if index == (max_cols - 1):
						break
		except sqlite3.OperationalError:
			print("Cannot expand database for {}".format(self.browser.upper()))

	def save(self, 
			 filename = None, 
			 meta_output_params = None, 
			 browser_output_params = None, 
			 overwrite = False):
		"""
		Organizes saving
		"""
		if not hasattr(self, 'browser_history'):
			print('Cannot save {} history. Does not exist.'.format(self.browser.upper()))
			return
		# Gets indices of pulled db parameters
		parameter_indices = self.get_parameter_indices()
		# Sets filename and file extension if none provided
		if filename == None:
			file_extension = 'tsv'
			filename = self.get_save_filename(extension = file_extension, overwrite = overwrite)
		else:
			file_extension = filename.split(separator)[-1]
		# Sets parameter output if none provided
		if meta_output_params == None:
			meta_output_params, _ = self.get_parameter_output_order()
		if browser_output_params == None:
			_, browser_output_params = self.get_parameter_output_order()
			for elem in parameter_indices.keys():	
				if elem not in browser_output_params:
					browser_output_params.append(elem)
					print('WARNING: {} output less than total db. Appending {} to right.'.format(self.browser.upper(), elem))
		# Saves file
		if file_extension == 'tsv':
			self.save_tsv(filename = filename, parameter_indices = parameter_indices, meta_output_params = meta_output_params, browser_output_params = browser_output_params)

	def get_parameter_output_order(self):
		"""
		Helper function for saving, organizing output files the way you want
		"""
		meta_params = ['user_id', 'pull_date', 'browser']
		if self.browser == 'chrome':
			browser_params = ['visit_time', 'title', 'url', 'visit_duration', 'last_visit_time', 'visit_count']
		elif self.browser == 'safari':
			browser_params = []
		elif self.browser == 'edge':
			browser_params = []
		elif self.browser == 'firefox':
			browser_params = ['url', 'title', 'visit_count', 'last_visit_date']
		elif self.browser == 'opera':
			browser_params = []
		elif self.browser == 'brave':
			browser_params = []
		else:
			print('No default output for {}.'.format(self.browser.upper()))
			return meta_params, list(self.get_parameter_indices())
		return meta_params, browser_params

	def get_save_filename(self, extension,
						  file_directory = os.getcwd() + '/output/',
						  overwrite = False,
						  append_num = 1):
		"""
		Checks save file names and generates a new one if needed
		"""
		if not (os.path.isdir(file_directory)):
			os.mkdir(file_directory)
		if self.user_id == None:
			filename = '{}_history_{}.{}'.format(self.browser, self.pull_date, extension)
		elif self.user_id == 'test':
			filename = '{}_{}_history.{}'.format(self.user_id, self.browser, extension)
		else:
			filename = '{}_{}_history_{}.{}'.format(self.user_id, self.browser, self.pull_date, extension)
		if overwrite:
			return file_directory + filename
		else:
			if not os.path.exists(filename):
				return file_directory + filename
			while True:
				_ = filename.split('.')
				output_filename = file_directory + _[0] + '(' + str(append_num) + ').' + _[1]
				if not os.path.exists(output_filename):
					return output_filename
				append_num += 1

	def save_tsv(self, filename, parameter_indices, meta_output_params, browser_output_params,
				 separator = '\t',
				 ender = '\n'):
		"""
		Saves browser history in .tsv file
		"""
		for elem in browser_output_params:
			if elem not in parameter_indices.keys():
				print('WARNING: Desired output parameter {} not in {} database. Cannot save that parameter.'.format(elem, self.browser.upper()))
				browser_output_params.remove(elem)
		elements_to_write = {}
		if 'browser' in meta_output_params:
			elements_to_write['browser'] = self.browser
		if 'user_id' in meta_output_params:
			elements_to_write['user_id'] = self.user_id
		if 'pull_date' in meta_output_params:
			elements_to_write['pull_date'] = self.pull_date
		if 'browser' in meta_output_params:
			elements_to_write['browser'] = self.browser
		parameter_output_order = meta_output_params + browser_output_params
		# Sets static meta info
		with open(filename, 'w') as f:
			f.write(separator.join(parameter_output_order) + ender)
			# Sets info for each history item
			for site in self.browser_history:
				for elem in parameter_indices:
					elements_to_write[elem] = site[parameter_indices[elem]]
				output = []
				for elem in parameter_output_order:
					try:
						output.append(elements_to_write[elem].encode('utf8'))
					except AttributeError:
						output.append(str(elements_to_write[elem]))
					except UnicodeEncodeError:
						output.append(str(elements_to_write[elem].encode('utf8')))
				try:
					f.write(separator.join(output) + ender)
				except TypeError:
					output = [_.decode('utf-8') if isinstance(_, bytes) else _ for _ in output]
					f.write(separator.join(output) + ender)

if __name__ == '__main__':
	### TODO: Windows machines do not come with python pre-installed. It might be necessary to run a virtual environment through a flash drive for these machines
	### TODO: Add command line arguments to indicate browser
	browser_history = BrowserHistoryExtractor(browser = 'chrome')
	browser_history.pull_browser_history_db()
	summary = browser_history.summarize_urls(max_sites = 50)
	print(summary)
	browser_history.save()