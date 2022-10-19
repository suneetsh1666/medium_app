from setuptools import setup, find_packages

with open('requirements.txt') as f:
	install_requires = f.read().strip().split('\n')

# get version from __version__ variable in medium_app/__init__.py
from medium_app import __version__ as version

setup(
	name='medium_app',
	version=version,
	description='meduim.com',
	author='hitesh',
	author_email='Hitesh@korecent.com',
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
