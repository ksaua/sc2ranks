import sys

from distribute_setup import use_setuptools
use_setuptools()
from setuptools import setup

# Since json is only available since Python 2.6, we include it as dependency if
# we run on an older platform
pre26requirements = []
if sys.hexversion < 0x02060000:
    pre26requirements.append('simplejson')

setup(name='sc2ranks',
      version='0.3',
      py_modules=['sc2ranks'],
      install_requires = [] + pre26requirements
      )

