# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
#	Code inspired from Docker and modified to fit our needs
#
#	Licensed under the Apache License, Version 2.0 (the "License"); you may
#	not use this file except in compliance with the License. You may obtain
#	a copy of the License at
#
#		http://www.apache.org/licenses/LICENSE-2.0
#
#	Unless required by applicable law or agreed to in writing, software
#	distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#	WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#	License for the specific language governing permissions and limitations
#	under the License.

import os

import flask
import glanceclient
from keystoneclient.v2_0 import client as keystoneclient

class GlanceStorage(object):

	"""
	This class stores the image layers into OpenStack Glance.
	"""

	disk_format = 'raw'
	container_format = 'wparrip'

	def __init__(self, config):
		self._config = config

	def _get_auth_token(self):
		args = {}
		for arg in ['username', 'password', 'tenant_name', 'auth_url']:
			env_name = 'OS_{0}'.format(arg.upper())
			if env_name not in os.environ:
				raise ValueError('Cannot find env var "{0}"'.format(env_name))
			args[arg] = os.environ[env_name]
		keystone = keystoneclient.Client(**args)
		return keystone.auth_token

	def _get_endpoint(self):
		if 'OS_GLANCE_URL' not in os.environ:
			raise ValueError('Cannot find env var "OS_GLANCE_URL"')
		return os.environ['OS_GLANCE_URL']

	def _create_glance_client(self):
		token = flask.request.headers.get('X-Meta-Auth-Token')
		endpoint = flask.request.headers.get('X-Meta-Glance-Endpoint')
		if not token:
			token = self._get_auth_token()
		if not endpoint:
			endpoint = self._get_endpoint()
		return glanceclient.Client('1', endpoint=endpoint, token=token)
	
	def _read_image_info_file(image_name):
		try:
			f = open(image_local+'/'+image_name, "r")
		except IOError:
			return None
		else:
			with f:
				obj = json.loads(f.read())
		return obj

	def _init_path(self, path, create=True):
		"""This resolve a standard Wparrip <image>.info file
		   and returns: glance_image obj, property_name
		   !The image_id should be in sync with what Glance has!
		   If property name is None, we want to reach the image_data
		"""
		localpath, filename = os.path.split(path)
		obj_res = _read_image_info_file(path)
		if not 'id' in obj_res:
			raise ValueError('Invalid image info file: {0}'.format(path))
		
		image_id = obj_res['id']
		glance = self._create_glance_client()
		image = self._find_image_by_id(glance, image_id)
		if not image and create is True:
			if 'X-Meta-Glance-Image-Id' in flask.request.headers:
				try:
					i = glance.images.get(
						flask.request.headers['X-Meta-Glance-Image-Id'])
					if i.status == 'queued':
						# We allow taking existing images only when queued
						image = i
						image.update(properties={'id': image_id},
									 purge_props=False)
				except Exception:
					pass
			if not image:
				image = glance.images.create(
					disk_format=self.disk_format,
					container_format=self.container_format,
					properties={'id': image_id})
			try:
				image.update(is_public=True, purge_props=False)
			except Exception:
				pass
		propname = 'meta_{0}'.format(filename)
		if filename == 'layer':
			propname = None
		return image, propname

	def _find_image_by_id(self, glance, image_id):
		filters = {
			'disk_format': self.disk_format,
			'container_format': self.container_format,
			'properties': {'id': image_id}
		}
		images = [i for i in glance.images.list(filters=filters)]
		if images:
			return images[0]

	def _clear_images_name(self, glance, image_name):
		images = glance.images.list(filters={'name': image_name})
		for image in images:
			image.update(name=None, purge_props=False)

	def get_content(self, path):
		(image, propname) = self._init_path(path, False)
		if not propname:
			raise ValueError('Wrong call (should be stream_read)')
		if not image or propname not in image.properties:
			raise IOError('No such image {0}'.format(path))
		return image.properties[propname]

	def put_content(self, path, content):
		(image, propname) = self._init_path(path)
		if not propname:
			raise ValueError('Wrong call (should be stream_write)')
		props = {propname: content}
		image.update(properties=props, purge_props=False)

	def stream_read(self, path):
		(image, propname) = self._init_path(path, False)
		if propname:
			raise ValueError('Wrong call (should be get_content)')
		if not image:
			raise IOError('No such image {0}'.format(path))
		return image.data(do_checksum=False)

	def stream_write(self, path, fp):
		(image, propname) = self._init_path(path)
		if propname:
			raise ValueError('Wrong call (should be put_content)')
		image.update(data=fp, purge_props=False)

	def exists(self, path):
		(image, propname) = self._init_path(path, False)
		if not image:
			return False
		if not propname:
			return True
		return (propname in image.properties)

	def remove(self, path):
		(image, propname) = self._init_path(path, False)
		if not image:
			return
		if propname:
			# Delete only the image property
			props = image.properties
			if propname in props:
				del props[propname]
				image.update(properties=props)
			return
		image.delete()

	def get_size(self, path):
		(image, propname) = self._init_path(path, False)
		if not image:
			raise OSError('No such image: \'{0}\''.format(path))
		return image.size
