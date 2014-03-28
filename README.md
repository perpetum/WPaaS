WPaaS
=====

WPAR Platform as a Service for POWER platform. 
AIX WPAR ReST APIs, incl. Nova driver for OpenStack.
Glance repository can be used to push images to the WPARRIP hypervisor.

The 'driver' repository contains the Nova driver for the WPARs.
It uses the WPARRIP ReST API to manage the WPARs and LPAR host.

The 'wpars' repository contains the WPARRIP code.
Its goal is to provide ReST APIs to manage the WPARs and
get some info on the LPAR host.

Features:
	- Spawn a WPAR with Network and Image information
	- Start a WPAR
	- Stop a WPAR
	- Delete a WPAR

Status:
	- the code works, and a WPAR can be deployed using OpenStack Havana.

TODO List:
	- Use the uploaded image so the WPAR can be created/configured with the image
	- Support other WPAR actions
	- Attach a volume to a WPAR
	- VNC connection to the WPAR

