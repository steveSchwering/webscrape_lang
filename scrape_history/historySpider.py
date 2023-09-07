import os
import sys
import glob
import justext
import pandas
import scrapy
import helperfunctions as hf
from scrapy.crawler import CrawlerProcess

class HistorySpider(scrapy.Spider):
	name = 'history'

	def __init__(self, *args, **kwargs):
		super(HistorySpider, self).__init__(*args, **kwargs)
		self.url_log_file = kwargs.get('url_log_file')

	def check_output_folder(self, output_folder, overwrite = True):
		"""
		Creates output folder and checks if participant data has already been scraped
		"""
		try:
			if not overwrite:
				assert not os.path.exists(output_folder)
			os.mkdir(output_folder)
		except AssertionError:
			self.log('Output folder for {} spider already exists. Overwrite set to False. Aborting.'.format(self.name))
			sys.exit()
		except FileExistsError:
			pass

	def get_jobs_from_master_log(self, scraped_check_key = 'scraped'):
		"""
		Reads master log urls and returns the ones that haven't been scraped
		"""
		try:
			assert os.path.exists(self.url_log_file)
			extension = self.url_log_file.split('.')[-1]
			if extension == 'tsv':
				master_log = pandas.read_csv(self.url_log_file, sep = '\t')
			elif extension == 'csv':
				master_log = pandas.read_csv(self.url_log_file)
			master_log = master_log.loc[master_log[scraped_check_key].isnull()]
			return master_log
		except AssertionError:
			self.log('Error accessing {}. Cannot retrieve urls.'.format(self.url_log_file))
			return None
		except TypeError:
			self.log("Must define urls for spider {}".format(self.name))
			return None

	def start_requests(self, url_key = 'url', url_id_key = 'url_id'):
		"""
		Generator of requests
		"""
		# Generates output folder
		self.check_output_folder(output_folder = os.getcwd() + '/output/html')
		self.check_output_folder(output_folder = os.getcwd() + '/output/justext')
		# Pulls urls that need to be queried
		job_list = self.get_jobs_from_master_log()
		# Begins making requests
		for url, url_id in zip(job_list[url_key], job_list[url_id_key]):
			yield scrapy.Request(url = url, callback = self.parse, cb_kwargs = dict(url_id = url_id))

	def parse(self, response, url_id, out_dir_html = os.getcwd() + '/output/html/', out_dir_justext = os.getcwd() + '/output/justext/'):
		"""
		Directs how requests will be parsed
		"""
		yield self.parse_save_html(response = response, out_dir = out_dir_html, url_id = url_id)
		yield self.parse_justext(response = response, out_dir = out_dir_justext, url_id = url_id)

	def parse_save_html(self, response, out_dir, url_id):
		"""
		Parses webpages by saving html repsonse
		"""
		filename = '{}{}.html'.format(out_dir, url_id)
		with open(filename, 'wb') as f:
			f.write(response.body)
		self.log('Saved file {}'.format(filename))

	def parse_justext(self, response, out_dir, url_id):
		"""
		Parses webpages by scraping html using justext
		"""
		output = []
		paragraphs = justext.justext(response.body, justext.get_stoplist("English"))
		for paragraph in paragraphs:
			if not paragraph.is_boilerplate:
				for para in paragraph.text.split('\n'):
					for word in para.split(' '):
						output.append(word)
		filename = '{}{}.txt'.format(out_dir, url_id) 
		with open(filename, 'w') as f:
			for word in output:
				try:
					f.write(word + "\n")
				except UnicodeEncodeError:
					f.write(word.encode('utf-8') + "\n")
		self.log('Saved file {}'.format(filename))

if __name__ == '__main__':
	# Parameters
	url_log_file = os.getcwd() + '/input/master_url_log.tsv'
	# Build and send ot the spider
	process = CrawlerProcess({
		'USER_AGENT': 'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1)'
	})
	process.crawl(HistorySpider, url_log_file = url_log_file)
	process.start()