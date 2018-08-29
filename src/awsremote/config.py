'''
Created on 27.08.2018

@author: chof
'''
import os
import json
import sys
from distutils.command.config import config

def getResourcePath(resource): 
    return os.path.join(os.path.dirname(sys.modules['awsremote'].__file__), 
                       resource)
    
class Config(object):
    '''
    classdocs
    '''

    AWSREMOTE_CONFIG = '.awsremote'
        
    @staticmethod
    def enableAWSRemoteConfig(projectpath):
        configfile = projectpath + '/' + Config.AWSREMOTE_CONFIG

        if not os.path.isfile(configfile) :
            import shutil
            shutil.copyfile(getResourcePath('data/templates/configuration_template.json'), 
                            configfile)
        
        return configfile
    
    def _readBaseConfig(self, projectpath):
    #***************************************************************************
        configfile = self.enableAWSRemoteConfig(projectpath)
        
        with open(configfile) as f:
            parameters = json.load(f)
        return parameters
    
    def _writeBaseConfig(self):
    #***************************************************************************
        configfile = self.projectdir + '/' + Config.AWSREMOTE_CONFIG
        with open(configfile, 'w') as outfile:
            json.dump(self.parameters, outfile)

    def __init__(self, projectpath):
    #***************************************************************************
        '''
        Constructor
        '''
        self.projectdir = projectpath
        self.parameters = self._readBaseConfig(projectpath)
        
    def __del__(self):
        self._writeBaseConfig()
        
    def get(self, section, key, default=None):
    #***************************************************************************
        value = default
        if section in self.parameters:
            if key in self.parameters[section]:
                value = self.parameters[section][key]
        return value
    
    def set(self, section, key, value):
    #***************************************************************************
        if not section in self.parameters:
            self.parameters[section] = {
                }
        self.parameters[section][key] = value