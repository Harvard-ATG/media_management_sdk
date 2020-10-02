# Image Media Manager SDK 

The Image Media Manager SDK provides a python interface to the [Image Media Manager API](https://github.com/harvard-atg/media_management_api).

## Getting Started

Install:

```
$ pip install git+https://github.com/Harvard-ATG/media_management_sdk@master#egg=media_management_sdk==0.1.0
```

Write code:

```python
from media_management_sdk import Client

# Your client ID and secret obtained from the Media Manager API /admin
client = Client(
    client_id='your_client_id',
    client_secret='your_client_secret',
    base_url='http://localhost:8000/api',
)

# Authenticate with API and obtain a temporary access token
client.authenticate(user_id='your_sis_user_id')

# Perform API actions
response = client.api.search_courses('Medieval Media')
print(response)
```

## Development

Install development dependencies:

```
$ pip install -r requirements-dev.txt
```

Run unit tests:

```
$ pytest tests/unit
```

Run unit tests against multiple python environments:

```
$ tox
$ tox -e py38
```

Run functional tests against the API (no mocking - actual API calls):

```
$ export MEDIA_MANAGEMENT_API_ID=media_management_sdk
$ export MEDIA_MANAGEMENT_API_SECRET=secret_for_test
$ export MEDIA_MANAGEMENT_API_URL=https://myinstance.domain/api 
$ export MEDIA_MANAGEMENT_API_USER_ID=test_user_id
$ pytest tests/functional
```

_Note: In order to run the functional tests, you must first register an _Application_ with the API in order to obtain client credentials, and then configure those details using environment variables as shown above. It's recommended to use a non-production instance._

Generate and preview docs locally:

```
$ cd docs
$ make html
$ python3 -mhttp.server --bind 127.0.0.1 8080
$ open http://127.0.0.1:8080
```
