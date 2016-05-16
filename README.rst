============================
ZenPacks.community.UserGroup
============================

Description
===========
This ZenPack monitors Operating System users and user groups.
It is almost entirely created with zenpacklib (Version 1.0.11).
It uses a COMMAND modeler and a COMMAND template.

In addition to standard zenpack.yaml definition of Zenoss device classes and
device and component object classes, along with templates, it also demonstrates
using custom icons and the use of creating and calling methods for a 
component object.


zenpacklib usage
----------------

This ZenPack is built with the zenpacklib library so does not have explicit code definitions for
device classes, device and component objects or zProperties; however a User.py file *does* exist
to provide a method to derive secondary user groups for a user.

Templates are also created through zenpacklib.
These elements are all created through the zenpack.yaml file in the main directory of the ZenPack.
See http://zenpacklib.zenoss.com/en/latest/index.html for more information on zenpacklib.

Note that if templates are changed in the zenpack.yaml file then when the ZenPack is reinstalled, the
existing templates will be renamed in the Zenoss ZODB database and the new template from the YAML file
will be installed; thus a backup is effectively taken.  Old templates should be deleted in the Zenoss GUI
when the new version is proven.


Features
========

Zenoss Device Classes
---------------------

zenpacklib creates */Server/Linux/UserGroup* with:

* zPythonClass: ZenPacks.community.UserGroup.UserGroupDevice
* zDeviceTemplates:

  - DnsMonitor
  - Device

* zSshConcurrentSessions: 5
* zCollectorPlugins: ['zenoss.snmp.NewDeviceMap', 'zenoss.snmp.DeviceMap', 'zenoss.snmp.InterfaceMap', 'zenoss.snmp.RouteMap', 'zenoss.snmp.IpServiceMap', 'zenoss.snmp.HRFileSystemMap', 'zenoss.snmp.HRSWRunMap', 'zenoss.snmp.CpuMap', 'zenoss.snmp.SnmpV3EngineIdMap', 'cmd.UserGroupMap']

* The User component template is created, available to this class


Device and component object classes
-----------------------------------
* UserGroupDevice  - it has no new attributes

  - uses an icon defined by four-tux-56x56.png, shipped in the resources/icon subdirectory of the ZenPack.

* UserGroup component class with attributes:

  - groupName
  - GID
  - secondaryUsers
  - hasSecondaries

  - monitoring_templates set to [UserGroup]


* User component class with attributes:

  - userName
  - UID
  - primaryGID
  - primaryGroupName
  - getSecGroups  (this demonstrates an object method property)
  - userComment
  - homeDir
  - commandShell

  - monitoring_templates set to [User]

Relationships are:
  * UserGroupDevice -> contains many UserGroup components -> contains many User components

Properties
----------

zenpacklib creates a zProperty, *zMinUID* used to limit the number of users discovered to
those with a UID greater than or equal to zMinUID.


Modeler Plugins
---------------

There is no device-level modeler.

* UserGroupMap in modeler/plugins/cmd, a COMMAND modeler which populates:

  - UserGroups
  - Users with the UserGroup as their primary GID


Monitoring Templates
--------------------

* Device templates
   
  - no device templates are shipped

* Component templates

  - User with a single COMMAND datasource to gather the number of groups for a given user.


Datasources
-----------

None.

Events
------

None.


GUI modifications
-----------------

The hasSecondaries attribute of the UserGroup demonstrates the use of a renderer in zenpack.yaml
to display a coloured icon.

Usage
=====

The new zProperty for zMinUID may be adjusted for a device class or specific device.
The default is 0 (all users collected).

Ensure that suitable values for zCommandUsername, zCommandPassword and zKeyPath are customised for the device class
and potentially overridden for specific devices.

Test ssh communications from the command line before expecting Zenoss to perform successful ssh communications.


Requirements & Dependencies
===========================

* Zenoss Versions Supported:  4.x, 5.x
* External Dependencies: 

  - The zenpacklib package that this ZenPack is built on, requires PyYAML.  This is installed as standard with Zenoss 5 and with Zenoss 4 with SP457 and later.
    To test whether it is installed, as the zenoss user, enter the python environment and import yaml::

        python
        import yaml
        yaml

        <module 'yaml' from '/opt/zenoss/lib/python2.7/site-packages/PyYAML-3.11-py2.7-linux-x86_64.egg/yaml/__init__.py'>

    If pyYAML is not installed, install it, as the zenoss user, with::

        easy_install PyYAML

    and then rerun the test above.

* ZenPacks:
  - None


* Installation Notes: 

  - Restart zenoss entirely after installation 



Download
========
Download the appropriate package for your Zenoss version from the list
below.

* Zenoss 4.0+ and 5.x  `Latest Package for Python 2.7`_

ZenPack installation
======================

This ZenPack can be installed from the .egg file using either the GUI or the
zenpack command line. 

To install in development mode, find the repository on github and use the *Download ZIP* button
(right-hand margin) to download a tgz file and unpack it to a local directory, say,
/code/ZenPacks .  Install from /code/ZenPacks with::
  zenpack --link --install ZenPacks.community.UserGroup
  Restart zenoss after installation.

Device Support
==============

This ZenPack only requires very basic Unix commands on the target devices.

Limitations and Troubleshooting
===============================



Change History
==============
* 1.0.0
   - Initial Release
* 1.0.1
   - UserGroup is a component of Device in core code
   - or UserGroup is a component of component os  in core code
   - this is in GitHub device branch
   - 3 files need changing to swap UserGroup from a device component to an os subcomponent
      - zenpack.yaml - replace with either zenpack.yaml_device or zenpack.yaml_osComp
      - __init__.py - replace with __init__.py_device or __init__.py_osComp
      - modeler/plugins/cmd/UserGroupMap.py - replace with UserGroupMap.py_device or UserGroupMap.py_osComp


Screenshots
===========

See the screenshots directory.


.. External References Below. Nothing Below This Line Should Be Rendered

.. _Latest Package for Python 2.7: https://github.com/ZenossDevGuide/ZenPacks.community.UserGroup/blob/device/dist/ZenPacks.community.UserGroup-1.0.1-py2.7.egg?raw=true

Acknowledgements
================


