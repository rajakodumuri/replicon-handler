# Handler for Replicon Web Services

[![Downloads](https://pepy.tech/badge/replicon-handler/month)](https://pepy.tech/project/replicon-handler)
[![Changelog v1.1.7 badge][changelog-badge]][changelog]
[![Supported Versions](https://img.shields.io/pypi/pyversions/replicon-handler.svg)](https://pypi.org/project/replicon-handler)
[![Contributors](https://img.shields.io/github/contributors/rajakodumuri/replicon-handler.svg)](https://github.com/rajakodumuri/replicon-handler/graphs/contributors)
[![Publish Replicon Handler](https://github.com/rajakodumuri/replicon-handler/actions/workflows/python-package-publish.yml/badge.svg)](https://github.com/rajakodumuri/replicon-handler/actions/workflows/python-package-publish.yml)

Replicon-Handler is built in [Python](https://www.python.org/) and is maintained by [Rajendra Kodumuri](https://www.github.com/rajakodumuri). Interactions with Replicon WebServices are made possible, using the [requests](https://docs.python-requests.org/en/latest/) library.

Repetitive white noise, so to speak, can be avoided; Making working with the Replicon WebServices a breeze. [Click here](https://www.github.com/rajakodumuri/replicon-handler#support-features) for more details.

```python
from replicon_handler import RepliconHandler

replicon = RepliconHandler(
    company_key='company_key',
    username=None,
    password=None,
    authentication_token='',
    method='post',
    headers=headers,
    log_file=r'log_path\log_file.log'
)

headers['Content-Type'] = 'application/json'
headers['X-Replicon-Application'] = 'CompanyKey_OperationName_Version'
headers['Authorization'] = f'Bearer {replicon.authentication_token}'
```

## Installing Replicon Handler

Replicon Handler is distributed via PyPI, installing it is as simple as:

```bash
> pip install -U replicon-handler
```

## User Guide available on [Read the Docs](https://replicon-handler.readthedocs.io).

[![Read the Docs](https://raw.githubusercontent.com/rajakodumuri/replicon-handler/main/extras/documentation.png)](https://replicon-handler.readthedocs.io)

## Supported Features

Generation of Replicon tenant details and API URLs highlighted below, can be eliminated, to make working with the Replicon WebServices a breeze.
- Finding the Slug.
- Finding the Swimlane.
- Generating URLs for:
    - Analytics API.
    - User Audit Log API.
    - Web Service End Points.
```python
get_all_users = replicon.web_service('UserService1.svc', 'GetAllUsers')

payload = {}
all_users = replicon.connection_handler(get_all_users, payload)
```
- Retries requests that failed due to connections failures.
- Handles component call limitations of the Replicon Gen3 API.
- Availability of concurrent threaded and asynchronous request handlers, out of the box.
```python
get_user_details = replicon.web_service('UserService1.svc', 'GetUser2')

payloads = [{'userUri':user['uri']} for user in all_users]
all_users_details = replicon.threaded_handler(get_user_details, payloads, 5)
```
