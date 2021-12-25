from setuptools import setup, find_packages

with open('README.md', 'r', encoding='utf-8') as read_me:
    long_description = read_me.read()

classifiers = [
    'Development Status :: 4 - Beta',

    'Programming Language :: Python :: 3',
    'Programming Language :: Python :: 3.6',
    'Programming Language :: Python :: 3.7',
    'Programming Language :: Python :: 3.8',
    'Programming Language :: Python :: 3.9',
    'Programming Language :: Python :: 3.10',

    'License :: OSI Approved :: MIT License',
    'Operating System :: OS Independent',

    'Topic :: Office/Business',
    'Topic :: Internet :: WWW/HTTP',
    'Topic :: Software Development :: Libraries :: Python Modules',
]

project_urls = {
    'Source': 'https://github.com/rajakodumuri/replicon-handler/',
    'Bug Tracker': 'https://github.com/rajakodumuri/replicon-handler/issues',
}

py_modules = [
    'replicon_handler'
]

setup(
    name='replicon_handler',
    version='1.1.7',

    author='Rajendra Kodumuri',
    author_email='rajakodumuri@gmail.com',

    description='Work with Replicon Web Services easily.',
    long_description=long_description,
    long_description_content_type='text/markdown',

    url='https://github.com/rajakodumuri/replicon-handler',
    project_urls=project_urls,
    classifiers=classifiers,

    keywords='replicon, webservices, api, gen3, polaris',

    py_modules=py_modules,
    package_dir={'': 'src'},
    packages=find_packages(where='src'),

    python_requires='>=3.6',
    install_requires=[
        'requests',
        'aiohttp'
    ],
)
