import json
import os
from module import ClassifierFactory

def handler(event, context):
    mentor = '6109d2a86e6fa01e5bf3219f'
    shared = os.environ.get('SHARED_ROOT')
    result = (
            ClassifierFactory()
            .new_training(
                mentor=mentor, shared_root=shared, data_path='models', arch='module.arch.lr_transformer'
            )
            .train(shared)
        )
    body = {
        "message": f"{mentor} trained, accuracy: {result.accuracy}",
    }

    response = {
        "statusCode": 200,
        "body": json.dumps(body)
    }

    return response



# # for local debugging:
# if __name__ == '__main__':
#     handler({}, {})
# if __name__ == '__main__':
#     with open('__events__/transcribe-collect-event.json.dist') as f:
#         event = json.loads(f.read())
#         handler(event, {})
