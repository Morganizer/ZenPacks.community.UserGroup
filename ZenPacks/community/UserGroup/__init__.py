from . import zenpacklib

CFG = zenpacklib.load_yaml()

## Contributed by James Newman - see https://gist.github.com/James-Newman/9609c84688a0b9a4fee842878b9a5b00 
##  This is an example of executing code when your zenpack gets installed (or removed)
## This __init__.py file should be located at ZenPacks.namespace.Name/ZenPacks/namespace/Name/__init__.py
## This code should be carefully added to your zenpack so as not to accidently overwrite key methods (

'''
Here begins the non default code
'''
# Import all the things.
import logging
# Log information shows up in $ZENHOME/log/events.log, as well as stdout if installing/removing via the command line
log = logging.getLogger('zen.UserGroup')

# Only need to import ZenPackBase if NOT using zenpacklib
# Using zenpacklib, need to import schema to inherit ZenPack class from zenpacklib
#from Products.ZenModel.ZenPack import ZenPack as ZenPackBase
from . import schema

# Make our configuration variable names global,
# its easier than passing them around to every method
global deviceClassToAdd
global templatesToAdd
global leaveDeviceClass
global updateTemplates

# We use deviceClassToAdd as a dictionary of classes and templates
# Template name should be identical to the one either already in Zenoss or provided in the objects.xml or zenpack.yaml file within the ZenPack
# Thats right,  you can use this way of adding templates to add classes that are provided by other zenpacks
# If a class already exists then nothing bad happens.
# Leaving the value as an empty list means that no changes get done,  the class just inherits from the parent
# If a parent doesn't exist, it automatically gets created
deviceClassToAdd = {'Server/Linux/UserGroup' : ['FtpMonitor'],
                    'Server/Linux': ['DnsMonitor']
                    }
# These are the properties that mean our classes stick around during an uninstall or not
# Times when you want to keep the classes are when you have other zenpacks that are using the class, or a child of the class
# Or when you want to keep things around for posterity because you're a sentimental old fool and you like a bit of whimsy.
leaveDeviceClass = True

