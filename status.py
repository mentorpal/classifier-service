#
# This software is Copyright ©️ 2020 The University of Southern California. All Rights Reserved.
# Permission to use, copy, modify, and distribute this software and its documentation for educational, research and non-profit purposes, without fee, and without a written agreement is hereby granted, provided that the above copyright notice and subject to the full license file found in the root of this software deliverable. Permission to make commercial use of this software may be obtained by contacting:  USC Stevens Center for Innovation University of Southern California 1150 S. Olive Street, Suite 2300, Los Angeles, CA 90115, USA Email: accounting@stevens.usc.edu
#
# The full terms of this copyright and license should always be found in the root directory of this software deliverable as "license.txt" and if these terms are not found with this software, please contact the USC Stevens Center for the full license.
#
import json
import boto3
import os
from module.api import user_can_edit_mentor
from module.ttl_cache import TTLCache
from module.utils import load_sentry, create_json_response, require_env
from module.logger import get_logger
from train import get_auth_headers

load_sentry()
log = get_logger("status")
JOBS_TABLE_NAME = require_env("JOBS_TABLE_NAME")
log.info(f"using table {JOBS_TABLE_NAME}")
aws_region = os.environ.get("REGION", "us-east-1")
dynamodb = boto3.resource("dynamodb", region_name=aws_region)
job_table = dynamodb.Table(JOBS_TABLE_NAME)


def get_requesting_user_id(event):
    token = json.loads(event["requestContext"]["authorizer"]["token"])
    return token["id"]


cached_user_can_edit_mentor = TTLCache()


def get_user_can_edit_mentor(mentor, user_id, auth_headers):
    user_can_edit_mentor_result = cached_user_can_edit_mentor.get((mentor, user_id))
    if not user_can_edit_mentor_result:
        user_can_edit_mentor_result = user_can_edit_mentor(mentor, auth_headers)
        cached_user_can_edit_mentor.set((mentor, user_id), user_can_edit_mentor_result)
    return user_can_edit_mentor_result


def handler(event, context):
    log.debug(json.dumps(event))
    status_id = event["pathParameters"]["id"]
    auth_headers = get_auth_headers(event)
    db_item = job_table.get_item(Key={"id": status_id})
    log.debug(db_item)
    if "Item" in db_item:
        item = db_item["Item"]
        user_id = get_requesting_user_id(event)
        if not user_id:
            return create_json_response(
                401,
                {
                    "error": "not authorized, no user id",
                    "message": "not authorized, no user id",
                },
                event,
            )
        user_can_edit_mentor_result = get_user_can_edit_mentor(
            item["mentor"], user_id, auth_headers
        )
        if not user_can_edit_mentor_result:
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
                "state": item["status"],
                "mentor": item["mentor"],
                # only added after trainjob runs
                **({"updated": item["updated"]} if "updated" in item else {}),
                "statusUrl": f"/status/{status_id}",
            }
    else:
        data = {
            "error": "not found",
            "message": f"{status_id} not found",
        }
        status = 400

    return create_json_response(status, data, event)


# # for local debugging:
# if __name__ == '__main__':
#     with open('__events__/status-event.json.dist') as f:
#         event = json.loads(f.read())
#         handler(event, {})
