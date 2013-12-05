import configuration

import webapp2
import jinja2
import os
import json
import logging

import headers

from google.appengine.api.urlfetch import fetch
from google.appengine.api import memcache
from urlparse import urlparse
import urllib

import ophan
import content_api

jinja_environment = jinja2.Environment(
	loader=jinja2.FileSystemLoader(os.path.join(os.path.dirname(__file__), "templates")))



class USMostPopular(webapp2.RequestHandler):
	def get(self):
		template = jinja_environment.get_template("most-popular.html")

		ophan_list_data = memcache.get("ophan_list")

		if not ophan_list_data:
			ophan_list_data = ophan.popular_by_country(country_code="us")
			memcache.set("ophan_list", ophan_list_data, 60)

		content_list = []

		if ophan_list_data:
			ophan_list = json.loads(ophan_list_data)
			content_list = [content_api.content_id(result['url']) for result in ophan_list]
			content_list = [content_api.read(path) for path in content_list]
			content_list = [json.loads(result) for result in content_list if result]
			content_list = [result["response"]["content"] for result in content_list if content_api.response_ok(result)]

		data ={"hello" : content_list}

		headers.set_cors_headers(self.response)
		self.response.out.write(template.render(data))

app = webapp2.WSGIApplication([
	('/components/most-popular/us', USMostPopular),],
	debug=True)