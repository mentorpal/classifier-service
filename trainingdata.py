import os
from module.api import fetch_training_data
from module.utils import append_cors_headers, append_secure_headers

SHARED = os.environ.get('SHARED_ROOT')


def handler(event, context):
    mentor = '6109d2a86e6fa01e5bf3219f'
    data = fetch_training_data(mentor)
    data_csv = data.to_csv(index=False)

    headers = {
        "Content-Disposition": f"attachment; filename={mentor}-trainingdata.csv",
        "Content-type": "text/csv",
    }
    append_cors_headers(headers, event)
    append_secure_headers(headers)
    response = {
        "statusCode": 200,
        "body": data_csv,
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
