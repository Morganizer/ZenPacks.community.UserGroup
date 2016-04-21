# Module-level documentation will automatically be shown as additional
# information for the modeler plugin in the web interface.
"""
UserGroupMap
SSH plugin to gather user group and user information
"""

# When configuring modeler plugins for a device or device class, this plugin's
# name would be cmd.UserGroupMap because its filesystem path within
# the ZenPack is modeler/plugins/cmd/UserGroupMap.py. The name of the
# class within this file must match the filename.

# CommandPlugin is the base class that provides lots of help in modeling data
# that's available by connecting to a remote machine, running command line
# tools, and parsing their results.
from Products.DataCollector.plugins.CollectorPlugin import CommandPlugin

# Classes we'll need for returning proper results from our modeler plugin's process method.
from Products.DataCollector.plugins.DataMaps import ObjectMap, RelationshipMap
from Products.ZenUtils.Utils import prepId
import collections
from itertools import chain

class UserGroupMap(CommandPlugin):
    # relname and modname for the CommandPlugin will be inherited by any calls to
    #    rm = self.relMap()   or om = self.objectMap()
    # No compname specified here as UserGroup is a component directly on the device (defaults to null string)
    # classname not required as largely deprecated. classname is the same as the module name here
    relname = 'userGroups'
    modname = 'ZenPacks.community.UserGroup.UserGroup'

    deviceProperties = CommandPlugin.deviceProperties +(
        'zMinUID',
        )

    # The command to run.
    # Get user groups (one per line) then a line with __SPLIT__ then users (one per line)
    # Beware this has potential to return LOTS of data
    command = (
            'getent group ;'
            'echo __SPLIT__; '
            'getent passwd'
            )

    def process(self, device, results, log):
        log.info("Modeler %s processing data for device %s",
            self.name(), device.id)
        #log.debug('results is %s ' % (results))

        # Setup an ordered collection of dictionaries to return data to the ApplyDataMap routine of zenmodeler
        maps = collections.OrderedDict([
            ('myuserGroups', []),
            ('myusers', []),
        ])
        # Instantiate a relMap.  This inherits relname and compname from the plugin.
        rm = self.relMap()

        # For CommandPlugin, the results parameter to the process method will
        # be a string containing all output from the command defined above.
        # 
	#root:x:0:
	#daemon:x:1:
	#adm:x:4:pi
	#audio:x:29:pi,mollie
	#mollie:x:1003:
        # __SPLIT__
	#root:x:0:0:root:/root:/bin/bash
	#daemon:x:1:1:daemon:/usr/sbin:/bin/sh
	#zenplug:x:1001:1002::/home/zenplug:/bin/bash
	#snmp:x:107:110::/var/lib/snmp:/bin/false
	#mollie:x:1002:1003:Mol:/home/mollie:/bin/bash

        # lines[0] are the user groups    lines[1] are the users
        lines = results.split('__SPLIT__')
        for ug in lines[0].split('\n'):
            #log.debug(' group is %s' % (ug))
            if ug:
                try:
		    # split each line on ':'
		    ugList = ug.split(':')
		    # ugList[0] = groupName, uglist[2] = GID, ugList[3] = secondaryUsers
		    ug_id = prepId(ugList[0])             # Ensure no dodgy characters in id
		    # Add an Object Map for this user group 
		    # Use prepId to ensure id is unique and doesn't include any dodgy characters like /
		    # om = self.objectMap() inherits modname and compname (null) from plugin
		    om = self.objectMap()
		    om.id = ug_id
		    om.groupName = ugList[0]
		    om.GID = int(ugList[2])    # GID defined as integer so need to ensure this
		    om.secondaryUsers = ugList[3]
                    # hasSecondaries takes string value that matches an event status so that
                    #   we can cheat and use Zenoss.render.severity to give icons for this value
                    #   If secondaries exist then we get the green 'clear' icon. Otherwise red.
                    if ugList[3]:
                        om.hasSecondaries = 'clear'
                    else:
                        om.hasSecondaries = 'critical'
		    rm.append(om)
		    # For this user group, create a map for associated users, passing this ug_id as part of compname
		    log.debug('GID is %s ' % (om.GID))
		    um = (self.getUserMap( device, lines[1], int(ugList[2]), ugList[0], 'userGroups/%s' % ug_id, log))
		    #log.debug('ug %s has um  %s \n um relname is %s and um compname is %s ' % (om.id, um, um.relname, um.compname))
		    maps['myusers'].append(um)
                except Exception as e: 
                    log.info('Exception in group processing - %s' % (e))
                    continue

        if len(rm.maps) == 0:
            log.info('No user group data found on %s ' % (device.id))
            return None

        # Add the rm relationships to maps['myuserGroups']
        maps['myuserGroups'].append(rm)

        # Need this complicated setup with maps = collections.OrderedDict and the chain return
        #   to ensure that relationship maps are applied in the correct order.  Otherwise there tend
        #   to be issues trying to create relationships on objects that don't yet exist
        return list(chain.from_iterable(maps.itervalues()))

    def getUserMap(self, device, users_string, GID, ugName, compname, log):
        #log.debug('users_string is %s , compname is %s GID is %s' % (users_string, compname, GID))
        user_maps = []
        for u in users_string.split('\n'):
            if u:
		#log.debug(' user is %s' % (u))
		# Split out each user fields divided by colons
		uList = u.split(':')
		# uList[0] = userName ulist[2] = UID, uList[3] = primary GID, 
                #   uList[4] = userComment  uList[5] = homeDir  uList[6] = commandShell
                if int(uList[2]) >= int(device.zMinUID):
		    try:
			#log.info('Found user %s in group %s ' % (uList[0], ugName))
			if int(uList[3]) == GID:		# got a match with this group
			    user_id = prepId(uList[0])      # Ensure no dodgy characters in id
			    # Don't want to inherit compname or modname from plugin as we want to set this expicitly
			    # Use ObjectMap rather than om=self.objectMap()
			    user_maps.append(ObjectMap(data = {
				'id': prepId(uList[0]),
				'userName' : uList[0],
				'UID' : int(uList[2]),
				'primaryGID' : int(uList[3]),
				'primaryGroupName' : ugName,
				'userComment' : uList[4],
				'homeDir' : uList[5],
				'commandShell' : uList[6],
				}))
			    log.info('Found user %s in group %s ' % (user_id, ugName))
		    except Exception as e:
			log.info('Exception in user processing - %s ' % (e))
			continue

        # Return user_maps relationship map with compname passed as parameter to this method
        # Again - don't want to inherit relname, modname or compname for this relationship as we want to set them explicitly
        # Use RelationshipMap rather then rm=self.relMap()(
        return RelationshipMap(
            compname = compname,
            relname = 'users',
            modname = 'ZenPacks.community.UserGroup.User',
            objmaps = user_maps)


