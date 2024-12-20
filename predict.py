#
# This software is Copyright ©️ 2020 The University of Southern California. All Rights Reserved.
# Permission to use, copy, modify, and distribute this software and its documentation for educational, research and non-profit purposes, without fee, and without a written agreement is hereby granted, provided that the above copyright notice and subject to the full license file found in the root of this software deliverable. Permission to make commercial use of this software may be obtained by contacting:  USC Stevens Center for Innovation University of Southern California 1150 S. Olive Street, Suite 2300, Los Angeles, CA 90115, USA Email: accounting@stevens.usc.edu
#
# The full terms of this copyright and license should always be found in the root directory of this software deliverable as "license.txt" and if these terms are not found with this software, please contact the USC Stevens Center for the full license.
#
import json
import os
from typing import Dict
import boto3
import botocore
from module.logger import get_logger
from datetime import datetime
from module.classifier.dao import Dao
from module.utils import (
    load_sentry,
    append_cors_headers,
    append_secure_headers,
    require_env,
)

load_sentry()
log = get_logger("predict")
SHARED = os.environ.get("SHARED_ROOT")
log.info(f"shared: {SHARED}")
MODELS_BUCKET = require_env("MODELS_BUCKET")
log.info(f"bucket: {MODELS_BUCKET}")
s3 = boto3.client("s3")
MODELS_DIR = "/tmp/models"

classifier_dao = Dao(SHARED, MODELS_DIR)


def get_auth_headers(event) -> Dict[str, str]:
    return (
        {"Authorization": event["headers"]["Authorization"]}
        if "Authorization" in event["headers"]
        else {}
    )


def make_response(status, body, event):
    headers = {}
    append_cors_headers(headers, event)
    append_secure_headers(headers)
    response = {"statusCode": status, "body": json.dumps(body), "headers": headers}
    return response


def handler(event, context):
    log.debug(json.dumps(event))
    if "queryStringParameters" not in event:
        raise Exception("bad request")
    if (
        "mentor" not in event["queryStringParameters"]
        or "query" not in event["queryStringParameters"]
        or "chatsessionid" not in event["queryStringParameters"]
    ):
        raise Exception("bad request")
    mentor = event["queryStringParameters"]["mentor"]
    question = event["queryStringParameters"]["query"]
    chat_session_id = event["queryStringParameters"]["chatsessionid"]
    auth_headers = get_auth_headers(event)
    ping = (
        event["queryStringParameters"]["ping"]
        if "ping" in event["queryStringParameters"]
        else False
    )
    log.info(f"mentor: {mentor}, question: {question}")
    relative_path = os.path.join(
        mentor, "module.classifier.arch.lr_transformer", "model.pkl"
    )
    model_file = os.path.join(MODELS_DIR, relative_path)
    if os.path.exists(model_file):
        log.debug(f"model file exists {model_file}")
        modified_time = os.path.getmtime(model_file)
        utc_mod_time = datetime.utcfromtimestamp(modified_time)
        log.debug(f"model file modified at {utc_mod_time}")
        try:
            r = s3.get_object(
                Bucket=MODELS_BUCKET, Key=relative_path, IfModifiedSince=utc_mod_time
            )
            with open(model_file, "wb") as f:
                for chunk in r["Body"].iter_chunks(chunk_size=4096):
                    f.write(chunk)
            log.debug("model file updated")
        except botocore.exceptions.ClientError as e:
            if e.response["Error"]["Code"] != "304":
                log.error(e)
                raise e
            log.debug("model file not updated in s3 since last fetch")
    else:
        log.debug(f"fetching {model_file} from s3")
        os.makedirs(os.path.dirname(model_file), exist_ok=True)
        try:
            s3.download_file(MODELS_BUCKET, relative_path, model_file)
        except botocore.exceptions.ClientError as e:
            if e.response["Error"]["Code"] != "404":
                log.error(e)
                raise e
            body = {"message": f"No models found for mentor {mentor}."}
            return make_response(404, body, event)
        log.debug("model file download completed")

    if ping:
        # Just load the mentor and nothing else
        classifier_dao.find_classifier(mentor, auth_headers)
        body = {"message": f"Successful ping for mentor: {mentor}."}
        return make_response(200, body, event)

    result = classifier_dao.find_classifier(mentor, auth_headers).evaluate(
        question, chat_session_id
    )

    body = {
        "question": question,
        "answer_id": result.answer_id,
        "answer_text": result.answer_text,
        "answer_markdown_text": result.answer_markdown_text,
        "answer_media": result.answer_media,
        "external_video_ids": result.external_video_ids,
        "confidence": result.highest_confidence,
        "feedback_id": result.feedback_id,
        "classifier": "",
        "answer_missing": result.answer_missing,
    }
    response = make_response(200, body, event)
    return response


# # for local debugging:
# if __name__ == '__main__':
#     with open('__events__/predict-event.json.dist') as f:
#         event = json.loads(f.read())
#         handler(event, {}) # warmup
#         import cProfile
#         pr = cProfile.Profile()
#         pr.enable()
#         handler(event, {})
#         pr.disable()
#         pr.dump_stats('predict2.prof')
