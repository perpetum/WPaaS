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
    tasks
    ~~~~~
    This file contains all the tasks used by the REST API
    So, all the wpar commands used.
    
    :copyright: (c) 2013 by @MIS
"""


import os
import subprocess
import config
import tarfile

from celery import Celery
from celery.result import AsyncResult


celery = Celery('tasks', backend=config.BACKEND_URI, broker=config.BROCKER_URI)

def build_cmd_line(data):
	cmd_opts=[]

	if 'password' in data and data['password'] != "":
		cmd_opts.append('-P')
		cmd_opts.append(data['password'])
	if 'start' in data and data['start'] == "yes":
		cmd_opts.append('-s')
	if 'network' in data:
		if 'address' in data['network'] and data['network']['address'] != "":
			if not '-N' in cmd_opts:
				cmd_opts.append('-N')
			cmd_opts.append('address='+data['network']['address'])
		if 'netmask' in data['network'] and data['network']['netmask'] != "":
			if not '-N' in cmd_opts:
				cmd_opts.append('-N')
			cmd_opts.append('netmask='+data['network']['netmask'])
		if 'interface' in data['network'] and data['network']['interface'] != "":
			if not '-N' in cmd_opts:
				cmd_opts.append('-N')
			cmd_opts.append('interface='+data['network']['interface'])	
		if 'ipv4' in data['network'] and data['network']['ipv4'] != "":
			if not '-N' in cmd_opts:
				cmd_opts.append('-N')
			cmd_opts.append('address='+data['network']['ipv4'])	
		if 'broadcast' in data['network'] and data['network']['broadcast'] != "":
			if not '-N' in cmd_opts:
				cmd_opts.append('-N')
			cmd_opts.append('broadcast='+data['network']['broadcast'])	
		if 'ipv6' in data['network'] and data['network']['ipv6'] != "":
			if not '-N' in cmd_opts:
				cmd_opts.append('-N')
			cmd_opts.append('address6='+data['network']['ipv6'])	
		if 'prefixlen' in data['network'] and data['network']['prefixlen'] != "":
			if not '-N' in cmd_opts:
				cmd_opts.append('-N')
			cmd_opts.append('prefixlen='+data['network']['prefixlen'])
	if 'hostname' in data:
		if data['hostname'] != "":
			cmd_opts.append('-h')
			cmd_opts.append(data['hostname'])
	if 'autostart' in data and data['autostart'] == "yes":
		cmd_opts.append('-A')		
	if 'backupdevice' in data:
		if data['backupdevice'] != "":
			cmd_opts.append('-B')
			cmd_opts.append(data['backupdevice'])
	if 'checkpointable' in data and data['checkpointable'] == "yes":
		cmd_opts.append('-c')
	if 'versioned' in data and data['versioned'] == "yes":
		cmd_opts.append('-C')
	if 'basedir' in data:
		if data['basedir'] != "":
			cmd_opts.append('-d')
			cmd_opts.append(data['basedir'])
	if 'filesets' in data:
		if data['filesets'] != "":
			cmd_opts.append('-e')
			cmd_opts.append(data['filesets'])
	if 'force' in data and data['force'] == "yes":
		cmd_opts.append('-F')
	if 'vg' in data:
		if data['vg'] != "":
			cmd_opts.append('-g')
			cmd_opts.append(data['vg'])	
	if 'postscript' in data:
		if data['postscript'] != "":
			cmd_opts.append('-k')
			cmd_opts.append(data['postscript'])
	if 'privateRWfs' in data and data['privateRWfs'] == "yes":
		cmd_opts.append('-l')
	if 'mountdir' in data:
		if 'dir' in data['mountdir'] and data['mountdir']['dir'] != "":
			cmd_opts.append('-M')
			cmd_opts.append('directory='+data['mountdir']['dir'])
		if 'vfs' in data['mountdir'] and data['mountdir']['vfs'] != "":
			cmd_opts.append('vfs='+data['mountdir']['vfs'])	
		if 'dev' in data['mountdir'] and data['mountdir']['dev'] != "":
			cmd_opts.append('dev='+data['mountdir']['dev'])	
	if 'dupnameresolution' in data and data['dupnameresolution'] == "yes":
		cmd_opts.append('-r')
	if 'devname' in data and data['devname'] != "":
		if '-D' not in cmd_opts:
			cmd_opts.append('-D')
		cmd_opts.append('devname='+data['devname'])
	if 'rootvg' in data and data['rootvg'] != "no":
		if '-D' not in cmd_opts:
			cmd_opts.append('-D')
		cmd_opts.append('rootvg='+data['rootvg'])
	
	return cmd_opts

def _run_cmd(cmd, wait=True):
	
	process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	out, err = process.communicate()
	if err is None or err is "":
		ret = 0
	if wait:
		ret = process.wait()
	return ret,out,err

@celery.task
def wpar_mkwpar(name, options):
	wpar_cmd = ['/usr/sbin/mkwpar', '-n', name]
	# Let's add more options if needed
	wpar_cmd += options
	# Launch the command
	ret,out,err = _run_cmd(wpar_cmd)
	return ret,out,err

@celery.task
def wpar_check_task(task_id):
	async_res = AsyncResult(task_id)
	return async_res

@celery.task
def wpar_startwpar(name):
	wpar_cmd = ['/usr/sbin/startwpar', name]
	ret,out,err = _run_cmd(wpar_cmd)
	return ret,out,err

@celery.task
def wpar_stopwpar(name):
	wpar_cmd = ['/usr/sbin/stopwpar', name]
	ret,out,err = _run_cmd(wpar_cmd)
	return ret,out,err

@celery.task
def wpar_rebootwpar(name):
	wpar_cmd = ['/usr/sbin/rebootwpar', name]
	ret,out,err = _run_cmd(wpar_cmd)
	return ret,out,err

@celery.task
def wpar_rmwpar(name):
	# Add the -F flag to stop it whatever its state
	wpar_cmd = ['/usr/sbin/rmwpar', '-F', name]
	ret,out,err = _run_cmd(wpar_cmd)
	return ret,out,err

@celery.task
def wpar_restorewpar(name, file):
	wpar_cmd = ['/usr/sbin/restwpar', '-f', file, name]
	ret,out,err = _run_cmd(wpar_cmd)
	return ret,out,err

@celery.task
def wpar_savewpar(name, file):
	wpar_cmd = ['/usr/bin/savewpar', '-f', file, name]
	ret,out,err = _run_cmd(wpar_cmd)
	return ret,out,err

@celery.task
def wpar_migwpar(name, file):
	wpar_cmd = ['/usr/sbin/migwpar', '-d', file, '-C', name]
	ret,out,err = _run_cmd(wpar_cmd)
	return ret,out,err

@celery.task
def wpar_syncwpar(name):
	wpar_cmd = ['/usr/sbin/syncwpar', name]
	ret,out,err = _run_cmd(wpar_cmd)
	return ret,out,err

@celery.task
def wpar_listwpar():
	wpar_list_cmd = ['/usr/sbin/lswpar','-c']     
	ret,out,err = _run_cmd(wpar_list_cmd)
	return out

@celery.task
def wpar_listdetailswpar(wpar_name):
	wpar_list_cmd = ['/usr/sbin/lswpar','-L', wpar_name]     
	ret,out,err = _run_cmd(wpar_list_cmd)
	return out

@celery.task
def host_stats():
	stat_cmd = ['/usr/bin/lparstat','-i']     
	ret,out,err = _run_cmd(stat_cmd)
	return out

@celery.task
def host_cpustats():
	proc_cmd = ['/usr/bin/pmlist','-s']
	ret,out,err = _run_cmd(proc_cmd)
	return out

@celery.task
def host_status():
	status_cmd = ['/home/misoard/wparrip.sh']     
	ret,out,err = _run_cmd(status_cmd)
	return out

@celery.task
def host_shutdown():
	shutdown_cmd = ['/etc/shutdown']     
	ret,out,err = _run_cmd(shutdown_cmd)
	return out

@celery.task
def host_reboot():
	reboot_cmd = ['/etc/reboot','now']     
	ret,out,err = _run_cmd(reboot_cmd)
	return out

@celery.task
def host_os_stats():
	os_cmd = ['/usr/bin/oslevel']     
	ret,out,err = _run_cmd(os_cmd)
	return out

@celery.task
def host_network_devices():
	net_cmd = ['/etc/lsdev','-Cc','if']     
	ret,out,err = _run_cmd(net_cmd)
	return out

@celery.task
def image_inspect(image_fullpath):
	ls_cmd = ['/usr/bin/lsmksysb','-lf',image_fullpath]
	ret,out,err = _run_cmd(ls_cmd)
	return ret,out,err

@celery.task
def image_create(path, data):
	files = []
	# First create the <image_local>/<image_name>.info file. It acts as the image repository locally
	# to know which images are used by the WPARs (do not want it to be in a DB since it could be used
	# without this program.)
	info_file = path+'/'+data['name']+'.info'
	with open(info_file, 'w') as outfile:
  		json.dump(data, outfile)
	
	# Now, depending on the image, we build a .tgz file containing either:
	#	- The .info file only
	#	- The .info file and the mksysb
	# 	- The .info file and whatever NFS tree or program
	files.append(data['name']+'.info')
	if data['type'] == 'mksysb':
		files.append(data['name'])
	
	_targzip_content(files)
	return 0,data['id'],""

def _targzip_content(path, files):
	full=path+'/'+data['name']+'.tgz'
	tar = tarfile.open(full, "w:gz")
	for name in files:
		tar.add(path+'/'+name)
	tar.close()
	return full
