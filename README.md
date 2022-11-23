# lambda-boilerplate
🛠 Skip the boilerplate and start building fun λ things 🛠

![Lambda Boilerplate](https://github.com/mcataford/lambda-boilerplate/workflows/Lambda%20Boilerplate/badge.svg)

## Overview

AWS Lambdas are fun, but often the amount of boilerplate involved in getting a project off the ground hinders the fun. From setting up a local environment to writing out infrastructure templates, the overhead of Lambda-based greenfield projects can be daunting. No more. Just use this repository as a template or clone it and jump straight into the action! This repository offers a quick template your can use, full with a Docker setup for local development and invocation commands that you can use to package and deploy Lambda-based apps.

## Local development

The base Lambda handler is at `src/base.py` and all the Terraform configuration files are in `infrastructure`.

[Read more about Terraform](https://www.terraform.io/docs/index.html)

[Read more about AWS Lambda](https://docs.aws.amazon.com/lambda/latest/dg/lambda-python.html)

### Tooling

All the tooling is implemented using the [One Script to Rule Them
All](https://github.com/github/scripts-to-rule-them-all) paradigm and can be found under `script`.

## Deployment

Provided your runtime source code is prepackages and ready to go, you can simply `ARCHIVE=<path-to-function-zip> . script/deploy` to deploy your function in seconds!

By default, the resources are identified with an environment name `dev-$USER`, but you can change this in staging /
production deployments by specifying the `ENV_NAME` environment variable.

Individual parts of the application (i.e. the bootstrap resources or the application itself) can be deployed separately
using `PROJECT=<bootstrap|app> script/apply`.

Prepackaging the source code depends on what language is used as a runtime, more details can be found in [AWS Lambda
documentation](https://docs.aws.amazon.com/lambda/latest/dg/gettingstarted-package.html).

## Contributing

Got suggestions or improvements you'd like to make? Open a PR or [an issue](https://github.com/mcataford/lambda-boilerplate/issues)!

Feature requests should keep in mind that the goal of this boilerplate is to be general enough so that the cost of tailoring it to specific use cases is low.
