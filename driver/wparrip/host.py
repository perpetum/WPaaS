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
	Management class for host-related functions (start, reboot, etc).

	:copyright: (c) 2013 by @MIS
"""

from nova import exception
from nova.openstack.common.gettextutils import _
from nova.openstack.common import log as logging
from nova import unit
from nova import utils

LOG = logging.getLogger(__name__)


class Host(object):
	"""
	Implements host related operations.
	"""
	def __init__(self, session):
		self._session = session

	def host_power_action(self, host, action):
		"""Reboots or shuts down the host."""
		host_mor = vm_util.get_host_ref(self._session)
		LOG.debug(_("%(action)s %(host)s"), {'action': action, 'host': host})
		if action == "reboot":
			host_task = self._session.reboot_host()
		elif action == "shutdown":
			host_task = self._session.shutdown_host()
		elif action == "startup":
			# FIX ME
			host_task = self._session.reboot_host()
		self._session._wait_for_task(host, host_task)

	def host_maintenance_mode(self, host, mode):
		"""Start/Stop host maintenance window. On start, it triggers
		guest VMs evacuation.
		"""
		host_mor = vm_util.get_host_ref(self._session)
		LOG.debug(_("Set maintenance mod on %(host)s to %(mode)s"),
				  {'host': host, 'mode': mode})
		#FIX ME
		pass
		
	def set_host_enabled(self, _host, enabled):
		"""Sets the specified host's ability to accept new instances."""
		pass


class HostState(object):
	"""Manages information about the LPAR host this wparrip
	node is running on.
	"""
	def __init__(self, session, host_name):
		super(HostState, self).__init__()
		self._session = session
		self._host_name = host_name
		self._stats = {}
		self.update_status()

	def get_host_stats(self, refresh=False):
		"""Return the current state of the host. If 'refresh' is
		True, run the update first.
		"""
		if refresh or not self._stats:
			self.update_status()
		return self._stats

	def update_status(self):
		"""Update the current state of the host.
		"""
		host_mor = vm_util.get_host_ref(self._session)
		summary = self._session._make_request('GET','/wparrip/api/host')
		if resp.code != 200:
			return

		if summary is None:
			return
		
		#FIX ME ... WPARs and disk are not best friends... it all depends on
		# how you create the WPARs...
		# What should be done for openstack is maybe have a dedicated VG that supports
		# all the WPARs we want to create... it could be an easy fix at least at the beginning
		# so for now, let's assume there are always free storage for more WPARs...
		# try:
		#	 ds = vm_util.get_datastore_ref_and_name(self._session)
		# except exception.DatastoreNotFound:
		#	 ds = (None, None, 0, 0)

		data = {}
		data["vcpus"] = summary.host.Online_Virtual_CPUs
		data["cpu_info"] = \
				{"vendor": "IBM",
				 "model": summary.host.cpu.cpuModel,
				 "topology": {"cores": 4,
							  "sockets": 2,
							  "threads": 4}
				}
		data["disk_total"] = 20000
		data["disk_available"] = 10000
		data["disk_used"] = data["disk_total"] - data["disk_available"]
		data["host_memory_total"] = summary.host.stats.Online_Memory / unit.Mi
		#On AIX, the LPAR consumes all the memory, it does not mean
		# that we cannot allocate a wpar
		data["host_memory_free"] = summary.host.stats.Online_Memory / unit.Mi
		data["hypervisor_type"] = 'wparrip'
		data["hypervisor_version"] = '1.0'
		data["hypervisor_hostname"] = self._host_name
		data["supported_instances"] = [('POWER', 'wparrip', 'wpar')]

		self._stats = data
		return data
		
