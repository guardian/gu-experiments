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

class UserInteraction(webapp2.RequestHandler):
	def get(self):
		headers.set_cors_headers(self.response)
		headers.json(self.response)

		template = jinja_environment.get_template("js/user-interaction.js")
		template_values = {}

		self.response.out.write(template.render(template_values))

app = webapp2.WSGIApplication([
	webapp2.Route(r'/js/ng-user-interaction.js', handler=UserInteraction),
	],
	debug=True)