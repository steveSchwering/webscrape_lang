import os
import sys
import glob
import json
import pandas

"""
Put this script in a folder.
The folder with the script should contain the following folder system:

profiles
|
|----> dasha
		|
		|----> facebook-dasha

facebook-dasha should be your facebook profile data download containing the various json files.
This script should handle the rest.
"""

"""
profiles
|
|----> <profile_name_1> e.g. steve
|		|
|		|----> <social_media_profile_1> e.g. facebook-stevenschwering
|		|		|
|		|		|----> <messages>
|		|		|		|
|		|		|		|----> archived_threads
|		|		|		|		|
|		|		|		|		|----> <conversation_1> e.g. <friend-name>_npK8sOVFUw
|		|		|		|		|		|
|		|		|		|		|		|----> message_1.json
|		|		|		|		|
|		|		|		|		|----> <conversation_2>
|		|		|		|		|
|		|		|		|		|----> etc.
|		|		|		|
|		|		|		|----> filtered_threads
|		|		|		|		|
|		|		|		|		|----> <conversation_1>
|		|		|		|		|
|		|		|		|		|----> <conversation_2>
|		|		|		|		|
|		|		|		|		|----> etc.
|		|		|		|
|		|		|		|----> inbox
|		|		|		|
|		|		|		|----> stickers_used
|		|		|
|		|		|
|		|		|----> etc.
|		|
|		|
|		|----> <social_media_profile_2>
|		|
|		|----> etc.
|
|----> <profile_name_2>
|
|----> etc.
"""

def get_participant_output_directories(text_out_dir, profiles_dir):
	"""
	Returns output folder for a participant or generates a new one
	+ text_out_dir -- directory where formatted data will be stored
	+ profiles_dir -- location of participant directory containing raw social media data
	"""
	participant_output_dirs = {}
	for participant in profiles_dir:
		participant_name = profiles_dir[participant].split('/')[-1]
		participant_output_dir = text_out_dir + "/" + participant_name
		if not os.path.exists(text_out_dir):
			os.mkdir(text_out_dir)
		if not os.path.exists(participant_output_dir):
			os.mkdir(participant_output_dir)
		participant_output_dirs[participant] = participant_output_dir
	return participant_output_dirs

def get_participant_raw_directories(profiles_dir):
	"""
	Returns list of all participant directories
	+ profiles_dir -- location of participant directory containing raw social media data
	"""
	try:
		assert(os.path.exists(profiles_dir))
		profiles = glob.glob(profiles_dir + "/*")
		profiles_dic = {}
		for profile in profiles:
			profiles_dic[profile.split('/')[-1]] = profile
		return profiles_dic
	except AssertionError:
		print('Error accessing profiles. Profiles path {} does not exist.'.format(profiles_dir))
		sys.exit()

def get_social_media_directories(participants,
								 splitter = '/',
								 target_sites = ['facebook', 'twitter', 'instagram']):
	"""
	Given dictionary of participant folders, returns directories of social media sites for each participant
	+ participants -- dictionary of participant directories containing social media data
	"""
	try:
		assert type(participants) == dict
	except AssertionError:
		print('Argument \'participants\' requests dictionary of participant directories.')
		sys.exit()
	profiles_by_participant = {}
	# For each participant
	for participant_dir in participants:
		participant_name = participants[participant_dir].split(splitter)[-1]
		social_sites_dic = {} # Add sites to this dictionary
		social_media_sites = glob.glob(participants[participant_dir] + '/*')
		# Access each social media account for which we have data
		for social_site in social_media_sites:
			social_site_reduced = social_site.split('/')[-1]
			# Associates each social media site with a target name
			for target_site in target_sites:
				if target_site in social_site_reduced:
					social_sites_dic[target_site] = social_site
		# Append social media sites to dictionary keyed by participant name
		profiles_by_participant[participant_name] = social_sites_dic
	return profiles_by_participant

