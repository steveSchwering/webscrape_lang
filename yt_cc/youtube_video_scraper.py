import os
import io
import sys
import glob
import pandas
from youtube_transcript_api import YouTubeTranscriptApi
"""
The best code is a github repository: https://github.com/jdepoix/youtube-transcript-api
Brilliant point in lines 125 and 126 of _api.py file which find how the youtube page gets its transcription
It finds the request made by searching for 'timedtext', noting its index, and locating the end of that string the site requests
Then, it requests that same site to access the transcript of a Youtube video
"""

def get_channel_videos(channels_folder, file_extension = '.csv'):
	return glob.glob(channels_folder + '*' + file_extension)

def get_videos(youtube_kids_sources):
	"""
	Accesses target channels
	"""
	try:
		assert os.path.exists(youtube_kids_sources)
		kids_sources = pandas.read_csv(youtube_kids_sources)
		return youtube_kids_sources, kids_sources
	except AssertionError:
		print('Error accessing {}. Cannot retrieve target Youtube channels.'.format(self.youtube_kids_sources))
		return None
	except TypeError:
		print("Must define target channels for Youtube API requests".format())
		return None

def save_cc(video_id, video_cc_json,
		 	file_info = {'dir': os.getcwd() + '/video_ccs/',
						 'extension': '.csv', 
						 'separator': ',', 
						 'newline': '\n'},
			output_order = ['video_id',
		 				    'start_text_time',
		 				    'duration_text',
		 				    'text']):
	if not os.path.exists(file_info['dir']):
		os.mkdir(file_info['dir'])
	filename = file_info['dir'] + video_id + file_info['extension']
	to_write = {}
	with open(filename, 'w') as f:
		header = file_info['separator'].join(output_order)
		header += file_info['newline']
		f.write(header)
		to_write['video_id'] = video_id
		for text_entry in video_cc_json:
			to_write['text'] = str(text_entry['text']).strip().replace(',', '').replace('\n', ' ').replace('\r', ' ')
			to_write['start_text_time'] = str(text_entry['start'])
			to_write['duration_text'] = str(text_entry['duration'])
			output = []
			for out_elem in output_order:
				output.append(to_write[out_elem])
			output = file_info['separator'].join(output)
			output += file_info['newline']
			f.write(output)

def request_video_cc(video_info, 
					 caption_request = 'snippet',
					 video_id_key = 'video_id', 
					 cc_format = 'ttml', 
					 cc_lang = 'en',
					 target_languages = ['en'],
					 video_cc_dir = 'video_ccs',
					 transcript_accessed = 'transcript_accessed'):
	try:
		if video_info['transcript_accessed'] == 1:
			return 1
		if video_info['transcript_accessed'] == 0:
			return 0
	except:
		pass
	try:
		# This is a nice module that does a lot of the parsing of the html. 
		# See top of script for my description of how it works.
		# Still not sure how it accesses asr text vs human-generated text, though
		# Probably involves setting kind=asr when accessing transcript. If this is the case, possibly note?
		# Or maybe I could try accessing the transcript without going through this rigamarole. If error, then we know transcript is asr.
		# But if we do get response, it won't be clear that response from this module is necessarily asr, as it could be human-generated...
		video_cc_json = YouTubeTranscriptApi.get_transcript(video_info[video_id_key], languages = target_languages)
		save_cc(video_info[video_id_key], video_cc_json)
		return 1
	except:
		print("Failed to get transcript {}".format(video_info[video_id_key]))
		return 0
	"""
	video_json = youtube_api.captions().list(videoId = video_info[video_id_key],
											 part = caption_request).execute()
	video_cc_request = youtube_api.captions().download(id = video_json[items][0]['id'], 
													   tfmt = cc_format, 
													   tlang = cc_lang).execute()
	output_cc_file = video_cc_dir + '/' + video_info[video_id_key]
	fh = io.FileIO(output_cc_file, "wb")
	download_cc = MediaIoBaseDownload(fh, video_cc_request)
	complete = False
	while not complete:
		status, complete = download_cc.next_chunk()
	sys.exit()
	"""

def main(channel_videos, api_key):
	for channel in channel_videos:
		filename, videos = get_videos(channel)
		videos['transcript_accessed'] = videos.apply(lambda row: request_video_cc(video_info = row), axis = 1)
		videos.to_csv(filename, index = False, index_label = False)

if __name__ == '__main__':
	api_key = 'AIzaSyCIxzrknfCIfptXXhuhtjSbC6Mdwj9wWP0'
	channel_videos = get_channel_videos(channels_folder = os.getcwd() + '/channel_videos/')
	main(channel_videos = channel_videos, api_key = api_key)
