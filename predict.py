import json
import os
from module import ClassifierFactory


SHARED = os.environ.get('SHARED_ROOT')

def handler(event, context):
    mentor = '6109d2a86e6fa01e5bf3219f'
    question = 'how should we call you?'
    os.environ['CLASSIFIER_ARCH'] = 'module.arch.lr_transformer'
    result = (
            ClassifierFactory()
            .new_prediction(
                mentor=mentor, shared_root=SHARED, data_path='models'
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
