import webapp2
import jinja2
import os
import json
import logging

import headers

from urlparse import urlparse

#http://content.guardianapis.com/uk/gallery/2012/dec/18/queen-visits-downing-street-pictures?format=json&show-related=true&tag=type%2Fgallery&order-by=newest

def related_galleries(page_url):
	params = {"format" : "json",
		"show-related" : "true",
		"tag" : "type/gallery",
		"order-by" : "newest",}

	parsed_url = urlparse(page_url)

	content_api_url = "http://content.guardianapis.com" + parsed_url.path

	logging.info(content_api_url)

	return None


class RelatedGalleries(webapp2.RequestHandler):
	def get(self):
		if "page-url" in self.request.params:
			related_galleries(self.request.params["page-url"])
		data = {"hello" : "world",}
		headers.set_cors_headers(self.response)
		headers.json(self.response)
		self.response.out.write(json.dumps(data))

app = webapp2.WSGIApplication([
	('/related/galleries', RelatedGalleries),],
	debug=True)