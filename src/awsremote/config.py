'''
Created on 27.08.2018

@author: chof
'''
import os
import json
import sys
from distutils.command.config import config
import logging

def getResourcePath(resource): 
    return os.path.join(os.path.dirname(sys.modules['awsremote'].__file__), 
                       resource)
    
class Config(object):
    '''
    classdocs
    '''

    AWSREMOTE_CONFIG = '.awsremote'
    ERROR = -1
    ATTENTION = 0
    INFO = 1
    DEBUG = 2
    
    __LOG_LEVELS = {
      -1 : 40,
       0 : 30,
       1 : 20,
       2 : 10
    }
    
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
        logger = logging.getLogger('awsremote')
        sh = logging.StreamHandler()
        sh.setLevel(logging.DEBUG)
        
        formatter = logging.Formatter("[%(name)s:%(levelname)s]%(asctime)s - %(message)s ")
        sh.setFormatter(formatter)
        
        logger.addHandler(sh)
        
    def __del__(self):
        self._writeBaseConfig()
        
    @property
    def verbosity(self):
    #***************************************************************************
        return self.__verbosity
    
    @verbosity.setter
    def verbosity(self, verbosity):
    #***************************************************************************
        if not isinstance(verbosity, int):
            self.__verbosity = 0
        elif verbosity < 0:
            self.__verbosity = 0
        else:
            self.__verbosity = verbosity

        logger = logging.getLogger('awsremote')
        logger.setLevel(self.__LOG_LEVELS[self.__verbosity])
    
    def log(self, level, message):
    #***************************************************************************
        logger = logging.getLogger('awsremote')
        logger.log(self.__LOG_LEVELS[level], message)
        
        
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