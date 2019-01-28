from setuptools import setup
import os
from sphinx.setup_command import BuildDoc
cmdclass = {'build_sphinx': BuildDoc}

# https://pypi.org/classifiers/

name='zoho_analytics_connector'
keywords='zoho crm'
version='0.1.0'


setup(
        name=name,
        keywords=keywords,
        version=version,
        packages=['zoho_crm_connector'],
        python_requires='>=3.6',
        install_requires=['requests',
            ],
        setup_requires=["pytest-runner",],
        tests_require=["pytest",],
        classifiers=[
            'Development Status :: 3 - Alpha',
            'License :: OSI Approved :: MIT License',
            'Programming Language :: Python :: 3.7',
            'Topic :: Text Processing :: Linguistic',
            ],
        url='https://github.com/timrichardson/zoho_analytics_connector',
        license='GPL v3',
        author='Tim Richardson',
        author_email='tim@growthpath.com.au',
        description='Zoho Analytics connector',
        cmdclass=cmdclass,
        # these are optional and override conf.py settings
        command_options={
            'build_sphinx': {
                'project': ('setup.py', name),
                'version': ('setup.py', version),
                'release': ('setup.py', version),
                'source_dir': ('setup.py', 'docs')}},

        )
