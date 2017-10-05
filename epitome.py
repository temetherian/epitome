#!/usr/bin/python

import cloudstorage as gcs
import jinja2
import os
import webapp2

from google.appengine.api import app_identity

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

class FrontPage(webapp2.RequestHandler):
  def get(self):
    template = JINJA_ENVIRONMENT.get_template('index.html')
    self.response.write(template.render())

class NewTournamentPage(webapp2.RequestHandler):
  def get(self):
    bucket_name = os.environ.get('BUCKET_NAME',
                                 app_identity.get_default_gcs_bucket_name())
    files = gcs.listbucket('/' + bucket_name)
    existing_names = ",".join("'%s'" % f.filename.split('/')[2] for f in files)
    template_values = {'existing_names': existing_names}
    template = JINJA_ENVIRONMENT.get_template('templates/new.html')
    self.response.write(template.render(template_values))

class CreateTournamentHandler(webapp2.RequestHandler):
  def post(self):
    tourney_name = self.request.get('tname').lower()
    codeword = self.request.get('codeword')
    # then store these somewhere

class ServeTomeHandler(webapp2.RequestHandler):
  def get(self, tourney_name):
    tourney_name = tourney_name.lower()
    bucket_name = os.environ.get('BUCKET_NAME',
                                 app_identity.get_default_gcs_bucket_name())
    filename = '/%s/%s/export.js' % (bucket_name, tourney_name)
    export_data = gcs.open(filename)
    self.response.headers['Content-Type'] = 'text/plain'
    self.response.write(export_data.read())
    export_data.close()

class ManageTournamentPage(webapp2.RequestHandler):
  def get(self, tourney_name):
    template_values = {'tourney_name': tourney_name}
    template = JINJA_ENVIRONMENT.get_template('templates/manage.html')
    self.response.write(template.render(template_values))

class UpdateHandler(webapp2.RequestHandler):
  def post(self, tourney_name):
    tourney_name = tourney_name.lower()
    bucket_name = os.environ.get('BUCKET_NAME',
                                 app_identity.get_default_gcs_bucket_name())
    filename = '/%s/%s/export.js' % (bucket_name, tourney_name)
    codeword = self.request.get('codeword')
    # check that codeword is correct
    data = self.request.get('export')
    with gcs.open(filename, 'w', content_type='text/plain') as export_data:
      export_data.write(data)
    template_values = {'tourney_name': tourney_name} # and success information
    template = JINJA_ENVIRONMENT.get_template('templates/manage.html')
    self.response.write(template.render(template_values))

class TournamentPage(webapp2.RequestHandler):
  def get(self, tourney_name):
    tourney_name = tourney_name.lower()
    template_values = {'tourney_name': tourney_name}
    template = JINJA_ENVIRONMENT.get_template('templates/tourney.html')
    self.response.write(template.render(template_values))

ROUTES = [
  ('/', FrontPage),
  ('/new', NewTournamentPage),
  ('/create', CreateTournamentHandler),
  ('/([A-Za-z0-9\-]+)/tome.json', ServeTomeHandler),
  ('/([A-Za-z0-9\-]+)/manage/', ManageTournamentPage),
  ('/([A-Za-z0-9\-]+)/update', UpdateHandler),
  ('/([A-Za-z0-9\-]+)/', TournamentPage),
]

app = webapp2.WSGIApplication(routes=ROUTES)
