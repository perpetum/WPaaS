#!flask/bin/python
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
"""
    config
    ~~~~~
    This file contains the configuration options
    
    :copyright: (c) 2013 by Matthieu Isoard
"""

# This Configuration files has to be updated
# before launching celery and the app

# Run in debug mode
# !!! Warning: may crash the Flask server on AIX !!!
DEBUG = False
# When --log option is passed, where do we log?
LOGFILE="/tmp/wparrip.log"
# Celery Brocker URI - By default we use REDIS
BROCKER_URI = 'redis://localhost:6379/0'
# Celery Backend URI - By default we use REDIS
BACKEND_URI = 'redis://localhost:6379/0'
#ReST protocol
PROTOCOL = "http"
#ReST authentification
AUTH_LOGIN = "root"
AUTH_PASSWD = "cloud123"
# Server IP address
LPAR_ADDRESS = '10.197.160.84'
# Restrict or open Cross-Domain policy
CROSS_DOMAIN_RULE = '*'
#Local image repository - Can be local, NFS share, or other
IMAGE_REPOSITORY_LOCAL="/tmp"
#Remote image repository - None or glance for now (Swift, EC3, etc... in a near future)
#Make sure with Glance that the Python keystoneclient.v2_0 has been installed
IMAGE_REPOSITORY_REMOTE="glance"
