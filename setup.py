from setuptools import setup
from sphinx.setup_command import BuildDoc

cmdclass = {'build_sphinx': BuildDoc}

# https://pypi.org/classifiers/

name = 'zoho_analytics_connector'
keywords = 'zoho analytics'
version = '0.3.0'

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
        'Topic :: Text Processing :: Linguistic',
    ],
    url='https://github.com/timrichardson/zoho_analytics_connector',
    license='MIT',
    author='Tim Richardson',
    author_email='tim@growthpath.com.au',
    description='Zoho Analytics connector',
    long_description="Python 3-friendly wrapper for Zoho Analytics API (formely Zoho Reports), (using AuthToken and with untested oAuth2 support)",
    cmdclass=cmdclass,
    # these are optional and override conf.py settings
    command_options={
        'build_sphinx': {
            'project': ('setup.py', name),
            'version': ('setup.py', version),
            'release': ('setup.py', version),
            'source_dir': ('setup.py', 'docs')}},

)
