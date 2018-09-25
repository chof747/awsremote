'''
Created on 23.09.2018

@author: chof
'''
from .config import Config 

import os
import boto3

class AWSRemote:
    
    def __init__(self, projectpath, verbosity):
    #***************************************************************************
        self.__config = Config(projectpath) 
        self.__config.verbosity = verbosity
        
    @property
    #***************************************************************************
    def config(self):
        return self.__config
    
    def __defaultEnv(self, environment, action):
    #***************************************************************************
        if environment =='':
            return 'systemtest'
        elif environment == 'production':
            self.__config.log(self.__config.ERROR, 
                "You cannot %s production - use EC2 console for that!" % action)
            exit(1)
        else:
            return environment

    def __getInstanceOfEnvironment(self, environment, fail=True):
    #***************************************************************************
        instanceId = self.__config.get('environments', environment)
        if (instanceId == None or instanceId == '') and fail:
            self.__config.log(self.__config.ERROR, 
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
    
    def __isStarted(self, environment, description = None):
        
        instanceId = self.__getInstanceOfEnvironment(environment, fail=False)
        if instanceId != None:
            return False
        else:
            return description['Reservations'][0]['Instances'][0]["State"]["Name"] != "running"
            
        
            
    def makeAmiImage(self, imageName, imageDescription):
    #***************************************************************************        
        instanceId = self.__config.get('environments', 'production')
        self.__config.log(self.__config.INFO,  
            "Image will be taken from the following running instance: %s" % instanceId)
        oldAmi = self.__config.get('configuration', 'test-image')
    
        client = boto3.client('ec2')
        
        if oldAmi != "":
            imageinfo = client.describe_images(
                ImageIds=[oldAmi]
            )
            self.__config.log(self.__config.INFO, "Old Image id - will be deleted: %s" % oldAmi)
            self.__config.log(self.__config.DEBUG, imageinfo['Images'])
            
            client.deregister_image(
                ImageId=oldAmi
            )
            
        response = client.create_image(
            Name=imageName,
            Description=imageDescription,
            InstanceId=instanceId
        )    
        self.__config.set('configuration', 'test-image', response['ImageId'])
        
        client.create_tags(
            Resources=[response['ImageId']],
            Tags=[{
               'Key' : 'Name',
               'Value' : imageDescription 
            }]
        )
        
        if oldAmi != "":
            client.delete_snapshot(
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
        client = boto3.client('ec2')
        response = client.run_instances(
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
        client.create_tags(
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
        client = boto3.client('ec2')

        #rename instance to indicate termination        
        client.create_tags(
            Resources=[instanceId],
            Tags=[{
               'Key' : 'Name',
               'Value' : self.__environmentName(environment, terminating=True)
            }])

        #make the volume deleted on termination
        client.modify_instance_attribute(
            InstanceId=instanceId,
            BlockDeviceMappings=[{
                'DeviceName': '/dev/sda1',
                'Ebs': {
                    'DeleteOnTermination': True,
                }
            }])
        
        self.__config.log(self.__config.INFO, 
            "Terminating instance %s for environment %s " % \
            (instanceId, environment))
        client.terminate_instances(InstanceIds=[instanceId])
        self.__config.set('environments', environment, '')
        
    def startInstance(self, environment):
        return ""
        
        
    def login(self, environment = '', user='ubuntu'):
    #***************************************************************************
        if environment == '':
            environment = 'systemtest'
            
        key = self.__config.get('configuration', 'key-file')
        instanceId = self.__getInstanceOfEnvironment(environment)
        
        self.__config.log(self.__config.DEBUG, "Using key file: %s" % key)
        self.__config.log(self.__config.INFO, 
            "Retreiving connection info for instance %s" % instanceId)

        client = boto3.client('ec2')
        
        response = client.describe_instances(InstanceIds=[instanceId])
        
        if not self.__isStarted(environment, response):
            self.__config.log(self.__config.INFO,
                "Instance %s is not running - starting ... " % instanceId)
            ip = self.startInstance(environment)
            exit(0)    
        elif (len(response['Reservations']) > 0):
            ip = response['Reservations'][0]['Instances'][0]['PublicIpAddress']
            self.__config.log(self.__config.INFO,
                "Connectiong to %s" % ip)
            os.system("ssh -i %s -t ubuntu@%s 'exec bash'" % (key, ip))
        else:
            self.__config.log(self.__config.ERROR, 
                "Instance %s not available" % instanceId)