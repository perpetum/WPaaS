"""
    tasks
    ~~~~~
    This file contains all the tasks used by the REST API
    So, all the wpar commands used.
    
    :copyright: (c) 2013 by Matthieu Isoard
"""


import os
import subprocess
import config

from celery import Celery
from celery.result import AsyncResult


celery = Celery('tasks', backend=config.BACKEND_URI, broker=config.BROCKER_URI)

def build_cmd_line(data):
	cmd_opts=[]
	if data['autostart'] == 'yes':
		cmd_opts.append('-A')		
	if 'backupdevice' in data:
		cmd_opts.append('-B')
		cmd_opts.append(data['backupdevice'])
	if 'checkpointable' in data and data['checkpointable'] == 'yes':
		cmd_opts.append('-c')
	if 'versioned' in data and data['versioned'] == 'yes':
		cmd_opts.append('-C')
	if 'basedir' in data:
		cmd_opts.append('-d')
		cmd_opts.append(data['basedir'])
	if 'filesets' in data:
		cmd_opts.append('-e')
		cmd_opts.append(data['filesets'])
	if 'force' in data and data['force'] == 'yes':
		cmd_opts.append('-F')
	if 'vg' in data:
		cmd_opts.append('-g')
		cmd_opts.append(data['vg'])
	if 'hostname' in data:
		cmd_opts.append('-h')
		cmd_opts.append(data['hostname'])
	if 'postscript' in data:
		cmd_opts.append('-k')
		cmd_opts.append(data['postscript'])
	if 'privateRWfs' in data and data['privateRWfs'] == 'yes':
		cmd_opts.append('-l')
	if 'mountdir' in data:
		if 'dir' in data['mountdir']:
			cmd_opts.append('-M')
			cmd_opts.append('directory='+data['mountdir']['dir'])
		if 'vfs' in data['mountdir']:
			cmd_opts.append('vfs='+data['mountdir']['vfs'])	
		if 'dev' in data['mountdir']:
			cmd_opts.append('dev='+data['mountdir']['dev'])	
	if 'network' in data:
		cmd_opts.append('-N')
		if 'netmask' in data['network']:
			cmd_opts.append('netmask='+data['network']['netmask'])
		if 'interface' in data['network']:
			cmd_opts.append('interface='+data['network']['interface'])	
		if 'ipv4' in data['network']:
			cmd_opts.append('address='+data['network']['ipv4'])	
		if 'broadcast' in data['network']:
			cmd_opts.append('broadcast='+data['network']['broadcast'])	
		if 'ipv6' in data['network']:
			cmd_opts.append('address6='+data['network']['ipv6'])	
		if 'prefixlen' in data['network']:
			cmd_opts.append('prefixlen='+data['network']['prefixlen'])	
	if 'password' in data:
		cmd_opts.append('-p')
		cmd_opts.append(data['password'])
	if 'dupnameresolution' in data and data['dupnameresolution'] == 'yes':
		cmd_opts.append('-r')
	if 'rootvg' in data:
		cmd_opts.append('rootvg='+data['rootvg'])
	if 'start' in data and data['start'] == 'yes':
		cmd_opts.append('-s')

	return cmd_opts

@celery.task
def wpar_mkwpar(name, options):
	wpar_cmd = ['/usr/sbin/mkwpar', '-n', name]
	# Let's add more options if needed
	wpar_cmd += options
	# Launch the command
	process = subprocess.Popen(wpar_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	out, err = process.communicate()
	ret = process.wait()
	return ret,out,err

@celery.task
def wpar_check_task(task_id):
	async_res = AsyncResult(task_id)
	return async_res

@celery.task
def wpar_startwpar(name):
	wpar_cmd = ['/usr/sbin/startwpar', name]
	process = subprocess.Popen(wpar_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	out, err = process.communicate()
	ret = process.wait()
	return ret,out,err

@celery.task
def wpar_stopwpar(name):
	wpar_cmd = ['/usr/sbin/stopwpar', name]
	process = subprocess.Popen(wpar_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	out, err = process.communicate()
	ret = process.wait()
	return ret,out,err

@celery.task
def wpar_rebootwpar(name):
	wpar_cmd = ['/usr/sbin/rebootwpar', name]
	process = subprocess.Popen(wpar_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	out, err = process.communicate()
	ret = process.wait()
	return ret,out,err

@celery.task
def wpar_rmwpar(name):
	wpar_cmd = ['/usr/sbin/rmwpar', name]
	process = subprocess.Popen(wpar_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	out, err = process.communicate()
	ret = process.wait()
	return ret,out,err

@celery.task
def wpar_restorewpar(name, file):
	wpar_cmd = ['/usr/sbin/restwpar', '-f', file, name]
	process = subprocess.Popen(wpar_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = process.communicate()
        ret = process.wait()
        return ret,out,err

@celery.task
def wpar_savewpar(name, file):
	wpar_cmd = ['/usr/bin/savewpar', '-f', file, name]
	process = subprocess.Popen(wpar_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = process.communicate()
        ret = process.wait()
        return ret,out,err

@celery.task
def wpar_migwpar(name, file):
	wpar_cmd = ['/usr/sbin/migwpar', '-d', file, '-C', name]
	process = subprocess.Popen(wpar_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = process.communicate()
        ret = process.wait()
        return ret,out,err

@celery.task
def wpar_syncwpar(name):
	wpar_cmd = ['/usr/sbin/syncwpar', name]
	process = subprocess.Popen(wpar_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = process.communicate()
        ret = process.wait()
        return ret,out,err

@celery.task
def wpar_listwpar():
        wpar_list_cmd = ['/usr/sbin/lswpar','-c']     
        proc = subprocess.Popen(wpar_list_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return proc.communicate()[0]

@celery.task
def wpar_listdetailswpar(wpar_name):
        wpar_list_cmd = ['/usr/sbin/lswpar','-L', wpar_name]     
        proc = subprocess.Popen(wpar_list_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return proc.communicate()[0]
