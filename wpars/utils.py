# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
"""
import os
import urllib2
import math
import requests

from datetime import timedelta
from flask import make_response, request, current_app
from functools import update_wrapper

from functools import wraps

def check_auth(username, password):
	return username == 'admin' and password == 'secret'

def authenticate():
	message = {'message': "Authenticate."}
	resp = jsonify(message)

	resp.status_code = 401
	resp.headers['WWW-Authenticate'] = 'Basic realm="Example"'

	return resp

def requires_auth(f):
	@wraps(f)
	def decorated(*args, **kwargs):
		auth = request.authorization
		if not auth: 
			return authenticate()

		elif not check_auth(auth.username, auth.password):
			return authenticate()
		return f(*args, **kwargs)

	return decorated

def crossdomain(origin=None, methods=None, headers=None,
				max_age=21600, attach_to_all=True,
				automatic_options=True):
	if methods is not None:
		methods = ', '.join(sorted(x.upper() for x in methods))
	if headers is not None and not isinstance(headers, basestring):
		headers = ', '.join(x.upper() for x in headers)
	if not isinstance(origin, basestring):
		origin = ', '.join(origin)
	if isinstance(max_age, timedelta):
		max_age = max_age.total_seconds()

	def get_methods():
		if methods is not None:
			return methods

		options_resp = current_app.make_default_options_response()
		return options_resp.headers['allow']

	def decorator(f):
		def wrapped_function(*args, **kwargs):
			if automatic_options and request.method == 'OPTIONS':
				resp = current_app.make_default_options_response()
			else:
				resp = make_response(f(*args, **kwargs))
			if not attach_to_all and request.method != 'OPTIONS':
				return resp

			h = resp.headers

			h['Access-Control-Allow-Origin'] = origin
			h['Access-Control-Allow-Methods'] = get_methods()
			h['Access-Control-Max-Age'] = str(max_age)
			if headers is not None:
				h['Access-Control-Allow-Headers'] = headers
			return resp

		f.provide_automatic_options = False
		return update_wrapper(wrapped_function, f)
	return decorator

def downloadChunks(url, path):
	"""Helper to download large files
		the only arg is a url
	   this file will go to a temp directory
	   the file will also be downloaded
	   in chunks and print out how much remains
	"""
 
	baseFile = os.path.basename(url)
 
	#move the file to a more uniq path
	os.umask(0002)
	temp_path = path
	try:
		file = os.path.join(temp_path,baseFile)
 
		req = urllib2.urlopen(url)
		total_size = int(req.info().getheader('Content-Length').strip())
		downloaded = 0
		CHUNK = 256 * 10240
		with open(file, 'wb') as fp:
			while True:
				chunk = req.read(CHUNK)
				downloaded += len(chunk)
				print math.floor( (downloaded / total_size) * 100 )
				if not chunk: break
				fp.write(chunk)
	except urllib2.HTTPError, e:
		print "HTTP Error:",e.code , url
		return False
	except urllib2.URLError, e:
		print "URL Error:",e.reason , url
		return False
 
	return file

def download_file(url, path):
	#move the file to a more uniq path
	os.umask(0002)
	temp_path = path
	CHUNK=65536
	#local_filename = url.split('/')[-1]
	local_filename="test.tgz"
	file = os.path.join(temp_path,local_filename)
	# NOTE the stream=True parameter
	#print "url="+url
	#r = requests.get(url, stream=True)
	with open(file, 'wb') as f:
		for chunk in r.iter_content(chunk_size=CHUNK): 
			if chunk: # filter out keep-alive new chunks
				f.write(chunk)
				f.flush()
	return local_filename
