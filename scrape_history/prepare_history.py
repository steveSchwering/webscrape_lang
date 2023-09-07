import os
import sys
import glob
import pandas
import random
import string
import logging

def read_master_history(master_url_log, expected_cols = ['url', 'url_id', 'scraped', 'scraped_info']):
	"""
	Reads the file keeping track of all ids used for all urls
	"""
	try:
		assert os.path.exists(master_url_log)
		extension = master_url_log.split('.')[-1]
		if extension == 'tsv':
			master_history = pandas.read_csv(master_url_log, sep = '\t')
		elif extension == 'csv':
			master_history = pandas.read_csv(master_url_log)
		return master_history
	except AssertionError:
		print('Error accessing {}. Cannot retrieve master history. Generating new datafrane.'.format(master_url_log))
		return pandas.DataFrame(columns = expected_cols)
	return master_history

def read_part_history(hist_dir):
	"""
	Reads all history files from folder and then combines them into one dataframe
	"""
	try:
		assert os.path.exists(hist_dir)
		frames = []
		for file in glob.glob(hist_dir + '/*.*'):
			extension = file.split('.')[-1]
			if extension == 'tsv':
				frames.append(pandas.read_csv(file, sep = '\t'))
			elif extension == 'csv':
				frames.append(pandas.read_csv(file))
		return pandas.concat(frames)
	except AssertionError:
		print('Error accessing {}. Cannot retrieve participant history directory. Returning None'.format(hist_dir))
		return None

def clean_participant_history(df, url_key = 'url'):
	"""
	Cleans urls based on a few criteria:
	+ Removes query parameters (maybe want to remove duplicates that lack query parameters?)
	+ Removes http: links in favor of https: links
	+ Removes final slashes from links if they are present
	+ Removes duplicates
	"""
	df[url_key] = df.apply(lambda row: row[url_key].split('?')[0], axis = 1) # Strip query parameters
	df[url_key] = df.apply(lambda row: row[url_key].replace('http://', 'https://'), axis = 1)
	df[url_key] = df.apply(lambda row: row[url_key][:-1] if row[url_key].endswith('/') else row[url_key], axis = 1)
	df = df.drop_duplicates(subset = url_key, keep = 'first') # Drops duplicates. It is important this follows the other cleaning functions
	return df

def pandas_save_file(df, filename, overwrite = True, default_filetype = 'tsv'):
	"""
	Saves pandas file df as filename. Handles different data types
	"""
	if len(filename.split('.')) == 1:
		filename = filename + "." + default_filetype
	extension = filename.split('.')[-1]
	filename = ''.join(filename.split('.')[:-1])
	if not overwrite:
		_filename = filename
		counter=0
		while os.path.exists(_filename):
			_filename += " ({})".format(counter)
			counter+=1
		filename = _filename
	filename = filename + "." + extension
	if extension == 'tsv':
		df.to_csv(filename, sep = '\t', index = False)
	elif extension == 'csv':
		df.to_csv(filename, index = False)

def get_unique_id(row, used_ids, url_key = 'url', id_key = 'url_id'):
	"""
	Generates new id and compares to existing ids. Iteratively requests until new id is generted
	"""
	if not pandas.isnull(row[id_key]):
		return row[id_key]
	while True:
		new_id = generate_alphanum_id()
		if new_id in used_ids:
			continue
		else:
			return new_id

def generate_alphanum_id(total_length = 15, valid = ['lowercase', 'digits']):
	"""
	Generates alphanumeric id for a given url
	"""
	poten_chars = {
		'lowercase' : list(string.ascii_lowercase),
		'uppercase' : list(string.ascii_uppercase),
		'digits' : list(string.digits)
	}
	random_id = []
	for _ in range(total_length):
		random_id.append(random.choice(poten_chars[random.choice(valid)]))
	return ''.join(random_id)

def prepare_history(hist_dir, master_url_log,
					url_key = 'url', 
					id_key = 'url_id', 
					scraped_key = 'scraped', 
					scraped_info_key = 'scraped_info'):
	"""
	Master function that handles combining histories, generating ids for urls, and updating master log
	"""
	# Read in frames
	master_history = read_master_history(master_url_log = master_url_log, expected_cols = [url_key, id_key, scraped_key, scraped_info_key])
	participant_history = read_part_history(hist_dir = hist_dir)

	# Clean participant history
	participant_history = clean_participant_history(participant_history, url_key = url_key)

	# Add already known urls from master log
	participant_history = participant_history.merge(master_history, how = 'left', on = url_key)

	# Generate new ids
	# # # Note this may generate a duplicate id for a given participant (as currently generated ids are not tracked)
	used_ids = list(master_history[id_key])
	participant_history[id_key] = participant_history.apply(lambda row: get_unique_id(row = row, used_ids = used_ids, url_key = url_key, id_key = id_key), axis = 1)

	# Updates master log with new urls and ids
	master_history = master_history.merge(participant_history[[url_key, id_key, scraped_key, scraped_info_key]], how = 'outer', on = [url_key, id_key, scraped_key, scraped_info_key])
	return master_history, participant_history

if __name__ == '__main__':
	check_prepared = True
	participant_id = 'c_history'
	hist_dir = os.getcwd() + '/input/raw_history/' + participant_id
	master_url_log = os.getcwd() + '/input/master_url_log.tsv'
	participant_output_filename = os.getcwd() + '/input/prepared_history/' + participant_id
	if check_prepared:
		if os.path.exists(participant_output_filename):
			print('Output file already exists. Exiting to avoid overwriting data.')
			sys.exit()
	master_history, participant_history = prepare_history(hist_dir = hist_dir, 
														  master_url_log = master_url_log)
	pandas_save_file(master_history, master_url_log)
	pandas_save_file(participant_history, participant_output_filename)