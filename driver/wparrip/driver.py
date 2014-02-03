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
	A WPAR ReST Hypervisor which allows running WPAR Containers in nova.

	:copyright: (c) 2013 by @MIS
"""

import os
import random
import time
import httplib
import string

from oslo.config import cfg

from nova.compute import power_state
from nova.compute import task_states
from nova import exception
from nova.image import glance
from nova.openstack.common.gettextutils import _
from nova.openstack.common import jsonutils
from nova.openstack.common import log as logging
from nova import utils
from nova.virt import driver
from nova.virt.wparrip import client
from nova.virt.wparrip import host
from nova.virt.wparrip import rest_utils

LOG = logging.getLogger(__name__)

wparrip_opts = [
	cfg.StrOpt('host_ip',
			    help='URL for connection to WPAR ReST LPAR host.'),
	cfg.IntOpt('host_port',
				default=5000,
				help='URL port for connection to WPAR ReST LPAR host.'),
	cfg.StrOpt('host_username',
				help='Username for connection to WPAR ReST LPAR host.'),
	cfg.StrOpt('host_password',
				help='Password for connection to WPAR ReST LPAR host.',
				secret=True),
	cfg.StrOpt('host_protocol',
				default="http",
				help='Protocol for connection to WPAR ReST LPAR host.'),
	cfg.FloatOpt('task_poll_interval',
				default=5.0,
				help='The interval used for polling of remote tasks.'),
	cfg.IntOpt('api_retry_count',
				default=10,
				help='The number of times we retry on failures, e.g., '
				'socket error, etc.')
	]

CONF = cfg.CONF
CONF.register_opts(wparrip_opts, 'wparrip')

TIME_BETWEEN_API_CALL_RETRIES = 2.0


class Failure(Exception):
	"""Base Exception class for handling task failures."""

	def __init__(self, details):
		self.details = details

	def __str__(self):
		return str(self.details)


class WparDriver(driver.ComputeDriver):
	"""Wpar ReST hypervisor driver."""

	def __init__(self, virtapi, read_only=False):
		super(WparDriver, self).__init__(virtapi)
		self._wpar = None
	
		LOG.debug(_("wparrip, let's GO!"))
		# Get the list of LPARs to be used
		self._host_ip = CONF.wparrip.host_ip
		LOG.debug(_("wparrip, CONF OK= %s") % self._host_ip)
		if not (self._host_ip or CONF.wparrip.host_username is None or CONF.wparrip.host_password is None):
			raise Exception(_("Must specify host_ip, "
							  "host_username "
							  "and host_password to use "
							  "compute_driver=wparrip.WparDriver"))

		self._session = client.WparRIPSession()
		LOG.debug(_("wparrip, Session OK"))
		self._host = host.Host(self._session)
		LOG.debug(_("wparrip, Host OK"))
		self._host_state = None

	# FIXME(strus38): review and implement missing parts	
	@property
	def host_state(self):
		# FIXME(strus38): implement this
		if not self._host_state:
			self._host_state = host.HostState(self._session, self._host_ip)
		return self._host_state

	def init_host(self, host):
		"""Do the initialization that needs to be done."""
		# FIXME(strus38): implement this ... if needed, not yet!
		pass

	#IMPLEMENTED
	def list_instances(self, inspect=False):
		"""Return the names of all the instances known to the virtualization layer, as a list."""
		vms = self._session.list_containers()
		LOG.debug(_("list_instances %s") % vms)
		lst_vm_names = []
		if vms:
			for wpar in vms['wpars']:
				vm_name = wpar['name']
				lst_vm_names.append(vm_name)
				LOG.debug(_("Wparrip instance %s") % vm_name)
		else:
			LOG.debug(_("WparRIP Error: No WPARs found"))
		
		LOG.debug(_("Got total of %s instances") % str(len(lst_vm_names)))
		return lst_vm_names

	#IMPLEMENTED
	def plug_vifs(self, instance, network_info):
		"""Plug VIFs into networks."""
		pass

	#IMPLEMENTED
	def unplug_vifs(self, instance, network_info):
		"""Unplug VIFs from networks."""
		pass

	#IMPLEMENTED	
	def find_container_by_name(self, name):
		for info in self.list_instances(inspect=True):
			if info == name:
				return info
		return {}

	#IMPLEMENTED
	def get_info(self, instance):
		"""
		Get the current status of an instance, by name (not ID!)
		State :	the running state, one of the power_state codes
		Max_mem :	(int) the maximum memory in KBytes allowed
		Mem :	(int) the memory in KBytes used by the domain
		Num_cpu :	(int) the number of virtual CPUs for the domain
		Cpu_time :	(int) the CPU time used in nanoseconds
		"""
		LOG.debug(_("Wparrip get_info %s") % instance['name'])
		info = {
			'max_mem': 0,
			'mem': 0,
			'num_cpu': 1,
			'cpu_time': 0
		}
		conn_state = power_state.SHUTDOWN
		
		wpar = self._session.inspect_container(instance['name'])
		if wpar:
			if wpar['rescontrols']['MemoryLimits'] is not "":
				info['max_mem'].update(string.atoi(wpar['rescontrols']['MemoryLimits'],10))
			if wpar['rescontrols']['CPULimits'] is not "":
				info["num_cpu"].update(string.atoi(wpar['rescontrols']['CPULimits'],10))
				#FIXME to find the right piece of info
				
			if wpar['state'] is "Defined":
				conn_state = power_state.SUSPENDED
			elif wpar['state'] is "Stopped":
				conn_state = power_state.SHUTDOWN
			elif wpar['state'] is "Active":
				conn_state = power_state.RUNNING
			
		info['state'] = conn_state
		return info
	
	#IMPLEMENTED
	def _get_available_resources(self, host_stats):
		return {'vcpus': host_stats['vcpus'],
			   'memory_mb': host_stats['host_memory_total'],
			   'local_gb': host_stats['disk_total'],
			   'vcpus_used': 0,
			   'memory_mb_used': host_stats['host_memory_total'] -
								 host_stats['host_memory_free'],
			   'local_gb_used': host_stats['disk_used'],
			   'hypervisor_type': host_stats['hypervisor_type'],
			   'hypervisor_version': host_stats['hypervisor_version'],
			   'hypervisor_hostname': host_stats['hypervisor_hostname'],
			   'cpu_info': jsonutils.dumps(host_stats['cpu_info']),
			   'supported_instances': jsonutils.dumps(
				   host_stats['supported_instances']),
			   }

	#IMPLEMENTED
	def get_host_stats(self, refresh=False):
		"""
		Return the current state of the host.
		If 'refresh' is True, run the update first.
		"""
		return self.host_state.get_host_stats(refresh=refresh)
	
	#IMPLEMENTED
	def get_available_resource(self, nodename):
		"""Retrieve resource information.

		This method is called when nova-compute launches, and
		as part of a periodic task that records the results in the DB.

		:returns: dictionary describing resources

		"""
		host_stats = self.get_host_stats(refresh=True)

		# Updating host information
		return self._get_available_resources(host_stats)

	#IMPLEMENTED
	def spawn(self, context, instance, image_meta, injected_files,
			  admin_password, network_info=None, block_device_info=None):
		"""Create VM instance."""
		
		args = {
			'name': instance['name'],
			'password': admin_password,
			'start': 'yes'
		}
		container_id = self._session.create_container(args)
		if not container_name:
			raise exception.InstanceDeployFailure(
					_('Cannot deploy WPAR'),
					instance_id=instance['name'])

	#NOT IMPLEMENTED
	def snapshot(self, context, instance, name, update_task_state):
		"""Create snapshot from a running VM instance."""
		pass

	#IMPLEMENTED
	def reboot(self, context, instance, network_info, reboot_type,
			   block_device_info=None, bad_volumes_callback=None):
		"""Reboot VM instance."""
		self._session.reboot_container(instance["name"])

	#IMPLEMENTED
	def destroy(self, context, instance, network_info, block_device_info=None,
				destroy_disks=True):
		"""Destroy VM instance."""
		self._session.destroy_container(instance["name"])

	#NOT IMPLEMENTED
	def pause(self, instance):
		"""Pause VM instance."""
		# FIXME(strus38): implement this
		pass

	#NOT IMPLEMENTED
	def unpause(self, instance):
		"""Unpause paused VM instance."""
		# FIXME(strus38): implement this
		pass
	
	#IMPLEMENTED
	def power_off(self, instance):
		"""Power off the specified instance."""
		self._session.stop_container(instance["name"])
	
	#IMPLEMENTED
	def power_on(self, context, instance, network_info,
				 block_device_info=None):
		"""Power on the specified instance."""
		self._session.start_container(instance["name"])

	#NOT IMPLEMENTED
	def get_console_output(self, instance):
		pass
	
