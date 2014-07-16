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

class SentimentDashboard(webapp2.RequestHandler):
	def get(self):

		template = jinja_environment.get_template("pages/sentiment-dashboard.html")
		template_values = {}

		self.response.out.write(template.render(template_values))

class SentimentWidget(webapp2.RequestHandler):
	def get(self):

		template = jinja_environment.get_template("pages/sentiment-widget.html")
		template_values = {}

		self.response.out.write(template.render(template_values))
app = webapp2.WSGIApplication([
	webapp2.Route(r'/pages/dashboards/sentiment', handler=SentimentDashboard),
	webapp2.Route(r'/pages/widgets/sentiment', handler=SentimentWidget),
	],
	debug=True)