'''
Created on 27.08.2018

@author: chof
'''
import boto3
import json
from awsremote import AWSRemote


'''
if __name__ == '__main__':
    ec2 = boto3.resource('ec2')
    for instance in ec2.instances.all():
        print(instance)   
    pass

if __name__ == '__main__':
    ec2 = boto3.resource('ec2')
    instance = ec2.create_instances(
        LaunchTemplate = {
            "LaunchTemplateName":"Money20_Systemtest",
            "Version": "5"},
        ImageId="ami-038d7340c9ba7cc99",
        MaxCount=1,
        MinCount=1
    )
    print(instance)
    pass
with open('../data/configuration_template.json') as f:
    parameters = json.load(f, encoding="utf-8")
    print(parameters)

config = Config('/tmp')
config.set('environments', 'production', 'test')

client = boto3.client('ec2')

response = client.describe_images(
    ImageIds=["ami-034583eb8c4ae3fe2"]
)
#print(response['Images'][0]['BlockDeviceMappings'][0])
snapshot = response['Images'][0]['BlockDeviceMappings'][0]['Ebs']['SnapshotId']
response = client.delete_snapshot(
    SnapshotId = snapshot,
    DryRun=True)
print(response)
'''

awsremote = AWSRemote('/Users/chof/Documents/projects/money20/development/', 2)
config = awsremote.config
config.log(config.INFO, "test")

