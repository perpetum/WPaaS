#!flask/bin/python
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
# Celery Brocker URI
BROCKER_URI = 'redis://localhost:6379/0'
# Celery Backend URI
BACKEND_URI = 'redis://localhost:6379/0'
# Server IP address
LPAR_ADDRESS = '10.197.160.84'
# Restrict or open Cross-Domain policy
CROSS_DOMAIN_RULE = '*'
