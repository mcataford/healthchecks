import typing
import json

import pytest
import moto
import boto3
import boto3.dynamodb.conditions as ddb_conditions

import tests.mock_data as mock_data


@pytest.fixture(name="call_handler")
def fixture_call_handler():
    """Lambda handler with mocked DDB"""
    with moto.mock_dynamodb():
        # pylint: disable=import-outside-toplevel
        from src.base import handler as lambda_handler

        client = boto3.client("dynamodb", region_name="us-east-1")
        client.create_table(
            AttributeDefinitions=[
                {"AttributeName": "event_id", "AttributeType": "S"},
                {"AttributeName": "service_name", "AttributeType": "S"},
            ],
            TableName="healthchecks",
            KeySchema=[
                {"AttributeName": "event_id", "KeyType": "HASH"},
                {"AttributeName": "service_name", "KeyType": "RANGE"},
            ],
            ProvisionedThroughput={
                "ReadCapacityUnits": 5,
                "WriteCapacityUnits": 5,
            },
        )

        yield lambda_handler

        client.delete_table(TableName="healthchecks")


@pytest.fixture(name="get_mock_event")
def fixture_get_mock_event():
    def _get_mock_event(*, body: typing.Any, method: str):

        return {
            **mock_data.SAMPLE_EVENT,
            "body": body,
            "httpMethod": method,
            "requestContext": {
                **mock_data.SAMPLE_EVENT["requestContext"],
                "httpMethod": method,
            },
        }

    return _get_mock_event


@pytest.fixture(name="get_mock_context")
def fixture_get_mock_context():
    def _get_mock_context():
        return {}

    return _get_mock_context


# POST: healthcheck reception


def test_400s_on_non_json_request_body(get_mock_event, get_mock_context, call_handler):
    """The handler only accepts JSON payloads."""

    event = get_mock_event(body="totally-not-json", method="POST")
    context = get_mock_context()

    response = call_handler(event, context)

    assert response["statusCode"] == 400


@pytest.mark.parametrize("method", ["HEAD", "PATCH", "PUT"])
def test_400s_on_method_other_than_get_or_post(
    method, get_mock_event, get_mock_context, call_handler
):
    """Only GET and POST methods are allowed."""

    event = get_mock_event(body=json.dumps({"service_name": "test"}), method=method)
    context = get_mock_context()

    response = call_handler(event, context)

    assert response["statusCode"] == 400


def test_201s_on_valid_post_request_body(
    get_mock_event, get_mock_context, call_handler
):
    """The handler 201s on success."""
    event = get_mock_event(
        body=json.dumps({"service_name": "test", "checks": []}), method="POST"
    )
    context = get_mock_context()

    response = call_handler(event, context)

    assert response["statusCode"] == 201


def test_creates_dynamodb_record_on_valid_post_request(
    get_mock_event, get_mock_context, call_handler
):
    """The handler writes to DynamoDB on successful requests."""
    table = boto3.resource("dynamodb", region_name="us-east-1").Table("healthchecks")

    event = get_mock_event(
        body=json.dumps({"service_name": "test", "checks": []}), method="POST"
    )
    context = get_mock_context()

    query = table.scan(FilterExpression=ddb_conditions.Attr("service_name").eq("test"))
    assert query["Count"] == 0

    call_handler(event, context)

    query = table.scan(FilterExpression=ddb_conditions.Attr("service_name").eq("test"))

    assert query["Count"] == 1


# GET: Serving healthcheck queries


def test_200s_on_valid_get_request(get_mock_event, get_mock_context, call_handler):
    """The handler returns 200 for valid fetches"""
    event = get_mock_event(body="", method="GET")
    context = get_mock_context()

    response = call_handler(event, context)

    assert response["statusCode"] == 200


def test_returns_entries_by_services_on_get(
    get_mock_event, get_mock_context, call_handler
):
    """The handler returns a collection of healthchecks keyed by service"""

    # Create the checks/
    post_event_1 = get_mock_event(
        body=json.dumps({"service_name": "test-one", "checks": []}), method="POST"
    )
    post_event_2 = get_mock_event(
        body=json.dumps({"service_name": "test-two", "checks": []}), method="POST"
    )
    post_context = get_mock_context()

    post_response = call_handler(post_event_1, post_context)
    post_response = call_handler(post_event_2, post_context)
    assert post_response["statusCode"] == 201

    # Retrieve the checks.
    event = get_mock_event(body="", method="GET")
    context = get_mock_context()

    response = call_handler(event, context)

    response_body = json.loads(response["body"])

    assert len(response_body) == 2
