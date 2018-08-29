from boto3 import ec2
from .config import Config 

import os
import sys
import boto3


def makeAmiImage(projectpath, imageName, imageDescription):
    
    config = Config(projectpath)
    instanceId = config.get('environments', 'production')
    oldAmi = config.get('configuration', 'test-image')

    client = boto3.client('ec2')
    
    if oldAmi != "":
        imageinfo = client.describe_images(
            ImageIds=[oldAmi]
        )
        print(oldAmi)
        print(imageinfo['Images'])
        
        client.deregister_image(
            ImageId=oldAmi
        )
        
    response = client.create_image(
        Name=imageName,
        Description=imageDescription,
        InstanceId=instanceId
    )    
    config.set('configuration', 'test-image', response['ImageId'])
    
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
        
