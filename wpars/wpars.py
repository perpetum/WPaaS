#!../flask/bin/python

"""
    tasks
    ~~~~~
    This file is contains the  REST API
    
    :copyright: (c) 2013 by Matthieu Isoard
"""

import os
import subprocess
import sys
import re
import config

from flask import Flask, jsonify, request, make_response, session, abort, Response
from tasks import wpar_listwpar, wpar_listdetailswpar, build_cmd_line, wpar_mkwpar, wpar_check_task, wpar_rebootwpar, wpar_rmwpar, wpar_startwpar, wpar_stopwpar, wpar_restorewpar, wpar_savewpar, wpar_migwpar, wpar_syncwpar
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
		#if network == True or routes == True or fs == True or devexport == True:
			#Special cases for white space column names!! F... dev guys
		#	if "Virtual Device" in entry:
		#		entry = entry.replace("Virtual Device","VirtualDevice")
		#	if "EXTENSION NAME" in entry:
		#		entry = entry.replace("EXTENSION NAME","ExtensionName")
		#	entry = re.sub( '\s+', ' ', entry )
		#	values = entry.split(' ')
		#	if header_found == False:
		#		tmp = data_out.setdefault(main_key, dict())
		#		data_out[main_key] = dict((el,[]) for el in values)
		#		header_len = len(values)
		#		header_found = True
		#	else:
		#		while len(values) < header_len:
		#			values.append("")
		#		print values
		#		i=0
		#		for k, v in data_out[main_key].items():
		#			data_out[main_key][k].append(values[i])
		#			i=i+1
		#	continue
	return data_out

@app.route('/bull/api/wpars/<task_id>', methods = ['GET'])
def create_wpar_result(task_id):
	async_res = wpar_check_task(str(task_id))
	if async_res.ready() == True:
                return jsonify(ready=True, val=async_res.get()[0], out=async_res.get()[1], err=async_res.get()[2])
        else:
                return jsonify(ready=False)	

@app.route('/bull/api/wpars/list', defaults={'wpar_name': None},  methods = ['GET'])
@app.route('/bull/api/wpars/list/<wpar_name>', methods = ['GET'])
@crossdomain(origin='*')
def get_list(wpar_name):
	"""
	GET /bull/api/wpars/list
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
		return jsonify( { 'wpars': data} )
	else:
		all = wpar_listdetailswpar(wpar_name).rstrip()
		result = _parsewpar_output(all)
		return jsonify( { 'wpars': result} )

@app.route('/bull/api/wpars/create', methods = ['POST'])
@crossdomain(origin='*')
def create_wpar():
	"""
	POST /bull/api/wpars/create 
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
	"network": { "interface":<string>, "ipv4":<string>, "netmask":<string>, "broadcast":<string>, "ipv6":<string>, "prefixlen":<string> },
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
	options = build_cmd_line(data['options'])
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
	resp.headers['Location'] = "/bull/api/wpars/"+async_res.task_id
	return resp

@app.route('/bull/api/wpars/<wpar_name>', methods = ['PUT'])
@crossdomain(origin='*')
def update_wpar(wpar_name):
	"""
	PUT /bull/api/wpars/<wpar_name>
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
	resp.headers['Location'] = "/bull/api/wpars/"+async_res.task_id
	return resp

@app.route('/bull/api/wpars/<wpar_name>', methods = ['DELETE'])
@crossdomain(origin='*')
def delete_wpar(wpar_name):
	"""
	DELETE /bull/api/wpars/<wpar_name>
	"""
	if len(str(wpar_name)) == 0:
		abort(404)
	name = str(wpar_name)
	async_res = wpar_rmwpar.delay( name )
	resp = make_response(jsonify( { 'state': 'Deleting' } ), 201)
	resp.headers['Location'] = "/bull/api/wpars/"+async_res.task_id
	return resp

@app.errorhandler(404)
def not_found(error):
	return make_response(jsonify( { 'error': 'Not found' } ), 404)

if __name__ == '__main__':
	port = int(os.getenv('PORT', 5000))
	app.run(host=config.LPAR_ADDRESS, port=port)