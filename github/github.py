from trac.core import *
from trac.config import Option, IntOption, ListOption, BoolOption
from trac.web.api import IRequestFilter, IRequestHandler, Href, RequestDone
from trac.util.translation import _
from hook import CommitHook

import re
import simplejson

from git import Git

class GithubPlugin(Component):
    implements(IRequestHandler, IRequestFilter)
    
    
    key = Option('github', 'apitoken', '', doc="""Your GitHub API Token found here: https://github.com/account, """)
    closestatus = Option('github', 'closestatus', '', doc="""This is the status used to close a ticket. It defaults to closed.""")
    username = Option('github', 'username', '', doc="""your github user or organisation name""")
    autofetch = Option('github', 'autofetch', '', doc="""Should we auto fetch the repo when we get a commit hook from GitHub.""")
    repo = Option('trac', 'repository_dir' '', doc="""This is your repository dir""")
    gitreposdir = Option('github', 'gitreposdir' '', doc="""This is the path where all your git repo are""")

    def __init__(self):
        self.hook = CommitHook(self.env)
        self.env.log.debug("API Token: %s" % self.key)
        self.env.log.debug("Username: %s" % self.username)
        self.processHook = False

    
    # IRequestHandler methods
    def match_request(self, req):
        self.env.log.debug("Match Request")
        serve = req.path_info.rstrip('/') == ('/github/%s' % self.key) and req.method == 'POST'
        if serve:
            self.processHook = True
            #This is hacky but it's the only way I found to let Trac post to this request
            #   without a valid form_token
            req.form_token = None

        self.env.log.debug("Handle Request: %s" % serve)
        return serve
    
    def process_request(self, req):
        if self.processHook:
            self.processCommitHook(req)
        
        req.send_response(204)
        req.send_header('Content-Length', 0)
        req.write('')
        raise RequestDone

    # This has to be done via the pre_process_request handler
    # Seems that the /browser request doesn't get routed to match_request :(
    def pre_process_request(self, req, handler):
	if not self.username:
		return handler

	isBrowser = req.path_info.startswith('/browser/')
	if isBrowser: 
		uri = req.path_info.split('/');
		projectName = uri[2]
		repoType = "%s" % self.env.get_repository(projectName)
		isGitRepo = False
		if repoType.find('Git') != -1:
			isGitRepo = True
		self.env.log.debug("Handle Pre-Request /browser: %s" % isGitRepo)
		if isGitRepo:
			self.processBrowserURL(req, projectName)

	isChangeset = req.path_info.startswith('/changeset')
	self.env.log.debug("REQUEST %s" % req.path_info)
	if isChangeset:	    
		info = req.path_info.split('/');
		rev=info[2]
		projectName=info[3]
		self.env.log.debug("Handle Pre-Request /changeset: %s" % info)
		if not rev.isdigit(): # digit = svn, not digit = sha1 = git
			self.processChangesetURL(req, projectName, rev)

        return handler


    def post_process_request(self, req, template, data, content_type):
        return (template, data, content_type)


    def processChangesetURL(self, req, projectName, rev):
        self.env.log.debug("processChangesetURL")
        
        url = req.path_info.replace('/changeset/', '')
        if not url:
            url = ''

        redirect = 'https://github.com/%s/%s/commit/%s' % (self.username, projectName, rev)
        self.env.log.debug("Redirect URL: %s" % redirect)
        out = 'Going to GitHub: %s' % redirect

        req.redirect(redirect)


    def processBrowserURL(self, req, projectName):
        self.env.log.debug("processBrowserURL")
        rev = req.args.get('rev')
        self.env.log.debug("rev %s" % rev)
        url = req.path_info.replace('/browser', '')
        if not rev:
            rev = ''
        self.env.log.debug("url %s" % url)
        redirect = 'https://github.com/%s/%s' % (self.username, projectName)
        self.env.log.debug("Redirect URL: %s" % redirect)
        out = 'Going to GitHub: %s' % redirect

        req.redirect(redirect)
        

    def processCommitHook(self, req):
        self.env.log.debug("processCommitHook")
        status = self.closestatus
        if not status:
            status = 'closed'
	
        data = req.args.get('payload')
	jsondata = simplejson.loads(data)
		
	repoName = jsondata['repository']['name']

        if self.autofetch:
	    if data:
	    	jsondata = simplejson.loads(data)
		self.env.log.debug(jsondata['repository']['name']);
	        repo = Git(self.gitreposdir+repoName+"/.git")

            try:
              self.env.log.debug("Fetching repo %s" % self.repo)
              repo.execute(['git', 'fetch'])
              try:
                self.env.log.debug("Resyncing local repo")
                self.env.get_repository(repoName).sync()
              except:
                self.env.log.error("git sync failed!")
            except:
              self.env.log.error("git fetch failed!")

        jsondata = simplejson.loads(data)

         
        if jsondata:
            if jsondata['ref'] == "refs/heads/master" or re.search('-stable$', jsondata['ref']):
                for i in jsondata['commits']:
                    self.hook.process(i, status)
