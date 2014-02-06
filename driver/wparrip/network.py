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
	Class to decode Neutron network infos.

	:copyright: (c) 2013 by @MIS
"""
import socket,struct

from nova.openstack.common import log as logging
from nova.openstack.common import jsonutils

LOG = logging.getLogger(__name__)

class WparNetwork(object):
	"""
		This class takes the Neutron network info and
		convert them into usefull information for the wparrip driver
		FIXME: will have to handle other Network projects
	"""
	def __init__(self, network_info=None):
		if network_info is None:
			self.network_info = None
		else:
			self.network_info = self._get_network_for_wpar(network_info)
		
	def _find_fixed_ip(self, subnets):
		for subnet in subnets:
			for ip in subnet['ips']:
				if ip['type'] == 'fixed' and ip['address']:
					return ip['address']

	def _find_dns_ip(self, subnets):
		for subnet in subnets:
			for dns in subnet['dns']:
				if dns['type'] == 'dns' and dns['address']:
					return dns['address']
	
	def _find_gateway_ip(self, subnets):
		for subnet in subnets:
			if subnet['gateway']['type'] == 'gateway' and subnet['gateway']['address']:
					return subnet['gateway']['address']
	
	def _find_cidr(self, subnets):
		for subnet in subnets:
			if 'cidr' in subnet:
					#only get the mask
					return subnet['cidr'][-2:]
	
	def _get_network_for_wpar(self, network_info):
		data = {}
		data['ip'] = self._find_fixed_ip(network_info['subnets'])
		data['dns'] = self._find_dns_ip(network_info['subnets'])
		data['gateway'] = self._find_gateway_ip(network_info['subnets'])
		mask = int(self._find_cidr(network_info['subnets']))
		data['netmask'] = self._calcDottedNetmask(mask)
		return data
	
	def _calcDottedNetmask(self, mask):
		bits = 0
		for i in xrange(32-mask,32):
			bits |= (1 << i)
		return socket.inet_ntoa(struct.pack('>I', bits))
