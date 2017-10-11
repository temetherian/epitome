#!/usr/bin/python

import cloudstorage as gcs
import jinja2
import os
import urllib
import webapp2

from google.appengine.api import app_identity
from google.appengine.ext import ndb

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

class Tournament(ndb.Model):
  title = ndb.StringProperty()
  codeword = ndb.StringProperty()


################
# Web Handlers #
################

class FrontPage(webapp2.RequestHandler):
  def get(self):
    template = JINJA_ENVIRONMENT.get_template('templates/index.html')
    self.response.write(template.render())

class NewTournamentPage(webapp2.RequestHandler):
  def get(self):
    title = self.request.get('title', '')

    tourneys = Tournament.query()
    existing_names = ",".join("'%s'" % t.key.id() for t in tourneys)
    template_values = {'existing_names': existing_names,
                       'title': title}
    template = JINJA_ENVIRONMENT.get_template('templates/new.html')
    self.response.write(template.render(template_values))

class CreateTournamentHandler(webapp2.RequestHandler):
  def post(self):
    shortname = self.request.get('shortname').lower()
    title = self.request.get('title')
    codeword = self.request.get('codeword')

    if Tournament.get_by_id(shortname):
      params = {'title': title}
      self.redirect('/_to/new?' + urllib.urlencode(params))
    else:
      new_tournament = Tournament(id=shortname, title=title, codeword=codeword)
      new_tournament.put()
      self.redirect('/%s/manage' % shortname)

class ServeTomeHandler(webapp2.RequestHandler):
  def get(self, shortname):
    shortname = shortname.lower()
    bucket_name = os.environ.get('BUCKET_NAME',
                                 app_identity.get_default_gcs_bucket_name())
    filename = '/%s/%s/export.js' % (bucket_name, shortname)
    export_data = gcs.open(filename)
    self.response.headers['Content-Type'] = 'text/plain'
    self.response.write(export_data.read())
    export_data.close()

class ManageTournamentPage(webapp2.RequestHandler):
  def get(self, shortname):
    template_values = {'shortname': shortname}
    tourney = Tournament.get_by_id(shortname)
    if not tourney:
      self.response.set_status(404)
      self.response.write('Tournament not found.')
      return

    template = JINJA_ENVIRONMENT.get_template('templates/manage.html')
    self.response.write(template.render(template_values))

class UpdateHandler(webapp2.RequestHandler):
  def post(self, shortname):
    shortname = shortname.lower()
    tourney = Tournament.get_by_id(shortname)
    if not tourney:
      self.response.set_status(404)
      self.response.write('Tournament not found.')
      return

    codeword = self.request.get('codeword')
    if codeword != tourney.codeword:
      self.response.set_status(403)
      self.response.write("You didn't say the magic word.")
      return

    bucket_name = os.environ.get('BUCKET_NAME',
                                 app_identity.get_default_gcs_bucket_name())
    filename = '/%s/%s/export.js' % (bucket_name, shortname)
    data = self.request.get('export')
    with gcs.open(filename, 'w', content_type='text/plain') as export_data:
      export_data.write(data.encode('utf-8'))

    self.redirect('/%s/manage' % shortname)

class TournamentPage(webapp2.RequestHandler):
  def get(self, shortname):
    shortname = shortname.lower()
    tourney = Tournament.get_by_id(shortname)
    if not tourney:
      self.response.set_status(404)
      self.response.write('Tournament not found.')
      return
    template_values = {'shortname': shortname, 'title': tourney.title}
    template = JINJA_ENVIRONMENT.get_template('templates/tourney.html')
    self.response.write(template.render(template_values))

ROUTES = [
  ('/', FrontPage),
  ('/_to/new', NewTournamentPage),
  ('/_to/create', CreateTournamentHandler),
  ('/([A-Za-z0-9\-]+)/tome.json', ServeTomeHandler),
  ('/([A-Za-z0-9\-]+)/manage', ManageTournamentPage),
  ('/([A-Za-z0-9\-]+)/update', UpdateHandler),
  ('/([A-Za-z0-9\-]+)[/]?', TournamentPage),
]

app = webapp2.WSGIApplication(routes=ROUTES)
