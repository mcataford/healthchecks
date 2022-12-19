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
    http_method = event["requestContext"]["httpMethod"]

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

    logger.exception(
        "Handler does not accept HTTP method %s", event["requestContext"]["httpMethod"]
    )
    return {"statusCode": 400}
