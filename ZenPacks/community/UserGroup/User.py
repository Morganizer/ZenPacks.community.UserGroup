#######################################################################
#
# This program is part of the ZenPacks.community.UserGroup ZenPack
#
# Author:	Jane Curry
# Date:		April 21st, 2016
# Updated:
#
# For user (self), find all secondary user groups
# Filename must match object class name, must match class defined here
#
#######################################################################
from . import schema
import logging
LOG = logging.getLogger('zen.UserGroup')

# Need to define a method to get string of group names for a user
# Called by api_backendtype: method in zenpack.yaml

class User(schema.User):                      # class must match component object class 

    def getSecGroups(self):
        d = self.device()		      # get this user's device object
        secGroupList = []
        for g in d.userGroups():              # cycle through all this device's groups
            #if self.id in g.secondaryUsers:   # looking for this user in group's secondaries
            # secondaryUsers is a comma-separated string
            for su in g.secondaryUsers.split(','):
		if self.id == su.strip():      # looking for this user in group's secondaries
		    secGroupList.append(g.id)  # add the group id on a match
                    break

        return ','.join(secGroupList)         # return list, converted to string, comma sep
