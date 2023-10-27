from setuptools import setup, find_packages

setup(
    name='ec_land_db',
    version='0.0.1',
    author='Ewan Pinnington',
    author_email='ewan.pinnington@ecmwf.int',
    description='Experimental processing for land surface data',
    packages=find_packages(),   
    install_requires=['pyyaml', 'black', 'isort', 'flake8'],
)