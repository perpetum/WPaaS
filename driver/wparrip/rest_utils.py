# vim: tabstop=4 shiftwidth=4 softtabstop=4

#
#	Licensed under the Apache License, Version 2.0 (the "License"); you may
#	not use this file except in compliance with the License. You may obtain
#	a copy of the License at
#
#		 http://www.apache.org/licenses/LICENSE-2.0
#
#	Unless required by applicable law or agreed to in writing, software
#	distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#	WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#	License for the specific language governing permissions and limitations
#	under the License.

"""
	Class for REST APIs.

	:copyright: (c) 2013 by @MIS
"""
import functools

from eventlet.green import httplib
import six

from nova.openstack.common import jsonutils
from nova.openstack.common import log as logging

LOG = logging.getLogger(__name__)
	
def filter_data(f):
	"""Decorator that post-processes data returned by Wpar to avoid any
	   surprises with different versions of Wpar
	"""
	@functools.wraps(f)
	def wrapper(*args, **kwds):
		out = f(*args, **kwds)

		def _filter(obj):
			if isinstance(obj, list):
				new_list = []
				for o in obj:
					new_list.append(_filter(o))
				obj = new_list
			if isinstance(obj, dict):
				for k, v in obj.items():
					if isinstance(k, basestring):
						obj[k.lower()] = _filter(v)
			return obj
		return _filter(out)
	return wrapper

class Response(object):
	"""
	Create a Response object to make dev life easier
	"""
	def __init__(self, http_response, skip_body=False):
		self._response = http_response
		self.code = int(http_response.status)
		self.data = http_response.read()
		self.json = self._decode_json(self.data)

	def read(self, size=None):
		return self._response.read(size)
		
	@filter_data
	def _decode_json(self, data):
		if self._response.getheader('Content-Type') != 'application/json':
			return
		try:
			return jsonutils.loads(self.data)
		except ValueError:
			return

	
