import random

import configuration

import webapp2
import jinja2
import os
import json
import logging

from datetime import date, timedelta

import headers

from google.appengine.api.urlfetch import fetch
from google.appengine.api import memcache
from urlparse import urlparse
import urllib

import ophan
import content_api

jinja_environment = jinja2.Environment(
	loader=jinja2.FileSystemLoader(os.path.join(os.path.dirname(__file__), "templates")))

OPHAN_CACHE_SECONDS=90
CONTENT_CACHE_SECONDS=60

def most_popular_ophan_cache_key(country_code, section, hours, referrer):
	cache_key = "ophan_list_{0}".format(country_code)

	for item in [section, hours, referrer]:
		if item:
			cache_key = cache_key + "_{0}".format(item)

	return cache_key

class MostPopularFromOphan(webapp2.RequestHandler):
	def get(self, country_code="us", entries="5", section=None, hours="1", referrer=None):
		headers.set_cors_headers(self.response)
		headers.json(self.response)

		template = jinja_environment.get_template("most-popular.html")

		logging.info(self.request.path)

		cached_output = memcache.get(self.request.path)

		if cached_output:
			self.response.out.write(json.dumps(cached_output))
			return

		cache_key = most_popular_ophan_cache_key(country_code, section, hours, referrer)

		ophan_list_data = memcache.get(cache_key)

		if not ophan_list_data:

			ophan_list_data = ophan.popular_by_country(country_code=country_code, section_id=section, hours=hours, referrer=referrer)

			memcache.set(cache_key, ophan_list_data, OPHAN_CACHE_SECONDS)

		content_list = []

		if ophan_list_data:
			ophan_list = json.loads(ophan_list_data)
			content_list = [content_api.content_id(result['url']) for result in ophan_list]
			content_list = [content_api.read(path, params={"show-fields" : "headline,thumbnail"}) for path in content_list]
			content_list = [json.loads(result) for result in content_list if result]
			content_list = [result["response"]["content"] for result in content_list if content_api.response_ok(result)]
			content_list = [c for c in content_list if c.get("fields", {}).get("thumbnail", None)]
			content_list = content_list[0:int(entries)]

		country_name_lookup = {
			"us" : "in the US",
			"au" : "in Australia",
			"in" : "in India",
			"ca" : "in Canada",
		}

		data = {
			"most_popular" : content_list,
			"component_title" : "Most popular {0}".format(country_name_lookup.get(country_code, "")),
		}

		memcache.set(self.request.path, data, CONTENT_CACHE_SECONDS)

		self.response.out.write(json.dumps(data))

app = webapp2.WSGIApplication([
	('/data/most-popular/(?P<country_code>\w{2})/(?P<entries>\d+)/section/(?P<section>[a-z-]+)/hours/(?P<hours>\d+)', MostPopularFromOphan),
	('/data/most-popular/(?P<country_code>\w{2})/(?P<entries>\d+)', MostPopularFromOphan),
	('/data/most-popular/(?P<country_code>\w{2})/(?P<entries>\d+)/section/(?P<section>[a-z-]+)/hours/(?P<hours>\d+)/referrer/(?P<referrer>.+)', MostPopularFromOphan),
	],
	debug=True)