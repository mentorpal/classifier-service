##
## This software is Copyright ©️ 2020 The University of Southern California. All Rights Reserved.
## Permission to use, copy, modify, and distribute this software and its documentation for educational, research and non-profit purposes, without fee, and without a written agreement is hereby granted, provided that the above copyright notice and subject to the full license file found in the root of this software deliverable. Permission to make commercial use of this software may be obtained by contacting:  USC Stevens Center for Innovation University of Southern California 1150 S. Olive Street, Suite 2300, Los Angeles, CA 90115, USA Email: accounting@stevens.usc.edu
##
## The full terms of this copyright and license should always be found in the root directory of this software deliverable as "license.txt" and if these terms are not found with this software, please contact the USC Stevens Center for the full license.
##
import json
from module.api import fetch_training_data
from module.utils import is_authorized, create_json_response
from module.logger import get_logger

log = get_logger("training-data")


def handler(event, context):
    log.debug(json.dumps(event))
    mentor = event["pathParameters"]["mentor"]
    token = json.loads(event["requestContext"]["authorizer"]["token"])
    if not is_authorized(mentor, token):
        data = {
            "error": "not authorized",
            "message": "not authorized",
        }
        return create_json_response(401, data, event)

    log.info(f"fetching training data for {mentor}")

    data_csv = fetch_training_data(mentor)

    headers = {
        "Content-Disposition": f"attachment; filename={mentor}-trainingdata.csv",
        "Content-type": "text/csv",
    }
    return create_json_response(200, data_csv, event, headers)


# # for local debugging:
# if __name__ == '__main__':
#     with open('__events__/trainingdata-event.json.dist') as f:
#         event = json.loads(f.read())
#         handler(event, {})
