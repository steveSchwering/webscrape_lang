def get_domain(url):
	"""
	Helper function to parse URLs into the domain
	"""
	try:
		parsed_url_components = url.split('//')
		sublevel_split = parsed_url_components[1].split('/', 1)
		domain = sublevel_split[0].replace("www.", "")
		return domain
	except IndexError:
		#traceback.print_exc()
		print("URL format error!")

def clean_time(timestamp,
			   timetype = '1601', 
			   output_str = True):
	"""
	TODO: OUTPUT TIME APPEARS TO BE OFF SOMEWHAT
	Helper function to onvert time to a human readable format
	Pulled from https://www.forensicswiki.org/wiki/Google_Chrome
	+ timetype can be 'visit_time' or 'start_time' depending on the start date -- 1601 and 1970, respectively
	+ Converts microseconds datatype to string if Ture. Microseconds are more efficient, so try to keep them.
	"""
	try:
		if timetype == '1601':
			date_string = datetime.datetime(1601, 1, 1) + datetime.timedelta(microseconds = timestamp)
		elif timetype == '1970':
			date_string = datetime.datetime(1970, 1, 1) + datetime.timedelta(microseconds = timestamp)
		else:
			print('Error converting time. Need to specify 1601 or 1970 timetype')
			return timestamp
	except TypeError:
		return None
	if output_str:
		return str(date_string)
	else:
		return date_string

def split_list_at_str(lst, splitter, case_sensitive = True):
	"""
	Splitting lists called by check_robots
	"""
	if case_sensitive:
		splitting_indices = [i for i, x in enumerate(lst) if splitter in x]
	else:
		splitting_indices = [i for i, x in enumerate(lst) if splitter.lower() in x.lower()]
	new_lst = []
	sub_lst = []
	for index, line in enumerate(lst):
		if line == '':
			continue
		if index in splitting_indices:
			new_lst.append(sub_lst)
			sub_lst = []
		sub_lst.append(line)
	new_lst.append(sub_lst)
	new_lst = [segment for segment in new_lst if segment]
	return new_lst