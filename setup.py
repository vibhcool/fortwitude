# -- coding: utf-8
from setuptools import setup
import os

def readme():
    with open('README.md') as f:
        return f.read()
    
setup(name = "fortwitude",
      version="0.1",
      description="Fortune cookies with Twitter",
      long_dscription = readme(),
      author="Anand B Pillai",
      license="BSD 3.0",
      author_email="anandpillai@letterboxes.org",
      url="https://github.com/pythonhacker/fortwitude",
      packages = ['fortwitude'],
      scripts = ['scripts/fortwitude','scripts/fortitude'],
      install_requires = ['twitter'],
      data_files=[(os.path.expanduser('~/.fortwitude_en'), ['data/1lncn10.txt'])])
