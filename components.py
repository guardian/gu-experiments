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



class MostPopularByCountry(webapp2.RequestHandler):
	def get(self, country_code="us", entries="5"):
		template = jinja_environment.get_template("most-popular.html")

		cache_key = "ophan_list_{0}".format(country_code)

		ophan_list_data = memcache.get(cache_key)

		if not ophan_list_data:
			ophan_list_data = ophan.popular_by_country(country_code=country_code)
			memcache.set(cache_key, ophan_list_data, 60)

		content_list = []

		if ophan_list_data:
			ophan_list = json.loads(ophan_list_data)
			content_list = [content_api.content_id(result['url']) for result in ophan_list]
			content_list = [content_api.read(path, params={"show-fields" : "headline,thumbnail"}) for path in content_list]
			content_list = [json.loads(result) for result in content_list if result]
			content_list = [result["response"]["content"] for result in content_list if content_api.response_ok(result)]
			content_list = content_list[0:int(entries)]

		country_name_lookup = {
			"us" : "in the US",
			"au" : "in Australia",
		}

		data ={
			"most_popular" : content_list,
			"component_title" : "Most popular {0}".format(country_name_lookup.get(country_code, "")),
		}

		headers.set_cors_headers(self.response)
		self.response.out.write(template.render(data))

class MostPopular(webapp2.RequestHandler):
	def get(self, entries="5"):
		template = jinja_environment.get_template("most-popular.html")

		cache_key = "ophan_list_popular"

		ophan_list_data = memcache.get(cache_key)

		if not ophan_list_data:
			ophan_list_data = ophan.popular()
			memcache.set(cache_key, ophan_list_data, 60)

		content_list = []

		if ophan_list_data:
			ophan_list = json.loads(ophan_list_data)
			content_list = [content_api.content_id(result['url']) for result in ophan_list]
			content_list = [content_api.read(path, params={"show-fields" : "headline,thumbnail"}) for path in content_list]
			content_list = [json.loads(result) for result in content_list if result]
			content_list = [result["response"]["content"] for result in content_list if content_api.response_ok(result)]
			content_list = content_list[0:int(entries)]

		data ={
			"most_popular" : content_list,
			"component_title" : "Most popular",
		}

		headers.set_cors_headers(self.response)
		self.response.out.write(template.render(data))

app = webapp2.WSGIApplication([
	('/components/most-popular/(\w{2})/(\d+)', MostPopularByCountry),
	('/components/most-popular/(?P<entries>\d+)', MostPopular),],
	debug=True)