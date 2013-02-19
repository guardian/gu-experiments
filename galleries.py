import configuration

import webapp2
import jinja2
import os
import json
import logging

import headers

from google.appengine.api.urlfetch import fetch
from urlparse import urlparse
import urllib

jinja_environment = jinja2.Environment(
	loader=jinja2.FileSystemLoader(os.path.join(os.path.dirname(__file__), "templates")))


#http://content.guardianapis.com/uk/gallery/2012/dec/18/queen-visits-downing-street-pictures?format=json&show-related=true&tag=type%2Fgallery&order-by=newest

def related_galleries(page_url):
	params = {"format" : "json",
		"show-related" : "true",
		"tag" : "type/gallery",
		"order-by" : "newest",
		"show-fields" : "thumbnail,headline",}

	parsed_url = urlparse(page_url)

	content_api_url = "http://content.guardianapis.com" + parsed_url.path + "?" + urllib.urlencode(params)

	logging.info(content_api_url)

	result = fetch(content_api_url, deadline = 9)

	if not result.status_code == 200:
		return None

	data = json.loads(result.content)

	logging.info(data)

	if not "relatedContent" in data["response"]: return None

	return data["response"]["relatedContent"]

def all_images(page_url):
	params = {"format" : "json",
		"show-media" : "picture",
		"order-by" : "newest",
		"show-fields" : "thumbnail,headline",
		"api-key" : configuration.lookup("CONTENT_API_KEY"),}

	parsed_url = urlparse(page_url)

	content_api_url = "http://content.guardianapis.com" + parsed_url.path + "?" + urllib.urlencode(params)

	logging.info(content_api_url)

	result = fetch(content_api_url, deadline = 9)

	if not result.status_code == 200:
		return []

	data = json.loads(result.content)

	logging.info(data)

	return data.get("response", {}).get("content", {}).get("mediaAssets", [])

class RelatedGalleries(webapp2.RequestHandler):
	def get(self):
		template = jinja_environment.get_template("related-galleries.html")

		data = {"title" : "Related galleries",}
		if "page-url" in self.request.params:
			data["galleries"] = related_galleries(self.request.params["page-url"])[:4]

		headers.set_cors_headers(self.response)
		self.response.out.write(template.render(data))

class AllImages(webapp2.RequestHandler):
	def get(self):
		template = jinja_environment.get_template("all-images-gallery.html")
		template_values = {}

		if "page-url" in self.request.params:
			template_values["images"] = all_images(self.request.params["page-url"])

		headers.set_cors_headers(self.response)
		self.response.out.write(template.render(template_values))

app = webapp2.WSGIApplication([
	('/related/galleries', RelatedGalleries),
	('/galleries/all-pictures', AllImages),],
	debug=True)