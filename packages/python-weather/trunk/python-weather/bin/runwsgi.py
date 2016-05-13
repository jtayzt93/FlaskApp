#!/usr/bin/env python
from wsgiref.simple_server import make_server
from Weather.interface import wsgi
print "Serving HTTP on port 8000..."
make_server('', 8000, wsgi).serve_forever()