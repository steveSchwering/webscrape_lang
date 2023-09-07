import os
import pandas
from apiclient.discovery import build

def get_channels(youtube_kids_sources):
	"""
	Accesses target channels
	"""
	try:
		assert os.path.exists(youtube_kids_sources)
		kids_sources = pandas.read_csv(youtube_kids_sources)
		return kids_sources
	except AssertionError:
		print('Error accessing {}. Cannot retrieve target Youtube channels.'.format(self.youtube_kids_sources))
		return None
	except TypeError:
		print("Must define target channels for Youtube API requests".format())
		return None

def save_playlist_video_info(channel_id, videos_json, 
							 file_info = {'dir': os.getcwd() + '/channel_videos/',
							 			  'extension': '.csv', 
							 			  'separator': ',', 
							 			  'newline': '\n'},
							 output_order = ['channel_id',
							 				 'channel_title',
							 				 'playlist_id',
							 				 'video_id', 
							 				 'video_publish_date',
							 				 'video_title',
							 				 'video_description']):
	"""
	Saves returned video information in a channel-level file
	"""
	if not os.path.exists(file_info['dir']):
		os.mkdir(file_info['dir'])
	filename = file_info['dir'] + channel_id + file_info['extension']
	to_write = {}
	# Defaults to saving one file per channel
	with open(filename, 'w') as f:
		header = file_info['separator'].join(output_order)
		header += file_info['newline']
		f.write(header)
		for video_json in videos_json:
			to_write['channel_id'] = video_json['snippet']['channelId']
			to_write['channel_title'] = video_json['snippet']['channelTitle'].strip().replace(',', '').replace('\n', ' ').replace('\r', ' ')
			to_write['playlist_id'] = video_json['snippet']['playlistId']
			to_write['video_id'] = video_json['snippet']['resourceId']['videoId']
			to_write['video_publish_date'] = video_json['snippet']['publishedAt']
			to_write['video_title'] = video_json['snippet']['title'].strip().replace(',', '').replace('\n', ' ').replace('\r', ' ')
			to_write['video_description'] = video_json['snippet']['description'].strip().replace(',', '').replace('\n', ' ').replace('\r', ' ')
			output = []
			for out_elem in output_order:
				output.append(to_write[out_elem])
			output = file_info['separator'].join(output)
			output += file_info['newline']
			f.write(output)

def request_videos_from_playlist(youtube_api, playlist_id, next_page_token = None, 
								 videos_key = 'items', 
								 next_page_token_key = 'nextPageToken'):
	"""
	Pulls information about a video for a given playlist
	"""
	playlist_response = youtube_api.playlistItems().list(playlistId = playlist_id,
														 part = 'snippet',
														 maxResults = 50,
														 pageToken = next_page_token).execute()
	videos = playlist_response[videos_key]
	next_page_token = playlist_response.get(next_page_token_key)
	if next_page_token is None:
		return videos
	else:
		videos += request_videos_from_playlist(youtube_api = youtube_api, playlist_id = playlist_id, next_page_token = next_page_token)
		return videos

def request_playlist(channel_info, youtube_api, 
					 channel_id = 'channel_id',
					 channel_requested_info = 'contentDetails',
					 channel_items = 'items',
					 channel_relevant_item_index = 0,
					 channel_contents = 'contentDetails',
					 channel_playlists = 'relatedPlaylists',
					 target_playlist = 'uploads'):
	"""
	For a given channel, accesses a playlist on that channel. 
	Defaults to accessing the uploads playlist, which contains all videos uploaded to that channel.
	"""
	channel_json = youtube_api.channels().list(id = channel_info[channel_id], 
											   part = channel_requested_info).execute()
	playlist_id = channel_json[channel_items][channel_relevant_item_index][channel_contents][channel_playlists][target_playlist]
	videos_json = request_videos_from_playlist(youtube_api, playlist_id)
	save_playlist_video_info(channel_info[channel_id], videos_json)

def main(api_key, youtube_kids_sources):
	"""
	Reads in channels, establishes api credentials, and begins making requests to api for info about each channel
	"""
	channels = get_channels(youtube_kids_sources = youtube_kids_sources)
	youtube_api = build('youtube', 'v3', developerKey = api_key)
	channels.apply(lambda row: request_playlist(channel_info = row, youtube_api = youtube_api), axis = 1)

if __name__ == '__main__':
	api_key = 'AIzaSyCIxzrknfCIfptXXhuhtjSbC6Mdwj9wWP0'
	main(api_key = api_key, youtube_kids_sources = os.getcwd() + '/youtube_channels.csv')