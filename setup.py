from setuptools import setup
from sphinx.setup_command import BuildDoc
from os import path
cmdclass = {'build_sphinx': BuildDoc}

# https://pypi.org/classifiers/

name = 'zoho_analytics_connector'
keywords = 'zoho analytics'
version = '0.5.0'
this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name=name,
    keywords=keywords,
    version=version,
    packages=['zoho_analytics_connector'],
    python_requires='>=3.6',
    install_requires=['requests',
                      ],
    setup_requires=['pytest-runner', 'wheel'],
    tests_require=["pytest", ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.7',
        'Topic :: Office/Business',
    ],
    url='https://github.com/timrichardson/zoho_analytics_connector',
    license='MIT',
    author='Tim Richardson',
    author_email='tim@growthpath.com.au',
    description='Zoho Analytics connector',
    long_description=long_description,
    long_description_content_type='text/markdown',
    cmdclass=cmdclass,
    # these are optional and override conf.py settings
    command_options={
        'build_sphinx': {
            'project': ('setup.py', name),
            'version': ('setup.py', version),
            'release': ('setup.py', version),
            'source_dir': ('setup.py', 'docs')}},

)
