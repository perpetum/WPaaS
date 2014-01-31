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
	This is an utility class to access the ReST API

    :copyright: (c) 2013 by @MIS
"""

import os
import random
import time
import httplib

from oslo.config import cfg

from nova.compute import power_state
from nova.compute import task_states
from nova import exception
from nova.image import glance
from nova.openstack.common.gettextutils import _
from nova.openstack.common import jsonutils
from nova.openstack.common import log
from nova import utils
from nova.virt import driver

LOG = logging.getLogger(__name__)

class WparRIPSession(object):
	"""
	Sets up a session with the Wpar LPAR host and handles all
	the calls made to the host.
	"""

	def __init__(self, host_ip=CONF.wpar.host_ip,
                 username=CONF.wpar.host_username,
                 password=CONF.wpar.host_password,
                 retry_count=CONF.wpar.api_retry_count,
                 scheme=CONF.wpar.host_protocol):
		self._host_ip = host_ip
		self._host_username = username
		self._host_password = password
		self._api_retry_count = retry_count
		self._protocol = protocol
		self.wparhttpclient = None
		self._create_session()

	def _get_wparhttpclient_object(self):
		"""Create the VIM Object instance."""
		return httplib.HTTPConnection(self._host_ip,self.__host_port)

	def _create_session(self):
		"""Creates a session with the Wpar LPAR host."""
		
		delay = 1
		
		while True:
			try:
				# Login and setup the session with the host for making
				# API calls
				if self.wparhttpclient:
					try:
						self.wparhttpclient.close()
					except Exception as excep:
						# This exception is something we can live with.
						LOG.debug(excep)
					self.wparhttpclient = self._get_wparhttpclient_object()
				
				return
			except Exception as excep:
				LOG.critical(_("Unable to connect to server at %(server)s, "
                    "sleeping for %(seconds)s seconds"),
                    {'server': self._host_ip, 'seconds': delay})
				time.sleep(delay)
				delay = min(2 * delay, 60)

	def __del__(self):
		"""Logs-out the session."""
		if hasattr(self, 'wparhttpclient') and self.wparhttpclient:
			self.wparhttpclient.close()

	def _is_wparhttpclient_object(self, module):
		"""Check if the module is a WparHTTPClient Object instance."""
		return isinstance(module, WparHTTPClient)


	def _get_wparhttpclient(self):
		"""Gets the WparHTTPClient object reference."""
		if self.wparhttpclient is None:
			self._create_session()
		return self.wparhttpclient

	def _wait_for_task(self, instance_uuid, task_ref):
		"""
		Return a Deferred that will give the result of the given task.
		The task is polled until it completes.
		"""
		done = event.Event()
		loop = loopingcall.FixedIntervalLoopingCall(self._poll_task,
                                                    instance_uuid,
                                                    task_ref, done)
		loop.start(CONF.wpar.task_poll_interval)
		ret_val = done.wait()
		loop.stop()
		return ret_val

	def _make_request(self, *args, **kwargs):
		headers = {}
		if 'headers' in kwargs and kwargs['headers']:
			headers = kwargs['headers']
		if 'Content-Type' not in headers:
			headers['Content-Type'] = 'application/json'
			kwargs['headers'] = headers
		
		rest = self._session
    	rest.request(*args, **kwargs)
    	return Response(rest.getresponse())
	
	def list_containers(self, _all=True):
        resp = self._make_request('GET','/wparrip/api/wpars/list')
		if resp.code != 200:
			return
		return resp.json

    def create_container(self, args):
		data = {
        	'name':'', 
			'options': { 
			'autostart':'no', 
			'backupdevice':'', 
			'checkpointable':'no', 
			'versioned':'no', 
			'basedir':'', 
			'filesets':'', 
			'force':'no', 
			'vg':'', 
			'hostname':'', 
			'postscript':'', 
			'privateRWfs':'no', 
			'mountdir': { 
				'dir':'', 
				'vfs':'', 
				'dev':'' 
			}, 
			'network': { 
				'interface':'', 
				'ipv4':'', 
				'netmask':'', 
				'broadcast':'', 
				'ipv6':'', 
				'prefixlen':'' 
			},
			'password':'', 
			'dupnameresolution':'no', 
			'rootvg':'no', 
			'start':'no' 
		} 
		
		data.update(args)
        resp = self._make_request('POST','/wparrip/api/wpars/create',body=jsonutils.dumps(data))
		if resp.code != 201:
			return
		# Read the URI where we have to wait  until complete
		location = resp.headers['Location']
		
		# now we have to loop until the wpar is ready...
		# this can take 3 to 30mn depending on the kind of WPAR  ...
		# Fix that!! with a wait_task
		done = False
		while !done:
			resp = self._make_request('GET', location)
			if resp.code != 200:
				return
			if resp.data['state'] == False:
				time.sleep(5)

		# ok, spawn done
		for k, v in obj.iteritems():
			if k.lower() == 'name':
				return v

	def start_container(self, container_id):
		resp= self._make_request('PUT','/wparrip/api/wpars/{0}'.format(container_id), body='{"name":'.container_id.', "state":"start"}')
		return (resp.code == 201)

	def reboot_container(self, container_id):
		resp= self._make_request('PUT','/wparrip/api/wpars/{0}'.format(container_id), body='{"name":'.container_id.', "state":"reboot"}')
		return (resp.code == 201)

    def inspect_container(self, container_name):
		resp = self._make_request('GET','/wparrip/api/wpars/list/{0}'.format(container_id))
		if resp.code != 200:
			return
		return resp.json

    def stop_container(self, container_id):
		resp = self._make_request('PUT','/wparrip/api/wpars/{0}'.format(container_id), body='{"state":"stop"}')
		return (resp.code == 201)

    def destroy_container(self, container_id):
		resp = self._make_request('DELETE','/wparrip/api/wpars/{0}'.format(container_id))
		return (resp.code == 201)

	
