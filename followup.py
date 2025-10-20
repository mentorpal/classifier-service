#
# This software is Copyright ©️ 2020 The University of Southern California. All Rights Reserved.
# Permission to use, copy, modify, and distribute this software and its documentation for educational, research and non-profit purposes, without fee, and without a written agreement is hereby granted, provided that the above copyright notice and subject to the full license file found in the root of this software deliverable. Permission to make commercial use of this software may be obtained by contacting:  USC Stevens Center for Innovation University of Southern California 1150 S. Olive Street, Suite 2300, Los Angeles, CA 90115, USA Email: accounting@stevens.usc.edu
#
# The full terms of this copyright and license should always be found in the root directory of this software deliverable as "license.txt" and if these terms are not found with this software, please contact the USC Stevens Center for the full license.
#
import json
from typing import Dict
from module.utils import create_json_response, load_sentry
from module.logger import get_logger
from module.followup_api import generate_followups
from train import get_auth_headers
load_sentry()
log = get_logger("followup")


def handler(event, context):
    log.debug(json.dumps(event))
    category = event["pathParameters"]["category"]
    mentor = event["pathParameters"]["mentor"]
    data = generate_followups(
        category,
        mentor,
        headers=get_auth_headers(event),
    )
    questions = [
        {
            "question": question.question,
            "entityType": question.entity,
            "template": question.template,
        }
        for question in data
    ]

    return create_json_response(200, {"followups": questions}, event)


# # for local debugging, must add valid jwt token to auth manually
# if __name__ == "__main__":
#     with open("__events__/followups-event.json.dist") as f:
#         event = json.loads(f.read())
#         handler(event, {})
