#!/usr/bin/python

import cloudstorage as gcs
import jinja2
import json
import os
import re
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
  app = ndb.StringProperty(default='tome')

################
# API Handlers #
################

class ApiUsedNames(webapp2.RequestHandler):
  def get(self):
    """Return a JSON list of all shortnames already in use."""
    self.response.headers['Content-Type'] = 'application/json'
    r = {}
    tourneys = Tournament.query()
    existing_names = [k.id() for k in tourneys.iter(keys_only=True)]
    r['names'] = existing_names
    self.response.write(json.dumps(r))

class ApiCreate(webapp2.RequestHandler):
  def post(self):
    """Create a new tournament in epiTOME.

    The request should be application/x-www-form-urlencoded with:
      shortname: the tournament to be updated
      codeword: the secret codeword for that tournament
      app: ('nrtm' or 'tome') the tournament app being used
           optional -- when omitted, will act like 'tome'

    The response is JSON containing:
      success: (bool)
      msg: (str) An error message (on failure) or the shortname (on success)
    """
    shortname = self.request.get('shortname').lower()
    title = self.request.get('title')
    codeword = self.request.get('codeword')
    app = self.request.get('app')

    self.response.headers['Content-Type'] = 'application/json'
    r = {}
    if not re.match('^[a-z0-9\-]{3,}$', shortname):
      self.response.set_status(400)
      r['success'] = False
      r['msg'] = 'Shortnames must be at least 3 characters and use only a-z, 0-9, and hyphens.'
    elif Tournament.get_by_id(shortname):
      self.response.set_status(409)
      r['success'] = False
      r['msg'] = 'That shortname is already in use.'
    else:
      new_tournament = Tournament(id=shortname, title=title, codeword=codeword, app=app)
      new_tournament.put()
      r['success'] = True
      r['msg'] = shortname

    self.response.write(json.dumps(r))

class ApiUpdate(webapp2.RequestHandler):
  def post(self):
    """Update a tournament's export data in the blobstore.

    The request should be application/x-www-form-urlencoded with:
      shortname: the tournament to be updated
      codeword: the secret codeword for that tournament
      export: the exported JSON

    The response is JSON containing:
      success: (bool)
      msg: (optional str) an explanation of an unsuccessful update
    """
    shortname = self.request.get('shortname').lower()
    codeword = self.request.get('codeword')

    self.response.headers['Content-Type'] = 'application/json'
    r = {}
    tourney = Tournament.get_by_id(shortname)
    if not tourney:
      self.response.set_status(404)
      r['success'] = False
      r['msg'] = 'unknown tournament'
    elif codeword != tourney.codeword:
      self.response.set_status(403)
      r['success'] = False
      r['msg'] = 'incorrect codeword'
    else:
      bucket_name = os.environ.get('BUCKET_NAME',
                                   app_identity.get_default_gcs_bucket_name())
      filename = '/%s/%s/export.js' % (bucket_name, shortname)
      data = self.request.get('export')
      with gcs.open(filename, 'w', content_type='text/plain') as export_data:
        export_data.write(data.encode('utf-8'))
      r['success'] = True

    self.response.write(json.dumps(r))

################
# Web Handlers #
################

class FrontPage(webapp2.RequestHandler):
  def get(self):
    template = JINJA_ENVIRONMENT.get_template('templates/index.html')
    self.response.write(template.render())

class InfoPage(webapp2.RequestHandler):
  def get(self):
    template = JINJA_ENVIRONMENT.get_template('templates/to.html')
    self.response.write(template.render())

class NewTournamentPage(webapp2.RequestHandler):
  def get(self):
    title = self.request.get('title', '')

    tourneys = Tournament.query()
    existing_names = ",".join("'%s'" % k.id() for k in tourneys.iter(keys_only=True))
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

class ServeJsonHandler(webapp2.RequestHandler):
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

class ConfirmDeletePage(webapp2.RequestHandler):
  def get(self, shortname):
    template_values = {'shortname': shortname}
    tourney = Tournament.get_by_id(shortname)
    if not tourney:
      self.response.set_status(404)
      self.response.write('Tournament not found.')
      return

    template = JINJA_ENVIRONMENT.get_template('templates/delete.html')
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

class DeleteHandler(webapp2.RequestHandler):
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

    try:
      gcs.delete(filename)
    except gcs.NotFoundError:
      pass

    tourney.key.delete()

    self.redirect('/')

class TournamentPage(webapp2.RequestHandler):
  def get(self, shortname):
    shortname = shortname.lower()
    tourney = Tournament.get_by_id(shortname)
    if not tourney:
      self.response.set_status(404)
      self.response.write('Tournament not found.')
      return
    template_values = {'shortname': shortname, 'title': tourney.title}
    if tourney.app == 'nrtm':
      template = JINJA_ENVIRONMENT.get_template('templates/nrtm.html')
    else:
      template = JINJA_ENVIRONMENT.get_template('templates/tome.html')
    self.response.write(template.render(template_values))

ROUTES = [
  ('/', FrontPage),
  ('/_api/usednames', ApiUsedNames),
  ('/_api/create', ApiCreate),
  ('/_api/update', ApiUpdate),
  ('/_to/', InfoPage),
  ('/_to/new', NewTournamentPage),
  ('/_to/create', CreateTournamentHandler),
  ('/([A-Za-z0-9\-]+)/tome.json', ServeJsonHandler),
  ('/([A-Za-z0-9\-]+)/nrtm.json', ServeJsonHandler),
  ('/([A-Za-z0-9\-]+)/manage', ManageTournamentPage),
  ('/([A-Za-z0-9\-]+)/slums', ConfirmDeletePage),
  ('/([A-Za-z0-9\-]+)/delete', DeleteHandler),
  ('/([A-Za-z0-9\-]+)/update', UpdateHandler),
  ('/([A-Za-z0-9\-]+)[/]?', TournamentPage),
]

app = webapp2.WSGIApplication(routes=ROUTES)
