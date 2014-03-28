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
Some functions to manage image files
"""

import os

from nova import exception
from nova.image import glance

from nova.openstack.common import log as logging


LOG = logging.getLogger(__name__)

class WparImage(object):

	def __init__(self, image_meta=None):
	
		self.image_name = self._get_image_name(image_meta)
		self.image_type = None
			

	def _get_image_name(self, image=None):
		if image != None:
			fmt = image['container_format']
			if fmt != 'wparrip':
				msg = _('Image container format not supported ({0})')
				raise exception.ImageUnacceptable(msg.format(fmt),image_id=image['id'])
		
			return image['name']
		return None
	
	def get_image_info(self, context, image_href):
		if not image_href:
			return None, {}
		(image_service, image_id) = glance.get_remote_image_service(context,image_href)
		image = image_service.show(context, image_id)
		return image_id, image
	
	def get_image_iter(self, context, image_href):
		if not image_href:
			return None
		(image_service, image_id) = glance.get_remote_image_service(context,image_href)
		readiter = image_service.download(context, image_id)
		return readiter
	
	def get_image_size(self, context, image_href):
		image_id, metadata = self.get_image_info(context, image_href)
		file_size = int(metadata['size'])
		
		return file_size
