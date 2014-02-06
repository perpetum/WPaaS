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

import os
import subprocess
import sys
import re
import config

from flask import Flask, jsonify, request, make_response, session, abort, Response
from tasks import host_network_devices, host_cpustats, host_status, host_stats, wpar_listwpar, wpar_listdetailswpar, build_cmd_line, wpar_mkwpar, wpar_check_task, wpar_rebootwpar, wpar_rmwpar, wpar_startwpar, wpar_stopwpar, wpar_restorewpar, wpar_savewpar, wpar_migwpar, wpar_syncwpar
from utils import crossdomain

app = Flask(__name__)

wpars = [ ]

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
	print tmp
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
				#print key +"|"+value
				data_out[main_key][key] += value
			else:
				items = entry.split(':')
        			key, value = items[0], items[1]		
				if value == None:
					value=""
				#print key +"="+value
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
		#print key +"="+value
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

@app.route('/wparrip/api/wpars/<task_id>', methods = ['GET'])
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
		all = wpar_listwpar().rstrip().split('\n')
		header = all[0][1:].split(':')
		all.pop(0)
		all.pop
		for wpar in all:
			values = wpar.split(':') 
			data.update(dict(zip(header, values)))
		return jsonify( { "wpars": [ data ] } )
	else:
		all = wpar_listdetailswpar(wpar_name).rstrip()
		result = _parsewpar_output(all)
		return jsonify( { "wpars": result } )

@app.route('/wparrip/api/wpars/create', methods = ['POST'])
@crossdomain(origin='*')
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
	}
	}
	"""
	if not request.json or not 'name' in request.json:
		abort(400)

	data = request.get_json()
	name = data['name']
	print name
	if 'options' in request.json:
		print data['options']
		options = build_cmd_line(data['options'])
	else:
		options = {}
	
	print options
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
	resp.headers['Location'] = "/wparrip/api/wpars/"+async_res.task_id
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
	resp.headers['Location'] = "/wparrip/api/wpars/"+async_res.task_id
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
	resp.headers['Location'] = "/wparrip/api/wpars/"+async_res.task_id
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
	
	return jsonify( { 'host': { 'stats' : resp, 'cpu' : cpuresp , 'network' : ifstats } } )

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
	print "shutdown"
	result = host_shutdown()
	return jsonify( { 'host': { 'status': result}} )

@app.route('/wparrip/api/host/reboot', methods = ['GET'])
@crossdomain(origin='*')
def reboot_host():
	"""
	GET /wparrip/api/host/reboot
	"""
	print "reboot"
	result = host_reboot()
	return jsonify( { 'host': { 'status': result}} )

@app.errorhandler(404)
def not_found(error):
	return make_response(jsonify( { 'error': 'Not found' } ), 404)

if __name__ == '__main__':
	port = int(os.getenv('PORT', 5000))
	app.run(host=config.LPAR_ADDRESS, port=port)
