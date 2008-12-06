from trac.core import *
from trac.config import Option, IntOption, ListOption, BoolOption
from trac.web.api import IRequestFilter, IRequestHandler, Href
from hook import CommitHook
import simplejson

class GithubPlugin(Component):
    implements(IRequestHandler)
    
    key = Option('github', 'apitoken', '', doc="""Your GitHub API Token found here: https://github.com/account, """)

    def __init__(self):
        self.hook = CommitHook(self.env)
        self.env.log.debug("API Token: %s" % self.key)

    
    # IRequestHandler methods
    def match_request(self, req):
        self.env.log.debug("Request Method: %s" % req.method)
        self.env.log.debug("Request #1: %s" % req.path_info)
        self.env.log.debug("Request #2: %s" % req.path_info.rstrip('/'))
        serve = req.path_info.rstrip('/') == ('/github/%s' % self.key) and req.method == 'POST'
        self.env.log.debug("Match Request: %s" % serve)
        self.env.log.debug("Match Token: %s" % req.form_token)
        self.env.log.debug("Match Token: %s" % req.args.get('__FORM_TOKEN'))
        if serve:
            #This is hacky but it's the only way I found to let Trac post to this request
            #   without a valid form_token
            req.form_token = None
        return serve
    
    def process_request(self, req):
        self.env.log.debug("Process Request")
        self.env.log.debug("Request Data: %s" % req.read())

        #Not sure why this part is breaking? Noting is coming in from the request..
        #May be related to the Hack??
            
        #try:
        #data = simplejson.loads(req.read())

        #for sha1, commit in data['commits'].items():
        #    self.env.log.debug("Commit %s:" % commit)
            #self.hook.process(commit)
        #req.send_response(200)
        #req.send_header('Content-Type', 'text/plain')
        #req.end_headers()
        #req.write('Hello world!')
        #except json.ReadException, e:
        #    req.send_response(400)
        #    req.send_header('Content-type', 'text/plain')
        #    req.end_headers()
        #    req.write(e.message)
