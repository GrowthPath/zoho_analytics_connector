from setuptools import setup
from os import path

# https://pypi.org/classifiers/
name = 'zoho_analytics_connector'
keywords = 'zoho analytics'
version = '1.5.0'
this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name=name,
    keywords=keywords,
    version=version,
    packages=['zoho_analytics_connector'],
    python_requires='>=3.9',
    install_requires=['requests', 'emoji'],
    setup_requires=['pytest-runner', 'wheel'],  # Removed sphinx from setup_requires
    tests_require=["pytest"],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Topic :: Office/Business',
    ],
    url='https://github.com/timrichardson/zoho_analytics_connector',
    license='MPL-2.0',
    author='Tim Richardson',
    author_email='tim@growthpath.com.au',
    description='Zoho Analytics connector',
    long_description=long_description,
    long_description_content_type='text/markdown',
)
