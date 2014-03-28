WPaaS: WPAR Platform as a Service for POWER platform
====================================================

This project aims to leverage AIX WPAR container so they can be:<br/>
	- Managed with a standard REST interface<br/>
	- Be managed from OpenStack (Havana)</br>

<br />
AIX WPAR ReST APIs, incl. Nova driver for OpenStack.<br />
Glance repository can be used to push images to the WPARRIP hypervisor.<br />
<br />
The 'driver' repository contains the Nova driver for the WPARs.<br />
It uses the WPARRIP ReST API to manage the WPARs and LPAR host.<br />
<br />
The 'wpars' repository contains the WPARRIP code.<br />
Its goal is to provide ReST APIs to manage the WPARs and
get some info on the LPAR host.<br />
<br />
<h3>Features:</h3>
	- Spawn a WPAR with Network and Image information<br />
	- Start a WPAR<br />
	- Stop a WPAR<br />
	- Delete a WPAR<br />
<br />
<h3>Status:</h3>
	- the code works, and a WPAR can be deployed using OpenStack Havana.<br />
<br />
<h3>TODO List:</h3>
	- Use the uploaded image so the WPAR can be created/configured with the image<br />
	- Support other WPAR actions<br />
	- Attach a volume to a WPAR<br />
	- VNC connection to the WPAR<br />
<br />
<h2>Installation process:</h2>
<b>WPARRIP Hypervisor</b><br />
- Read the install.sh file and follow the step (it will become a real install script one day…)<br />
- Run the env.sh file<br />
- Start the Flask server: $ ./wpars.py<br />
<br />
<b>OpenStack WPARRIP driver</b><br />
- Copy the whole driver repository in <openstack>/nova/nova/<br />
- Modify the config file if needed<br />
- Restart nova<br />
<br />