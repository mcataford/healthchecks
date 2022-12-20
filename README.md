# Healthcheck service

The healthcheck service is a small Lambda-based backend that can receive healthcheck reports from services and serve
them in an easy-to-digest format for quick status page frontends. Data is kept in DynamoDB and has a 24h TTL so provide
a historical window into received statuses.

## Development

The development environment can be set up via `. script/bootstrap` -- this will install `tflint` for Terraform linting
needs, as well as a Python 3.9 venv with dev dependencies as defined in `setup.py`.

### Tests

You can run the test suite via `pytest --cov=src`.

## Deployment

The source code can be packed into a Lambda-ready archive via `. script/pack`, and the deployment can be triggered via
`ARCHIVE=./{name-of-your-zipped-source} ENV_NAME={environment-name} . script/deploy`. During the deployment, an API key
value that allows the service to authorize incoming checks needs to be submitted -- this key also need to be provided as
the `Authorization` header of any incoming POSTs.
