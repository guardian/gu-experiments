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

def most_popular_ophan_cache_key(country_code, section):
	cache_key = "ophan_list_{0}".format(country_code)

	if section:
		cache_key = cache_key + "_{0}".format(section)
	return cache_key

class MostPopularByCountry(webapp2.RequestHandler):
	def get(self, country_code="us", entries="5", section=None):
		template = jinja_environment.get_template("most-popular.html")

		cache_key = most_popular_ophan_cache_key(country_code, section)

		ophan_list_data = memcache.get(cache_key)

		if not ophan_list_data:
			ophan_list_data = []
			if section:
				ophan_list_data = ophan.popular_by_country(country_code=country_code, section_id=section)
			else:
				ophan_list_data = ophan.popular_by_country(country_code=country_code)

			memcache.set(cache_key, ophan_list_data, 60)

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
			"ca" : "in Canda",
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

class RecipeBox(webapp2.RequestHandler):
	def get(self, entries="4"):
		template = jinja_environment.get_template("recipe-box.html")
		headers.set_cors_headers(self.response)

		last_60_days = date.today() - timedelta(days=60)

		query = {
			"tag" : "tone/recipes",
			"show-fields" : "headline,thumbnail",
			"page-size" : 50,
			"from-date" : last_60_days.isoformat(),
		}

		content = content_api.search(query)

		if not content:
			webapp2.abort(500, "Failed to read recipes list")

		content_data = json.loads(content)

		recipes = content_data.get("response", {}).get("results", [])

		recipes = [r for r in recipes if "thumbnail" in r.get("fields", {})]
		random.shuffle(recipes)

		data = {
			"recipes" : recipes[0:int(entries)],
		}


		self.response.out.write(template.render(data))

class AuthorRecipeBox(webapp2.RequestHandler):
	def get(self, entries="4"):
		template = jinja_environment.get_template("recipe-box.html")
		headers.set_cors_headers(self.response)

		if not "path" in self.request.params:
			webapp2.abort(400, "No path specified")

		content = content_api.read(self.request.params["path"], {"show-tags" : "contributor"})
		content_data = json.loads(content)

		authors = [tag for tag in content_data["response"]["content"]["tags"] if tag["type"] == "contributor"]

		if not authors:
			webapp2.abort(500, "No contributors identified")

		first_author = authors[0]

		last_60_days = date.today() - timedelta(days=60)

		query = {
			"tag" : "tone/recipes,{author_id}".format(author_id=first_author["id"]),
			"show-fields" : "headline,thumbnail",
			"page-size" : 50,
			"from-date" : last_60_days.isoformat(),
		}

		content = content_api.search(query)

		if not content:
			webapp2.abort(500, "Failed to read recipes list")

		content_data = json.loads(content)

		recipes = content_data.get("response", {}).get("results", [])

		recipes = [r for r in recipes if "thumbnail" in r.get("fields", {})]
		random.shuffle(recipes)

		data = {
			"author" : authors[0],
			"recipes" : recipes[0:int(entries)],
		}


		self.response.out.write(template.render(data))

class SeriesRandomBox(webapp2.RequestHandler):
	def get(self, entries=4):
		template = jinja_environment.get_template("boxes/series.html")
		template_values = {}
		headers.set_cors_headers(self.response)

		if not "path" in self.request.params:
			webapp2.abort(400, "No path specified")

		path = self.request.params["path"]
		content = content_api.read(path, {"show-tags" : "series"})
		content_data = json.loads(content)

		series_tags = [t for t in content_data.get("response", {}).get("content", {}).get("tags",[]) if t.get("type", "") == "series"]

		if not len(series_tags) == 1:
			if series_tags:
				logging.warning("Content did not have a single series tag: %s" % path)
			for tag in series_tags:
				logging.debug(tag)
			webapp2.abort(500, "Single series tag not available")

		series_tag = series_tags[0]
		#logging.info(series_tag)

		query = {
			"tag" : series_tag["id"],
			"show-fields" : "headline,thumbnail",
			"page-size" : 50,
		}

		content = content_api.search(query)

		if not content:
			abort(404, "No content found for series tag")

		content_data = json.loads(content)

		items = content_data.get("response", {}).get("results", [])

		valid_items = [i for i in items if "thumbnail" in i.get("fields", {}) and i['id'] != path[1:]]
		random.shuffle(valid_items)

		template_values["series_name"] = series_tag['webTitle']
		template_values["series_content"] = valid_items[:entries]

		self.response.out.write(template.render(template_values))

class SeriesOrderedBox(webapp2.RequestHandler):
	def get(self, entries=4):
		template = jinja_environment.get_template("boxes/series.html")
		template_values = {}
		headers.set_cors_headers(self.response)

		if not "path" in self.request.params:
			webapp2.abort(400, "No path specified")

		path = self.request.params["path"]
		content_id = path[1:]

		content = content_api.read(path, {"show-tags" : "series"})
		content_data = json.loads(content)

		series_tags = [t for t in content_data.get("response", {}).get("content", {}).get("tags",[]) if t.get("type", "") == "series"]

		if not len(series_tags) == 1:
			if series_tags:
				logging.warning("Content did not have a single series tag: %s" % path)
			for tag in series_tags:
				logging.debug(tag)
			webapp2.abort(500, "Single series tag not available")

		series_tag = series_tags[0]
		#logging.info(series_tag)

		query = {
			"tag" : series_tag["id"],
			"show-fields" : "headline,thumbnail",
			"page-size" : 50,
		}

		content = content_api.search(query)

		if not content:
			abort(404, "No content found for series tag")

		content_data = json.loads(content)

		items = content_data.get("response", {}).get("results", [])

		content_index = [c["id"] for c in items].index(content_id)
		logging.info(content_index)

		valid_items = [i for i in items if "thumbnail" in i.get("fields", {}) and i['id'] != content_id]

		template_values["series_name"] = series_tag['webTitle']
		total_items = len(valid_items)
		window = (entries / 2)
		min_index = content_index - window
		max_index = content_index + window

		if min_index < 0:
			max_index += (-1 * min_index)
			min_index = 0

		if max_index > total_items:
			min_index -= (max_index - total_items)
			max_index = total_items
		logging.info(min_index)
		logging.info(max_index)
		template_values["series_content"] = valid_items[min_index:max_index]

		self.response.out.write(template.render(template_values))

app = webapp2.WSGIApplication([
	('/components/most-popular/(\w{2})/(\d+)', MostPopularByCountry),
	('/components/most-popular/(\w{2})/(\d+)/section/(?P<section>[a-z-]+)', MostPopularByCountry),
	('/components/most-popular/(?P<entries>\d+)', MostPopular),
	('/components/recipes/more-by-author/(?P<entries>\d+)', AuthorRecipeBox),
	('/components/recipes/more/(?P<entries>\d+)', RecipeBox),
	('/components/series/random', SeriesRandomBox),
	('/components/series/ordered', SeriesOrderedBox),],
	debug=True)