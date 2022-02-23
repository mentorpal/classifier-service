##
## This software is Copyright ©️ 2020 The University of Southern California. All Rights Reserved.
## Permission to use, copy, modify, and distribute this software and its documentation for educational, research and non-profit purposes, without fee, and without a written agreement is hereby granted, provided that the above copyright notice and subject to the full license file found in the root of this software deliverable. Permission to make commercial use of this software may be obtained by contacting:  USC Stevens Center for Innovation University of Southern California 1150 S. Olive Street, Suite 2300, Los Angeles, CA 90115, USA Email: accounting@stevens.usc.edu
##
## The full terms of this copyright and license should always be found in the root directory of this software deliverable as "license.txt" and if these terms are not found with this software, please contact the USC Stevens Center for the full license.
##
import json
import boto3
from module.utils import append_cors_headers, append_secure_headers, require_env
from module.logger import get_logger

log = get_logger("status")

JOBS_TABLE_NAME = require_env("JOBS_TABLE_NAME")
log.info(f"using table {JOBS_TABLE_NAME}")
dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
job_table = dynamodb.Table(JOBS_TABLE_NAME)


def handler(event, context):
    log.debug(json.dumps(event))
    status_id = event["pathParameters"]["id"]
    token = json.loads(event["requestContext"]["authorizer"]["token"])

    response = job_table.get_item(Key={"id": status_id})
    log.debug(response)
    if "Item" in response:
        item = response["Item"]
        is_authorized = (
            token["role"] == "CONTENT_MANAGER"
            or token["role"] == "ADMIN"
            or item["mentor"] in token["mentorIds"]
        )
        if not is_authorized:
            status = 401
            data = {
                "error": "not authorized",
                "message": "not authorized",
            }
        else:
            status = 200
            data = {
                "id": item["id"],
                "status": item["status"],
                "updated": item["updated"],
                "mentor": item["mentor"],
                "statusUrl": f"/status/{status_id}",
            }
    else:
        data = {
            "error": "not found",
            "message": f"{status_id} not found",
        }
        status = 400

    body = {"data": data}
    headers = {}
    append_cors_headers(headers, event)
    append_secure_headers(headers)
    dynamo_msg = {"statusCode": status, "body": json.dumps(body), "headers": headers}

    return dynamo_msg


# # for local debugging:
# if __name__ == '__main__':
#     with open('__events__/status-event.json.dist') as f:
#         event = json.loads(f.read())
#         handler(event, {})
