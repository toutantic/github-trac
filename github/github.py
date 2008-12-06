from trac.core import *
from trac.config import Option, IntOption, ListOption, BoolOption
from trac.web import IRequestHandler
from hook import CommitHook
import simplejson

class GithubPlugin(Component):
    implements(IRequestHandler)
    
    GITHUB_KEY = Option('github', 'apitoken', '', 
        doc="""Your GitHub API Token found here: https://github.com/account, """)

    def __init__(self):
        self.hook = CommitHook(self.env)
    
    # IRequestHandler methods
    def match_request(self, req):
        return req.path_info.rstrip('/') == ('/github/%s' % GITHUB_KEY) and req.method == 'POST'
    
    def process_request(self, req):
        try:
            data = simplejson.loads(req.read())

            for sha1, commit in data['commits'].items():
                self.hook.process(commit)
            req.send_response(200)
            req.send_header('Content-Type', 'text/plain')
            req.end_headers()
            req.write('Hello world!')
        except json.ReadException, e:
            req.send_response(400)
            req.send_header('Content-type', 'text/plain')
            req.end_headers()
            req.write(e.message)
