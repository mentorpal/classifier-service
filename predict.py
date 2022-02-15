##
## This software is Copyright ©️ 2020 The University of Southern California. All Rights Reserved. 
## Permission to use, copy, modify, and distribute this software and its documentation for educational, research and non-profit purposes, without fee, and without a written agreement is hereby granted, provided that the above copyright notice and subject to the full license file found in the root of this software deliverable. Permission to make commercial use of this software may be obtained by contacting:  USC Stevens Center for Innovation University of Southern California 1150 S. Olive Street, Suite 2300, Los Angeles, CA 90115, USA Email: accounting@stevens.usc.edu
##
## The full terms of this copyright and license should always be found in the root directory of this software deliverable as "license.txt" and if these terms are not found with this software, please contact the USC Stevens Center for the full license.
##
import json
import os
import boto3
from module import ClassifierFactory, mentor_model_path
from module.utils import append_cors_headers, append_secure_headers, require_env

SHARED = os.environ.get('SHARED_ROOT')
os.environ['CLASSIFIER_ARCH'] = 'module.arch.lr_transformer'
MODELS_BUCKET = require_env('MODELS_BUCKET')
s3 = boto3.client("s3")
MODELS_DIR='/tmp/models'

def handler(event, context):
    print(json.dumps(event))
    if "queryStringParameters" not in event:
       raise Exception("bad request")
    if "mentor" not in event['queryStringParameters'] or "query" not in event['queryStringParameters']:
        raise Exception("bad request")
    mentor = event['queryStringParameters']["mentor"]
    question = event['queryStringParameters']["query"]

    # todo cache models
    relative_path = os.path.join(mentor, 'module.arch.lr_transformer', 'model.pkl')
    model_file = os.path.join(MODELS_DIR, relative_path)
    os.makedirs(os.path.dirname(model_file), exist_ok = True)
    s3.download_file(MODELS_BUCKET, relative_path, model_file)

    result = (
            ClassifierFactory()
            .new_prediction(
                mentor=mentor, shared_root=SHARED, data_path=MODELS_DIR
            )
            .evaluate(question=question,shared_root=SHARED)
        )
    body = {
        "question": question,
        "answer_id": result.answer_id,
        "answer_text": result.answer_text,
        "answer_media": result.answer_media,
        "confidence": result.highest_confidence,
        "feedback_id": result.feedback_id,
        "classifier": "",
    }
    headers = {}
    append_cors_headers(headers, event)
    append_secure_headers(headers)
    response = {
        "statusCode": 200,
        "body": json.dumps(body),
        "headers": headers
    }

    return response



# # for local debugging:
# if __name__ == '__main__':
#     handler({}, {})
# if __name__ == '__main__':
#     with open('__events__/transcribe-collect-event.json.dist') as f:
#         event = json.loads(f.read())
#         handler(event, {})
