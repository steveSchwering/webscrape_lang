import sys
import pathlib
import logging
from concurrent.futures import ThreadPoolExecutor

from Goodreads import Goodreads

class Dispatcher():
	def __init__(self, max_threads = 5):
		self.queue = []
		self.history = []

		self.clients = {}

		self.executor = ThreadPoolExecutor(max_workers = max_threads)

	def add_client(self, client:type, client_id:str,
				   jobs_accepted:list = [],
				   **kwargs):
		"""
		Generates client objects and stores in clients dictionary
		"""
		if client_id in self.clients.keys():
			print('Clent ID already in use')
			return False

		# Get list of methods in function
		if not jobs_accepted:
			jobs_accepted = [func for func in dir(client) 
							 if callable(getattr(client, func)) and 
							 not func.startswith("__")]
		else:
			try:
				jobs_accepted = [getattr(client, func) for func in jobs_accepted]
			except AttributeError:
				print('Cannot get acceptable jobs')
				sys.exit()

		# Add client to client list
		self.clients.update({
			client_id : {
				'client_name'   : client.__name__,
				'client_class'  : client,
				'client_obj'    : client(client_id = client_id, **kwargs),
				'jobs_accepted' : jobs_accepted,
				'jobs_assigned' : 0
			}
		})

		return True

	def select_client(self, job):
		"""
		Selects a client for the job
		"""
		# Check if any clients exist
		if not bool(self.clients):
			print('Cannot give job to client without any clients')
			sys.exit()
		# Assume no selection will be found
		selected_id = None
		for client_id in self.clients:

			# Only choose clients with selected job skills
			if job in self.clients[client_id]['jobs_accepted']:
				try: # Choose the client with the least use
					s_jobs_assigned = self.clients[selected_id]['jobs_assigned']
					c_jobs_assigned = self.clients[client_id]['jobs_assigned']
					if (s_jobs_assigned > c_jobs_assigned):
						selected_id = client_id
					else:
						continue
				except: # If no client has been selected yet
					selected_id = client_id

		self.clients[selected_id]['jobs_assigned'] += 1 
		return selected_id


	def submit_job(self, job, **kwargs):
		"""
		Uses ThreadPoolExecutor to schedule and complete jobs
		https://stackoverflow.com/questions/31159165/python-threadpoolexecutor-on-method-of-instance
		"""
		if not bool(self.clients):
			print('Cannot give job to client without any clients')
			sys.exit()

		client_id = self.select_client(job = job)
		method = getattr(self.clients[client_id]['client_obj'], job) # This must be a BOUND method of the specific class instance

		self.executor.submit(method, **kwargs)

	def collect_responses(self):
		"""
		"""
		pass

	def get_jobs(self, job_path):
		"""
		Get jobs from files on disc. Job type given by folder in which jobs ar elocated.
		"""
		job_type = path.parents[0].name

		with open(job_path, 'r') as f:
			all_job_info = [job.strip() for job in f.readlines()]

		jobs = []
		for job_info in all_job_info:
			jobs.append({
				'job_type' : job_type,
				'job_info' : job_info
			})

		return jobs

if __name__ == '__main__':
	d = Dispatcher()
	d.add_client(client = Goodreads, client_id = 'searcher', jobs_accepted = ['search_api'], log = 'dispatch')
	d.add_client(client = Goodreads, client_id = 'worker_1', log = 'dispatch')
	d.add_client(client = Goodreads, client_id = 'worker_2', log = 'dispatch')
	d.add_client(client = Goodreads, client_id = 'worker_3', log = 'dispatch')
	d.submit_job(job = 'search_api', search_term = 'the golden compass')
	d.submit_job(job = 'search_api', search_term = 'game of thrones')
	d.submit_job(job = 'search_api', search_term = 'muffins')
	d.submit_job(job = 'search_api', search_term = 'squares')
	d.submit_job(job = 'search_api', search_term = 'dogs')
	d.submit_job(job = 'search_api', search_term = 'cats')
	d.submit_job(job = 'search_api', search_term = 'horses')