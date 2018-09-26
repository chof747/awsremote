'''
Created on 23.09.2018

@author: chof
'''
from .config import Config 

import os
import boto3
from time import sleep

class AWSRemote:
    
    def __init__(self, projectpath, verbosity):
    #***************************************************************************
        self.__config = Config(projectpath) 
        self.__config.verbosity = verbosity
        self.__description = {}
        self.__client = boto3.client('ec2')
        
    def error(self, message):
    #***************************************************************************
        self.__log(self.__config.ERROR, message)
    
    def warn(self, message):
    #***************************************************************************
        self.__log(self.__config.ATTENTION, message)

    def info(self, message):
    #***************************************************************************
        self.__log(self.__config.INFO, message)

    def debug(self, message):
    #***************************************************************************
        self.__log(self.__config.DEBUG, message)

    def __log(self, level, message):
    #***************************************************************************
        self.__config.log(level, message)
        
    @property
    #***************************************************************************
    def config(self):
        return self.__config
    
    
    def description(self, environment, cache = True):
    #***************************************************************************
        if (not environment in self.__description) or not cache:
            instanceId = self.__getInstanceOfEnvironment(environment, False)
            if instanceId != None:
                self.__description[environment] = \
                    self.__client.describe_instances(InstanceIds=[instanceId])
            else:
                self.__description[environment] = None
                        
        return self.__description[environment]
    
    def __getIp(self, environment):
    #***************************************************************************
        description = self.description(environment, False)
        if (len(description['Reservations']) > 0):
            if 'PublicIpAddress' in description['Reservations'][0]['Instances'][0]:
                return description['Reservations'][0]['Instances'][0]['PublicIpAddress']
        return None

    def __defaultEnv(self, environment, action):
    #***************************************************************************
        if environment =='':
            return 'systemtest'
        elif environment == 'production':
            self.error( 
                "You cannot %s production - use EC2 console for that!" % action)
            exit(1)
        else:
            return environment

    def __getInstanceOfEnvironment(self, environment, fail=True):
    #***************************************************************************
        instanceId = self.__config.get('environments', environment)
        if (instanceId == None or instanceId == '') and fail:
            self.error( 
                "The environment %s is not available" % environment)
            exit(2)        
        elif instanceId == None or instanceId == '':
            return None
        else:
            return instanceId
    
    def __environmentName(self, environment, terminating = False):
    #***************************************************************************
        application = self.__config.get('configuration', 'application')
        if terminating:
            prefix = 'TERMINATING: '
        else:
            prefix = ''
            
        return "%s%s_%s" % (prefix, application, environment)
    
    def __isStarted(self, environment):
    #***************************************************************************        
        description = self.description(environment)
        if description != None:
            return description['Reservations'][0]['Instances'][0]["State"]["Name"] == "running"
        else:
            return False
            
        
            
    def makeAmiImage(self, imageName, imageDescription):
    #***************************************************************************        
        instanceId = self.__config.get('environments', 'production')
        self.info(  
            "Image will be taken from the following running instance: %s" % instanceId)
        oldAmi = self.__config.get('configuration', 'test-image')
    
        if oldAmi != "":
            imageinfo = self.__client.describe_images(
                ImageIds=[oldAmi]
            )
            self.info( "Old Image id - will be deleted: %s" % oldAmi)
            self.debug( imageinfo['Images'])
            
            self.__client.deregister_image(
                ImageId=oldAmi
            )
            
        response = self.__client.create_image(
            Name=imageName,
            Description=imageDescription,
            InstanceId=instanceId
        )    
        self.__config.set('configuration', 'test-image', response['ImageId'])
        
        self.__client.create_tags(
            Resources=[response['ImageId']],
            Tags=[{
               'Key' : 'Name',
               'Value' : imageDescription 
            }]
        )
        
        if oldAmi != "":
            self.__client.delete_snapshot(
                SnapshotId=imageinfo['Images'][0]['BlockDeviceMappings'][0]['Ebs']['SnapshotId'])
            
    def createInstanceFromAmi(self, environment='', replace = False, amiImage=''):
    #***************************************************************************
        environment = self.__defaultEnv(environment, "create new instance for")
        instanceId = self.__getInstanceOfEnvironment(environment, fail=False)
        
        if instanceId != None and not replace:
            self.__config.log(self.__config.ATTENTION, 
                "Instance %s exists for environment %s use replace option (-r, --replace) to replace it or terminate before" % \
                (instanceId, environment))
            exit(3)
        elif instanceId != None:
            self.terminateInstance(environment)

                    
        if amiImage == '':
            amiImage = self.__config.get('configuration', 'test-image')

        instanceName = self.__environmentName(environment)
        
        self.__config.log(self.config.INFO, "Creating instance from ami: %s" % amiImage)

        response = self.__client.run_instances(
            #DryRun=True,
            ImageId=amiImage,
            MaxCount=1,
            MinCount=1,
            LaunchTemplate={
                'LaunchTemplateName' : 'Money20_Systemtest',
                "Version": "5"
            })
        
        instanceId = response['Instances'][0]['InstanceId']      
        #set the name  
        self.__client.create_tags(
            Resources=[instanceId],
            Tags=[{
               'Key' : 'Name',
               'Value' : instanceName
            }])
        
        self.__config.set('environments', environment, instanceId) 
        
        self.__config.log(self.config.INFO, "Instance Id: %s created as %s" % \
                          (instanceId, instanceName))


    def terminateInstance(self, environment=''):
    #***************************************************************************
        environment = self.__defaultEnv(environment, "terminate")
        instanceId = self.__getInstanceOfEnvironment(environment)

        #rename instance to indicate termination        
        self.__client.create_tags(
            Resources=[instanceId],
            Tags=[{
               'Key' : 'Name',
               'Value' : self.__environmentName(environment, terminating=True)
            }])

        #make the volume deleted on termination
        self.__client.modify_instance_attribute(
            InstanceId=instanceId,
            BlockDeviceMappings=[{
                'DeviceName': '/dev/sda1',
                'Ebs': {
                    'DeleteOnTermination': True,
                }
            }])
        
        self.info( 
            "Terminating instance %s for environment %s " % \
            (instanceId, environment))
        self.__client.terminate_instances(InstanceIds=[instanceId])
        self.__config.set('environments', environment, '')
        
    def startInstance(self, environment):
    #***************************************************************************
        self.__client.start_instances(InstanceIds=[
            self.__getInstanceOfEnvironment(environment)]);
        
        ip = None
        while ip == None:
            sleep(5)
            ip = self.__getIp(environment)
            
        self.info('Instance for environment %s started. Public IP = %s' 
            % (environment, ip))
        return ip
    
    def stopInstance(self, environment):
        environment = self.__defaultEnv(environment, 'stop')
        self.__client.stop_instances(InstanceIds=[
            self.__getInstanceOfEnvironment(environment, True)
        ])
        
        
    def login(self, environment = '', user='ubuntu'):
    #***************************************************************************
        if environment == '':
            environment = 'systemtest'
            
        key = self.__config.get('configuration', 'key-file')
        instanceId = self.__getInstanceOfEnvironment(environment)
        
        self.debug( "Using key file: %s" % key)
        self.info( 
            "Retreiving connection info for instance %s" % instanceId)

        ip = self.__getIp(environment)
        
        if not self.__isStarted(environment):
            self.info(
                "Instance %s is not running - starting ... " % instanceId)
            ip = self.startInstance(environment)
            self.info('Wait 10sec for startup finalization ...')
            sleep(10)
                    
        if ip != None:
            self.info(
                "Connectiong to %s" % ip)
            os.system("ssh -i %s -t ubuntu@%s 'exec bash'" % (key, ip))
        else:
            self.error( 
                "Instance %s not available" % instanceId)