def get_message_files(profile_name, facebook_profile_dir,
					  messages_folder = '/messages',
					  target_messages_subfolders = ['archived_threads', 'inbox']):
	"""
	Returns the full set of message files with some additional information
	"""
	try:
		assert os.path.exists(facebook_profile_dir)
	except AssertionError:
		print("Facebook profile {} does not exist".format(facebook_profile_dir))
		sys.exit()
	# Set messages directory and check participant data folder has messages folder
	messages_directory = facebook_profile_dir + messages_folder
	try:
		assert os.path.exists(messages_directory)
	except AssertionError:
		print("Messages not found for profile {}".format(facebook_profile))
		sys.exit()
	# Start accessing files messages folder
	profile_message_files = []
	for message_thread in glob.glob(messages_directory + '/*'):
		message_thread_type = message_thread.split('/')[-1]
		# Only records messages of certain type (e.g. archived, inbox)
		if message_thread_type in target_messages_subfolders:
			# Accesses all conversations in folder
			for conversation_dir in glob.glob(message_thread + '/*'):
				conversation_title = conversation_dir.split('/')[-1]
				for conversation_file_path in glob.glob(conversation_dir + '/*.json'):
					profile_message_files.append({'profile_name': profile_name,
												  'message_thread_type': message_thread_type,
												  'conversation_title': conversation_title,
												  'conversation_file_path': conversation_file_path})
	return profile_message_files

def save_messages(output, text_out_dir, conversation_meta_data,
				  file_info = {'extension': '.tsv',
								'separator': '\t',
								'header_meta': ['profile_name',
												'message_thread_type',
												'conversation_title',
												'conversation_file_path'],
								'header_convo': ['message_timestamp_ms', 
												 'sender_name', 
												 'text',
												 'num_words'],
								'subfolder': 'facebook_messages'}):
	"""
	Saves output to file
	"""
	filename = "{}/{}{}".format(text_out_dir,
								file_info['subfolder'],
								file_info['extension'])
	exists_bool = os.path.exists(filename)
	with open(filename, 'a') as f:
		if not exists_bool:
			f.write(file_info['separator'].join(file_info['header_meta'] + file_info['header_convo']) + '\n')
		for message in output:
			out = []
			for column in file_info['header_meta']:
				try:
					out.append(str(conversation_meta_data[column]))
				except UnicodeEncodeError:
					out.append(conversation_meta_data[column].encode('ascii', 'ignore'))
			for column in file_info['header_convo']:
				try:
					out.append(str(message[column].replace('\n', ' ').replace('\t', ' ').replace('\r', ' ')))
				except AttributeError:
					out.append(str(message[column]))
				except UnicodeEncodeError:
					out.append(message[column].encode('ascii', 'ignore'))
			f.write(file_info['separator'].join(out) + '\n')

def extract_conversation_text(profile, conversation_meta_data, text_out_dir):
	all_text = get_conversation_data_from_json(conversation_meta_data)
	save_messages(output = all_text, conversation_meta_data = conversation_meta_data, text_out_dir = text_out_dir)

def get_conversation_data_from_json(conversation_meta_data,
									file_key = 'conversation_file_path',
									messages_key = 'messages',
									message_timestamp_ms = 'timestamp_ms',
									sender_name = 'sender_name',
									text = 'content'):
	"""
	Access message data
	"""
	output = []
	conversation_file = conversation_meta_data[file_key]
	with open(conversation_file, 'r') as f:
		conversation_json = json.load(f)
	messages = conversation_json[messages_key]
	for message in messages:
		try:
			output.append({'message_timestamp_ms': message[message_timestamp_ms],
						   'sender_name': message[sender_name],
						   'text': message[text],
						   'num_words': len(message[text].split(' '))})
		except KeyError:
			continue
	return output

def extract_messages(profiles_dir, text_out_dir, facebook_key = 'facebook'):
	"""
	Extracts messages from from Facebook data
	"""
	participants = get_participant_raw_directories(profiles_dir = profiles_dir)
	participant_output_dirs = get_participant_output_directories(text_out_dir = text_out_dir, profiles_dir = participants)
	profiles = get_social_media_directories(participants = participants)
	for profile in profiles:
		messages_meta_dic = get_message_files(profile_name = profile, facebook_profile_dir = profiles[profile][facebook_key])
		for conversation in messages_meta_dic:
			extract_conversation_text(profile = profile, conversation_meta_data = conversation, text_out_dir = participant_output_dirs[profile])

if __name__ == '__main__':
	PROFILES_DIR = os.getcwd() + '/profiles'
	TEXT_OUT_DIR = os.getcwd() + '/text_data'
	extract_messages(profiles_dir = PROFILES_DIR, 
					 text_out_dir = TEXT_OUT_DIR)