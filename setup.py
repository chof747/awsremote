'''
Created on 09. Okt. 2016

@author: chof
'''

from setuptools import setup
import os

packageDescription = ''

with open('README.rst', 'r') as f:
    packageDescription += f.read()

setup(name             = 'awsremote',
      version          = '0.1.0',
      author           = 'Christian Hofbauer',
      author_email     = 'chof@gmx.at',
      description      = 'A python tool and package that keeps track of ' +
                         'AWS EC2 instances for a web application.',
      long_description = packageDescription,
      license          = 'New BSD License',
      packages         = ['awsremote'],
      package_dir      = { '' : 'src' },
      package_data     = { 'awsremote' : ['data/templates/*.json']},
      setup_requires = [ 'boto3 >= 1.8'], 
      install_requires = [ 'boto3 >= 1.8'], 
      scripts=['src/aws_remote.py'] )