# If working WITHOUT zenpacklib, ZenPack inherits from ZenPackBase;
# otherwise inherit via schema from the ZenPack class defined in zenpacklib.
#class ZenPack(ZenPackBase):
class ZenPack(schema.ZenPack):
    # This is the standard install method. It gets called when you install the zenpack
    def install(self, app):

        log.info('Beginning Installation.')

        # If using zenpacklib, install the stuff defined by zenpacklib FIRST and
        #  then modify with this customisation.  Otherwise this stuff is
        #  overridden by zenpacklib stuff.
        super(ZenPack, self).install(app)
        # Create the new device classes and add templates
        # We iterate over the class/templates in the deviceClassToAdd dictionary
        log.info('Starting template customisation from ZenPack __init__')
        for classToAdd, templatesToAdd in deviceClassToAdd.iteritems():
            # Add the requested device class
            # Here we kick our the actual creation to a new method to make things easier for us
            # If the device class already exists, then the existing organizer is returned.
            addedDeviceClass = self.createDeviceOrganiserPath(classToAdd)
            # You can also run a bunch of custom stuff here on the new addedDeviceClass if you want
            # for example you can set the properties using 
            # addedDeviceClass.setZenProperty('zCommandUsername', 'root')
            # addedDeviceClass.setZenProperty('zCommandPassword', 'NOTSECURE')
            # Obviously, any passwords you put in here aren't secure, as your __init__.py is plain text!
            log.info(' Updating zProperty zSshConcurrentSessions; new value is 5')
            addedDeviceClass.setZenProperty('zSshConcurrentSessions', 5)
            # Once the class is added,  we can add the template, only if the template list has an element
            # Again we kick it out to a new method to make things easier for us
            if len(templatesToAdd) > 0:
                # Add the requested templates to the new device class
                self.setTemplates(addedDeviceClass, templatesToAdd)

        # Instruct Zenoss to install any objects into Zope from the objects.xml file contained inside the ZenPack
        # Once you get down here,  running this next line will tell zenoss to install the zenpack as it normally would
        # For non zenpacklib, use ZenPackBase.install;
        #  for zenpacklib, use super(ZenPack, self).install(app)
        #ZenPackBase.install(self, app)
        #super(ZenPack, self).install(app)


    # This is the standard remove method
    # it gets called when you remove the zenpack
    # If the install method is just to add templates, not classes, ensure
    # that leaveDeviceClass=True so that classes are not removed, only templates
    def remove(self, app, leaveObjects=False):

        log.info('Beginning ZenPack removal.')

        log.info('Starting template customisation from ZenPack __init__')
        # Remove the device class, this ensures that we don't remove devices as well if we don't want to
        # Again we iterate over the device classes and templates that the zenpack adds
        for classToRemove, templatesToRemove in deviceClassToAdd.iteritems():
            deviceClassToRemove =  self.dmd.Devices.getOrganizer(classToRemove)
            if deviceClassToRemove:
                # Only if we're removing templates do we run the new method to remove templates from device classes
                if len(templatesToRemove) > 0:
                    self.removeTemplatesFromDeviceClass(classToRemove, templatesToRemove)
                # This check here is what stops us removing device classes.  If we have leaveDeviceClass set to True,
                # then the device class will be left behind
                if leaveDeviceClass == False:
                    deviceList = self.removeDeviceOrganiser(classToRemove)
                # reset zproperty to default value of 10
                log.info(' Resetting zProperty zSshConcurrentSessions to default; new value is 10')
                deviceClassToRemove.setZenProperty('zSshConcurrentSessions', 10)

        # Instruct Zenoss to remove any objects from Zope from the objects.xml file contained inside the ZenPack
        # Once you get down here,  running this next line will tell zenoss to remove the zenpack as it normally would
        # For non zenpacklib, use ZenPackBase.remove;
        #  for zenpacklib, use super(ZenPack, self).remove(app, leaveObjects)
        #ZenPackBase.remove(self, app)
        super(ZenPack, self).remove(app, leaveObjects)

    '''The Installation Methods'''
    # All the new custom methods that will install things for you


    def createDeviceOrganiserPath(self, deviceClassToAddString):
        '''
        This creates the iterative device class path
        Why do we do it this way? Well if you want to add /Server/Linux/Foo/Bar in your zenpack
        but /Server/Linux/Foo doesn't exist in your zenoss install then you get a slightly confusing 
        KeyError exception when you try and install things
        Adding the device class iteratively gets around this
        If the class already exists, the existing organizer is simply returned.
        '''

        # Split up the requested device class and sequentially create it.
        classList = []
        classList = deviceClassToAddString.split('/')

        # Loop over the Class List and create all required child classes.
        for i in range(len(classList)):
            org = ('/').join(classList[:len(classList)+1-(len(classList)-i)]) # The sequenial path generator!  Fear it's confusion.
            try:
                # Test for the class already existing
                if self.dmd.Devices.getOrganizer(org):
                    log.info('Device Class %s already exists.', str(org))
            except KeyError:
                # The class doesn't exist, so we create it.
                log.info('Creating new device class at %s', str(org))
                self.dmd.Devices.createOrganizer(org)
                from transaction import commit
                commit()

        return self.dmd.Devices.getOrganizer(deviceClassToAddString)

    def setTemplates(self, deviceClass, newTemplates):
        '''
        This new method sets the templates for us.  We do this by 
        manipulating the zDeviceTemplates property of the class
        '''

        # Obtain the zDeviceTemplates of the newly created class, and add any extras.
        # We don't need to worry about getting the parent templates and artificially inheriting them,
        # Zenoss takes care of this for us.
        log.info('The following templates will be added; %s.', str(newTemplates))

        # Get the zDeviceTemplates of the new device class and copy it to a new list
        templates = list(deviceClass.zDeviceTemplates)
        log.info('The following templates have been inherited already; %s', str(templates))

        # Loop over the list of templates provided in the config section
        updateTemplates = False
        for template in newTemplates:
            if template not in templates:
                # Template is new, so we add it to the templates list.
                templates.append(template)
                updateTemplates = True
                log.info('%s added to templates', template)

        if updateTemplates == True:
            # If we need to update the templates on the device class, here we set the Zen Property and commit the change
            # Doing this automatically sets the zDeviceTemplates as a local copy
            # It will stop inheriting changes to parent properties!
            deviceClass.setZenProperty( 'zDeviceTemplates', templates )
            log.info('Device Class zDeviceTemplates updated to: %s', str(templates))
            from transaction import commit
            commit()
        else:
            # We don't have to update the templates, so we just log that and end the function
            # This way we don't start creating local copies of the zproperty if you dont need to
            log.info('No new templates need to be added.')

    '''The Removal Methods'''

    def removeTemplatesFromDeviceClass(self, deviceClassToRemoveString, templatesToRemove):
        '''
        This new method removes the previously added templates for us.  We do this by 
        manipulating the zDeviceTemplates property of the class
        '''
        # Obtain the device class that we need to remeove the tempalte from
        deviceClass = self.dmd.Devices.getOrganizer(deviceClassToRemoveString)
        # Copy the device template list from the device class
        templates = list(deviceClass.zDeviceTemplates)

        # Loop over the list of templates that we need to remove from the device class
        updateTemplates = False
        for template in templatesToRemove:
            if template in templates:
                # The template to remove has been found in the current templates.  We remove it from the list
                templates.remove(template)
                log.info('%s has been configured to be removed from the Device Class %s' % (template, deviceClassToRemoveString))
                updateTemplates = True
            else:
                # The template hasn't been found.  We don't need to remove the template.
                log.info("%s hasn't been found within the existing list of templates: %s" % (template, templates))

        if updateTemplates == True:
            # Taking our new templates list, we set the Device class property as required and commit
            # It should be noted that this will still leave the zProperty as a local copy
            # its left as an exercise for the reader to determine if they want this behaviour,
            # and if not, adjust the code accordingly.
            deviceClass.setZenProperty( 'zDeviceTemplates', templates )
            log.info('Device Class zDeviceTemplates updated to: %s', str(templates))
            from transaction import commit
            commit()
        else:
            # Nothing to be done.  Log and end the function.
            log.info('No templates need to be removed')

    def removeDeviceOrganiser(self, deviceClassToRemoveString):
        '''
        If you want to remove the device class then this chap will run
        The benefit of using this code is that while the deviceClass gets removed
        the devices in it will be moved to a new Homeless class so that the don't get
        completely deleted.  You can then delete them manually at your own discretion
        '''

        # Get our created child device class
        deviceClassToRemove = self.dmd.Devices.getOrganizer(deviceClassToRemoveString)

        log.info('The following device class will be removed: %s', str(deviceClassToRemove))

        # Check if the device class is empty of devices, if its not remidiate.
        if len(deviceClassToRemove.getSubDevices_recursive()) > 0:
            log.warn('Devices exist within this device class.  They will be moved to a holding area under the existing OS class.')

            # Set the parent OS device Class,  either a two stage Class is returned (Server/Linux), or a one stage class (Networking)
            try:
                parentOSClass = ('/').join(deviceClassToRemoveString.split('/')[:2])
            except:
                parentOSClass = ('/').join(deviceClassToRemoveString.split('/')[:1])

            # Create a homeless class string based on the parent class
            homelessClass = parentOSClass + '/' + 'Homeless'

            try:
                # Try and get the homeless class object
                if self.dmd.Devices.getOrganizer(homelessClass):
                    log.info('Device Class %s already exists.', str(homelessClass))
            except KeyError:
                # The homeless class doesn't exist, so we create it
                log.info('Creating new Device Class at %s', str(homelessClass))
                self.dmd.Devices.createOrganizer(homelessClass)

            for dev in deviceClassToRemove.devices():
                # Move the devices in our target device class to the homeless device class
                log.info('Moving device %s to the Homeless Device Class.', dev.id)
                dev.changeDeviceClass(homelessClass)

            # Test again to see if there are devices in the class.  If there are, something very wrong has broken and we log an error
            if len(deviceClassToRemove.getSubDevices_recursive()) > 0:
                log.error('Devices exist within this Device Class.  Even after moving them to a new class. Something very wrong has happened.  The Device Class will NOT be removed.')
            else:
                # Everything has worked correctly, we remove our target device class
                log.info('Attempting to remove the device class.')
                classParent = deviceClassToRemove.getParentNode()
                classParent.manage_deleteOrganizer(deviceClassToRemoveString.split('/')[-1])

        else:
            # No devices exist within our target device class, we can just remove the class
            classParent = deviceClassToRemove.getParentNode()
            classParent.manage_deleteOrganizer(deviceClassToRemoveString.split('/')[-1])

