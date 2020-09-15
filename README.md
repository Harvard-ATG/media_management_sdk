# Image Media Manager SDK 

The Image Media Manager SDK provides a python interface to the [Image Media Manager API](https://github.com/harvard-atg/media_management_api).

## Getting Started

```python
from media_management_sdk import Client

# Your client ID and secret obtained from the Media Manager API /admin
client = Client(
    client_id='your_client_id',
    client_secret='your_client_secret',
    base_url='http://localhost:8000/api',
)
client.obtain_token(user_id='your_sis_user_id')
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
$ pytest                  # invoke pytest directly
$ python3 -m pytest tests  # alternative way of invoking pytest
```

Run tests against multiple python environments:

```
$ tox
$ tox -e py38
```

Generate and preview docs locally:

```
$ cd docs
$ make html
$ python3 -mhttp.server --bind 127.0.0.1 8080
$ open http://127.0.0.1:8080
```
