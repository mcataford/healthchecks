#!/usr/bin/env python

"""
Healthcheck lambda handler

The healthcheck API serves two purposes: receive healthcheck requests
from registered services and commit them to DynamoDB, and retrieve the
latest healthchecks available by service when asked.
"""

import logging
import json
import typing
import datetime

import boto3

logger = logging.getLogger(__name__)

ddb_table = boto3.resource("dynamodb", region_name="us-east-1").Table("healthchecks")


class Response(typing.TypedDict):
    """Partial representation of the response format returned by the handler"""

    status_code: int


class HealthcheckEntry(typing.TypedDict):
    """
    Represents a single check reported by the service. A request
    pushing healthcheck statuses can push as many checks as it needs
    to report on different metrics.
    """

    name: str
    success: bool
    metric: float


class HealthcheckRecord(typing.TypedDict):
    """Represents the healthcheck data that services can send."""

    service_name: str
    event_id: str
    event_timestamp: str
    check_data: typing.List[HealthcheckEntry]
    ttl: int


def handler(event, *args, **kwargs) -> Response:
    """
    Entrypoint to the API.

    A GET will return a collection of all available healthcheck records
    for all services that reported in (up to the TTL, 24 hours). The
    returned map of checks is keyed by service name and the structure of the
    payload is documented in HealthcheckRecord.

    ```
    GET /

    200 OK {
        "services": {
            {service-name}: {HealthcheckRecord for service-name}
            ...
        }
    }
    ```

    A POST will submit a healthcheck entry to the tracker. If valid, this results
    in a row being added to the DynamoDB table that tracks healthchecks and returns
    a 201.

    ```
    POST /

    201 CREATED {}
    ```

    Any invalid payload (i.e. non-json request body for POST requests or HTTP verbs
    other than GET/POST) will result in a 400.
    """

    http_method: str = event["requestContext"]["httpMethod"]

    # Creating a healthcheck record
    #
    # This flow requires a valid json payload that describes the
    # healthcheck entry (see HealthcheckRecord for structure) and
    # writes a new entry with TTL (24h) to DynamoDB.

    if http_method == "POST":
        try:
            request_body = json.loads(event["body"])
        except:
            logger.exception(
                "Failed to deserialize request body, expected JSON",
                extra={"body": event["body"]},
            )
            return {"statusCode": 400}

        healthcheck: HealthcheckRecord = {
            "service_name": request_body["service_name"],
            "event_id": event["requestContext"]["requestId"],
            "event_timestamp": str(datetime.datetime.utcnow()),
            "checks": request_body["checks"],
            "ttl": int(
                (
                    datetime.datetime.utcnow() + datetime.timedelta(seconds=30)
                ).timestamp()
            ),
        }

        ddb_table.put_item(Item=healthcheck)

        return {"statusCode": 201}

    # Retrieving healthcheck records
    #
    # This flow scans the DynamoDB table and returns a collection of
    # healthcheck records keyed by service-name representing all available
    # data. Because data is TTL'ed at 24 hours, anything beyond that point
    # should be disregarded since it should have been marked for deletion
    # in AWS.

    if http_method == "GET":
        entries = ddb_table.scan()

        checks_map = {}

        for item in entries["Items"]:
            service_name = item["service_name"]

            if service_name not in checks_map:
                checks_map[service_name] = []

            checks_map[service_name].append(
                {
                    "checks": item["checks"],
                    "timestamp": item["event_timestamp"],
                }
            )

        return {"statusCode": 200, "body": json.dumps(checks_map)}

    # Catch-all for any invalid requests
    #
    # Any request using a verb other than GET/POST is ignored and results in
    # a 400.

    logger.exception(
        "Handler does not accept HTTP method %s", event["requestContext"]["httpMethod"]
    )
    return {"statusCode": 400}
