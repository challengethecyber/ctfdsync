import os, requests
from urllib.parse import urljoin

class CtfdApi(requests.Session):
	def __init__(self):
		super(CtfdApi, self).__init__()

		self.ctfd_endpoint = os.getenv("CTFD_ENDPOINT")
		assert self.ctfd_endpoint is not None, "Missing CTFD_ENDPOINT"
		self.prefix_url = self.ctfd_endpoint.rstrip("/") + "/"
		assert self.prefix_url.endswith("/api/v1/"), "Must specify API endpoint for CTFd"

		self.ctfd_token = os.getenv("CTFD_TOKEN")
		assert self.ctfd_token is not None, "Missing CTFD_TOKEN"

		self.headers.update({"Authorization": f"Token {self.ctfd_token}"})
		
	def request(self, method, url, *args, **kwargs):
		url_start = self.prefix_url

		if kwargs.get('omit_prefix', False):
			url_start = self.prefix_url.rstrip("/api/v1/") + "/"
			del kwargs['omit_prefix']
			
		url = urljoin(url_start, url.lstrip("/"))
		
		if "files" not in kwargs:
			kwargs["headers"] = kwargs.get("headers", {})
			kwargs["headers"].update({"Content-Type": "application/json"})

		return super(CtfdApi, self).request(method, url, *args, **kwargs)
