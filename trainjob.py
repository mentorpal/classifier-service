##
## This software is Copyright ©️ 2020 The University of Southern California. All Rights Reserved. 
## Permission to use, copy, modify, and distribute this software and its documentation for educational, research and non-profit purposes, without fee, and without a written agreement is hereby granted, provided that the above copyright notice and subject to the full license file found in the root of this software deliverable. Permission to make commercial use of this software may be obtained by contacting:  USC Stevens Center for Innovation University of Southern California 1150 S. Olive Street, Suite 2300, Los Angeles, CA 90115, USA Email: accounting@stevens.usc.edu
##
## The full terms of this copyright and license should always be found in the root directory of this software deliverable as "license.txt" and if these terms are not found with this software, please contact the USC Stevens Center for the full license.
##
import json
import os
import boto3
import datetime
from module import ClassifierFactory
from module.utils import require_env

shared = os.environ.get("SHARED_ROOT")
JOBS_TABLE_NAME = require_env("JOBS_TABLE_NAME")
MODELS_BUCKET = require_env('MODELS_BUCKET')
s3 = boto3.client("s3")
dynamodb = boto3.resource("dynamodb")
job_table = dynamodb.Table(JOBS_TABLE_NAME)
MODELS_DIR='/tmp/models'

def handler(event, context):
    print(json.dumps(event))
    for record in event["Records"]:
        request = json.loads(str(record["body"]))
        mentor = request["mentor"]
        update_status(request["id"], "IN_PROGRESS")
        try:
            classifier = ClassifierFactory()
            training = classifier.new_training(
                mentor=mentor,
                shared_root=shared,
                data_path=MODELS_DIR,
                arch="module.arch.lr_transformer",
            )
            training.train(shared)
            s3.upload_file(
                os.path.join(MODELS_DIR, mentor, 'module.arch.lr_transformer', 'model.pkl'),
                MODELS_BUCKET,
                os.path.join(mentor, 'module.arch.lr_transformer', 'model.pkl'),
            )
            update_status(request["id"], "DONE")
        except Exception as e:
            print(e)
            update_status(request["id"], "FAILED")


def update_status(id, status):
    job_table.update_item(
        Key={"id": id},
        # status is reserved, workaround according to:
        # https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Expressions.ExpressionAttributeNames.html
        UpdateExpression="set #status = :s, updated = :u",
        ExpressionAttributeNames={
            '#status': 'status',
        },
        ExpressionAttributeValues={
            ":s": status,
            ":u": datetime.datetime.now().isoformat(),
        },
    )


# # for local debugging:
# if __name__ == '__main__':
#     handler({}, {})
# if __name__ == '__main__':
#     with open('__events__/trainjob-event.json.dist') as f:
#         event = json.loads(f.read())
#         handler(event, {})