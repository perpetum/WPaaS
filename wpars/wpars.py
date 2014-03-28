#!../flask/bin/python
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
    This file is contains the  REST API
    
    :copyright: (c) 2013 by @MIS
"""
import logging
import os
import subprocess
import sys
import re
import config
import string
import time
import uuid

from flask import Flask, jsonify, request, make_response, session, abort, Response
from tasks import host_os_stats, image_create, image_inspect, host_network_devices, host_cpustats, host_status, host_stats, wpar_listwpar, wpar_listdetailswpar, build_cmd_line, wpar_mkwpar, wpar_check_task, wpar_rebootwpar, wpar_rmwpar, wpar_startwpar, wpar_stopwpar, wpar_restorewpar, wpar_savewpar, wpar_migwpar, wpar_syncwpar
from utils import requires_auth, crossdomain, downloadChunks, download_file

app = Flask(__name__)

numeric_level = logging.DEBUG
if not isinstance(numeric_level, int):
    raise ValueError('Invalid log level: %s' % loglevel)
logging.basicConfig(filename=config.LOGFILE, filemode='w', level=numeric_level, format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')

wpars = [ ]

#Initialyze image repositories
image_local = "/wparrip_images"
image_remote = "glance"
if config.IMAGE_REPOSITORY_LOCAL:
	image_local = config.IMAGE_REPOSITORY_LOCAL
	if not os.path.exists(image_local):
		os.makedirs(image_local)
if config.IMAGE_REPOSITORY_REMOTE:
	image_remote = config.IMAGE_REPOSITORY_REMOTE
	if image_remote == "glance":
		import glance
	

"""
Function: _parsewpar_output
Note: Compatible with AIX 6.1 and AIX 7.1
:param: result is the stdout of lswpar -L
:param: output: json format
"""
def _parsewpar_output(result):
	data_list = result.splitlines()
	
	data_out = {}
	main_key = ""
	header_len=0
	general=False
	network=False
	routes=False
	fs=False
	rescontrols=False
	security=False
	operation=False
	devexport=False
	reg_general=re.compile('^GENERAL$')
	reg_network=re.compile('^NETWORK$')
	reg_routes=re.compile('^USER-SPECIFIED ROUTES$')
	reg_fs=re.compile('^FILE SYSTEMS$')
	reg_rescontrols=re.compile('^RESOURCE CONTROLS$')
	reg_security=re.compile('^SECURITY SETTINGS$')
	reg_operation=re.compile('^OPERATION$')
	reg_devexport=re.compile('^DEVICE EXPORTS$')
	reg_kernext=re.compile('^KERNEL EXTENSIONS$')
	# Extract 2nd line where Name and State are displayed
	
	tmp=data_list[1].split('-')
	logging.debug('In _parsewpar_output: tmp=%s', tmp)
	
	data_out.setdefault('name', tmp[0].rstrip())
	data_out.setdefault('state', tmp[1].lstrip())
	for entry in data_list:
		if entry.startswith('----') or entry == '':
			continue
		if reg_general.match(entry):
			general=False
			network=False
			routes=False
			fs=False
			rescontrols=False
			security=False
			operation=False
			devexport=False
			general=True
			main_key='general'
			continue
		if reg_network.match(entry):
			general=False
			network=False
			routes=False
			fs=False
			rescontrols=False
			security=False
			operation=False
			devexport=False
			network=True
			header_found = False
			main_key='network'
			continue
		if reg_routes.match(entry):
			general=False
			network=False
			routes=False
			fs=False
			rescontrols=False
			security=False
			operation=False
			devexport=False
			routes=True
			header_found = False
			main_key='routes'
			continue
		if reg_fs.match(entry):
			general=False
			network=False
			routes=False
			fs=False
			rescontrols=False
			security=False
			operation=False
			devexport=False
			fs=True
			header_found = False
			main_key='fs'
			continue
		if reg_rescontrols.match(entry):
			general=False
			network=False
			routes=False
			fs=False
			rescontrols=False
			security=False
			operation=False
			devexport=False
			rescontrols=True
			main_key='rescontrols'
			continue
		if reg_security.match(entry):
			general=False
			network=False
			routes=False
			fs=False
			rescontrols=False
			security=False
			operation=False
			devexport=False
			security=True
			main_key='security'
			continue
		if reg_operation.match(entry):
			general=False
			network=False
			routes=False
			fs=False
			rescontrols=False
			security=False
			operation=False
			devexport=False
			operation=True
			main_key='operation'
			continue
		if reg_devexport.match(entry):
			general=False
			network=False
			routes=False
			fs=False
			rescontrols=False
			security=False
			operation=False
			devexport=False
			devexport=True
			header_found = False
			main_key='devexport'
			continue
		if reg_kernext.match(entry):
			break
			
		if general == True or rescontrols == True or operation == True or security == True:
			entry = re.sub( '\s+', '', entry )
			#Special case for multi-line values
			if (entry.endswith(',') or "PV_" in entry) and not ":" in entry:
				value=entry
				data_out[main_key][key] += value
			else:
				items = entry.split(':')
        			key, value = items[0], items[1]		
				if value == None:
					value=""
				tmp = data_out.setdefault(main_key, dict())
				tmp.setdefault(key,value)
			continue

	return data_out

"""
_parse_hostinfo_output
This function takes a lparstat -i output and
build a json answer for it.
"""
def _parse_hostinfo_output(result):
	data_out = {}
	data_list = result.splitlines()
	for entry in data_list:
		items = entry.split(':')
		key, value = items[0], items[1]
		key = key.rstrip()
		key = key.replace(' ','_')
		value = value.lstrip()
		value = value.replace(' MB','')
		if value == None:
			value=""
		data_out.setdefault(key, value)
	return data_out

"""
_parse_hostcpuinfo_output
This function takes a pmlist -s output and
build a beautiful :-) json answer for it.
"""
def _parse_hostcpuinfo_output(result):
	data_out = {}
	reg_exp = re.compile('^(\S+) supports \d+ counters$')
	found = "unknown"
	data_list = result.splitlines()
	for entry in data_list:
		m = reg_exp.match(entry)
		if m:
			found = m.group(1)
	data_out.setdefault('cpuModel', found)
	return data_out

def _parse_hostifinfo_output(result):
	data_out = {}
	reg_exp = re.compile('^(en\d+) Available\s+Standard Ethernet Network Interface$')
	ifs = []
	data_list = result.splitlines()
	for entry in data_list:
		m = reg_exp.match(entry)
		if m:
			ifs.append(m.group(1))
	data_out.setdefault('if', ifs)
	return data_out

@app.route('/wparrip/api/tasks/<task_id>', methods = ['GET'])
def get_task_result(task_id):
	async_res = wpar_check_task(str(task_id))
	if async_res.ready() == True:
		return jsonify(ready=True, task_id=task_id, val=async_res.get()[0], out=async_res.get()[1], err=async_res.get()[2])
	else:
		return jsonify(ready=False)	

@app.route('/wparrip/api/wpars/list', defaults={'wpar_name': None},  methods = ['GET'])
@app.route('/wparrip/api/wpars/list/<wpar_name>', methods = ['GET'])
@crossdomain(origin='*')
def get_list(wpar_name):
	"""
	GET /wparrip/api/wpars/list
	"""
	if wpar_name is None: 
		data = {}
		all, err = wpar_listwpar()
		if err == 0:
			all.rstrip().split('\n')
			header = all[0][1:].split(':')
			all.pop(0)
			all.pop
			for wpar in all:
				values = wpar.split(':') 
				data.update(dict(zip(header, values)))
		else:
			data={}
		return jsonify( { "wpars": [ data ] } )
	else:
		all, err = wpar_listdetailswpar(wpar_name)
		if err == 0:
			result = _parsewpar_output(all.rstrip())
		else:
			result = {}
		return jsonify( { "wpars": result } )

@app.route('/wparrip/api/wpars/create', methods = ['POST'])
@crossdomain(origin='*')
#@requires_auth
def create_wpar():
	"""
	POST /wparrip/api/wpars/create 
	:param json: { "name":"wpar95", "options": {
	"autostart":<yes|no>,
	"backupdevice":<path>,
	"checkpointable":<yes|no>,
	"versioned":<yes|no>,
	"basedir":<path>,
	"filesets":<path>,
	"force":<yes|no>,
	"vg":<vgname>,
	"hostname":<hostname>,
	"postscript":<path>,
	"privateRWfs":<yes|no>,
	"mountdir": { "dir":<path>, "vfs":<namefs|nfs>, "dev":<string> },
	"network": { "address":<ip>, "interface":<string>, "ipv4":<string>, "netmask":<string>, "broadcast":<string>, "ipv6":<string>, "prefixlen":<string> },
	"password":<string>,
	"dupnameresolution":<yes|no>,
	"rootvg":<yes|no>,
	"start":<yes|no>
	}, "image": { "name":<imagename>, "file":<filename>}
	}
	"""
	if not request.json or not 'name' in request.json:
		abort(400)

	data = request.get_json()
	name = data['name']
	
	logging.debug('In create_wpar: name=%s', name)
	
	if 'options' in request.json:
		logging.debug('In create_wpar: options=%s', data['options'])
		options = build_cmd_line(data['options'])
	else:
		options = {}
	
	async_res = wpar_mkwpar.delay( name, options )
	if len(wpars) == 0:
		id = 0
	else:
		id = len(wpars)
	wpar = {
		'id': id,
		'name': name,
		'options': options,
		'done': False
	}
	wpars.append(wpar)

	resp = make_response(jsonify( { 'wpar': wpar } ), 201)
	resp.headers['Location'] = "/wparrip/api/tasks/"+async_res.task_id
	return resp

@app.route('/wparrip/api/wpars/<wpar_name>', methods = ['PUT'])
@crossdomain(origin='*')
def update_wpar(wpar_name):
	"""
	PUT /wparrip/api/wpars/<wpar_name>
	This API allows to update a wpar.
	By updating we mean:
	* Start
	* Stop
	* Reboot
	* Save
	* Restore
	* Migrate
	* Update
	:params json:
	{ "name":<wpar_name>, "state":<start|stop|reboot|save|restore|migrate|update>, "file":<used for save, restore and migrate>
	"""
	if len(str(wpar_name)) == 0:
		abort(404)
	if not request.json:
		abort(400)
	if 'state' in request.json and type(request.json['state']) is not unicode:
		abort(400)

	wpar_state = request.json.get('state')
	if wpar_state == 'save' or wpar_state == 'restore' or wpar_state == 'migrate':
		 if 'file' in request.json and type(request.json['file']) is not unicode:
                	abort(400)

	file = str(request.json.get('file'))
	name = str(wpar_name)

	if (wpar_state == 'start'):
		async_res = wpar_startwpar.delay(name )
	elif (wpar_state == 'stop'):
		async_res = wpar_stopwpar.delay( name )
	elif (wpar_state == 'reboot'):
		async_res = wpar_rebootwpar.delay( name )
	elif (wpar_state == 'save'):
		async_res = wpar_savewpar.delay( name, file )
	elif (wpar_state == 'restore'):
		async_res = wpar_restorewpar.delay( name, file )
	elif (wpar_state == 'migrate'):
		async_res = wpar_migwpar.delay( name, file )
	elif (wpar_state == 'update'):
		async_res = wpar_syncwpar.delay( name )
	else:
		abort(404)
		
	wpar = {
		'name': name,
		'wpar_state': wpar_state,
		'done': False
	}
	resp = make_response(jsonify( { 'wpar': wpar } ), 201)
	resp.headers['Location'] = "/wparrip/api/tasks/"+async_res.task_id
	return resp

@app.route('/wparrip/api/wpars/<wpar_name>', methods = ['DELETE'])
@crossdomain(origin='*')
def delete_wpar(wpar_name):
	"""
	DELETE /wparrip/api/wpars/<wpar_name>
	"""
	if len(str(wpar_name)) == 0:
		abort(404)
	name = str(wpar_name)
	async_res = wpar_rmwpar.delay( name )
	resp = make_response(jsonify( { 'state': 'Deleting' } ), 201)
	resp.headers['Location'] = "/wparrip/api/tasks/"+async_res.task_id
	return resp

@app.route('/wparrip/api/host', methods = ['GET'])
@crossdomain(origin='*')
def stats_host():
	"""
	GET /wparrip/api/host
	"""
	
	result = host_stats()
	resp = _parse_hostinfo_output(result)
	
	result = host_cpustats()
	cpuresp = _parse_hostcpuinfo_output(result)
	
	result = host_network_devices()
	ifstats = _parse_hostifinfo_output(result)
	
	oslevel = host_os_stats()
	
	return jsonify( { 'host': { 'stats' : resp, 'cpu' : cpuresp , 'network' : ifstats, 'oslevel' : oslevel } } )

@app.route('/wparrip/api/host/status', methods = ['GET'])
@crossdomain(origin='*')
def status_host():
	"""
	GET /wparrip/api/host/status
	"""
	result = host_status()	
	return jsonify( { 'host': result} )

@app.route('/wparrip/api/host/shutdown', methods = ['GET'])
@crossdomain(origin='*')
def shutdown_host():
	"""
	GET /wparrip/api/host/shutdown
	"""
	logging.debug('In shutdown_host')
	result = host_shutdown()
	return jsonify( { 'host': { 'status': result}} )

@app.route('/wparrip/api/host/reboot', methods = ['GET'])
@crossdomain(origin='*')
def reboot_host():
	"""
	GET /wparrip/api/host/reboot
	"""
	logging.debug('In reboot_host')
	result = host_reboot()
	return jsonify( { 'host': { 'status': result}} )

def _read_image(image_name):
	try:
		f = open(image_local+'/'+image_name, "r")
	except IOError:
		return None
	else:
		with f:
			obj = json.loads(f.read())
		return obj
	
def _create_image(data):
	if data['type'] is None:
		oslevel = host_os_stats()
		data = {
			'image' : {
			'name':data['name'],
			'id': uuid.uuid4(),
			'hypervisor': 'warrip',
			'type':data['type'], 
			'date': time.strftime("%c"),
			'oslevel': oslevel,
			'tl': oslevel,
			'app': None
			}
		}
	elif data['type'] == "mksysb":
		data = _inspect_image(data['name'])
	elif data['type'] == "app":
		if not data or not 'app':
			abort(400)
		oslevel = host_os_stats()
		data = {
			'image' : {
			'name':data['name'],
			'id': uuid.uuid4(),
			'hypervisor': 'warrip',
			'type':data['type'], 
			'date': time.strftime("%c"),
			'oslevel': oslevel,
			'tl': oslevel,
			'app': data['app']
			}
		}
	async_res = image_create.delay(image_local, data)
	return async_res

@app.route('/wparrip/api/images/create', methods = ['POST'])
@crossdomain(origin='*')
def create_image():
	"""
	!DANGER!
		Well, that where the implement new functions that regular WPARs do not support
	!DANGER!
	For WPARs container, we can have several ways of booting them form images:
		- No images: the wpar is created based on the parent LPAR image
			- In this case, an image is automatically uploaded in Glance containing an image.info file with the LPAR OS level
		- mksysb: this is used for Versioned WPARs
			- In this case, we have to chek that the mksysb fits the requirements, then proceed
		- <app>: the wpar is an application WPAR, thus only the name of the app to launch needs to be known
			- In this case, the image will contains an image.info file with the script used to launch the app
		- PaaS like behavior:
			- In this case, we need a base to customize. The image.info file contains the customization
	"""
	# Handle the first case.
	data = request.get_json()
	if not data or not 'name' in data:
		abort(400)
	
	res = _read_image(data['name'])
	if res is None:
		async_res = _create_image(data)
		logging.debug('In create_image imagename=%s',imagename)
		resp = make_response(jsonify( { 'image': data['name'] } ), 201)
		resp.headers['Location'] = "/wparrip/api/tasks/"+async_res.task_id
	else:
		resp = make_response(jsonify( res ), 200)

	return resp

@app.route('/wparrip/api/images/push', methods = ['POST'])
@crossdomain(origin='*')
def image_upload():
	"""
	Given an image_id (uuid format BUT NOT related to the one used by Glance
	(will see if we would match them later on)), we upload the image to a
	remote image repository. A remote image repository can be Glance
	(and it is in this release), or any other in the __future__ (EC3,....)
	Note: licensing is not an issue (except when mksysb are used for versionned WPARs),
	and enforcing it is even less my issue... gentlemen, just pay your bills.
	"""
	data = request.get_json()
	
	glance = glance.GlanceStorage(None)
	glance.put_content(os.path.join(image_local,data['name']),None)
	resp = make_response(jsonify( {'status':'Done'} ), 200)
	return resp

@app.route('/wparrip/api/images/pull', methods = ['POST'])
@crossdomain(origin='*')
def image_download():
	"""
	The other way around... we download an image coming from
	Glance (or another source __future__). 
	Once done, it can be used to deploy a WPAR...
	"""
	ret_code = 404
	logging.debug('In image_download')
	print '------->'+str(request.headers)+'<------------'
	#print '------->'+str(request.data)+'<------------'
	local_filename=request.headers['X-Meta-Glance-Image-Id']
	file = os.path.join(image_local,local_filename)
	# At this step, we suppose that the Glance image format is known (TGZ is the default)
	# __future__: extend this defaultvalue with ISO, and mksysb
	if request.headers['Wparrip-Image-format'] == 'TGZ':
		f = open(file, 'wb')
		data = request.data
		if data:
			f.write(data)
			f.close()
			ret_code = 200
	resp = make_response(jsonify( {'image':local_filename} ), ret_code)
	return resp

def _inspect_image(image_fullpath):
	result, out = image_inspect(image_fullpath)
	data = None
	#Now decode the output
	if result == 0:
		""" Here is what the stdout will look like (we do not need VG info):
		VOLUME GROUP:           rootvg
		BACKUP DATE/TIME:       Wed Mar 27 23:07:10 CDT 2013
		UNAME INFO:             AIX nim01 1 7 00F81B111C00
		BACKUP OSLEVEL:         7.1.2.0
		MAINTENANCE LEVEL:      7100-00
		BACKUP SIZE (MB):       24896
		SHRINK SIZE (MB):       17634
		VG DATA ONLY:           no
		"""
		if out and out != "":
			data_list = out.splitlines()
			data = { 'image' : {
				'name':image_fullpath,
				'id': uuid.uuid4(),
				'hypervisor': 'wparrip',
				'type':'mksysb', 
				'vg': data_list[0].split(":")[1].lstrip(' '),
				'date': data_list[1].split(":")[1].lstrip(' '),
				'uname': data_list[2].split(":")[1].lstrip(' '),
				'oslevel': data_list[3].split(":")[1].lstrip(' '),
				'tl': data_list[4].split(":")[1].lstrip(' '),
				'bsize': string.atoi(data_list[5].split(":")[1].lstrip(' ')) * 1024,
				'ssize': string.atoi(data_list[6].split(":")[1].lstrip(' ')) * 1024,
				'vgdataonly': data_list[7].split(":")[1].lstrip(' '),
				'app': None
				}
			}
	return data

@app.errorhandler(404)
def not_found(error):
	return make_response(jsonify( { 'error': 'Not found' } ), 404)

if __name__ == '__main__':
	port = int(os.getenv('PORT', 5000))
	app.run(host=config.LPAR_ADDRESS, port=port)
