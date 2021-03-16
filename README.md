# Open API
A collection of useful tools powered by Open API schema

# Installation
Install Python 3.9 (other versions may be compatible)

Clone this repository
```bash
git clone https://github.com/specify/open-api
cd open-api
```

Configure a virtual environment
```bash
python -m venv venv
```

Install the dependencies
```bash
./venv/bin/pip install -r requirements.txt
```

# Config
Put your OpenAPI schema into `config/open_api.yaml`

# Testing API

## (Optional) Define parameter constrains
If response object depends on the query parameters, you can
test for these relationships by adding your parameter names
and handler function to the `parameter_constraints` dictionary
in `src/validate/parameter_constraints.py`.

Each handler function would receive the following arguments:
* parameter_value (bool): the value of the parameter this handler
  works with
* path (str): name of the current endpoint (useful if the same
  parameter is shared between multiple endpoints)
* response (any): full response object

The handler function should return a boolean value saying validating
whether the response object is as expected

## Run the test

Run the test
```bash
./venv/bin/python -m src.test.full_test
```
This script would automatically generate test URLs based on
your API schema.

All requests would be sent to the first server
specified in the `servers` part of the API schema.

# Generating API documentation
Run the flask web server
```bash
FLASK_APP=src.frontend.server ./venv/bin/python -m flask run
```

The web server is now available at http://127.0.0.1:5000/

For production, use a production WSGI server -
https://flask.palletsprojects.com/en/1.1.x/tutorial/deploy/#run-with-a-production-server

API Requests sent from this webserver are also going through validation
of both the request URL and the response object. All validation errors
are saved into the `logs` directory
