# TODO

- [ ] separate set of requirements for api lambdas (if they could be made small)
- [ ] authentication & authorization
- [ ] sentry
- [ ] architecture diagram
- [ ] dns name for the api gateway plus base path mapping
- [ ] logging
- [ ] github repo
- [ ] remove panda from fetch_training_data and use csv
- [ ] monitoring & alerting on slow responses
- [ ] default gateway response 4xx 5xx
- [ ] train: validate request in api gateway
- [x] sample events and document how to invoke locally
- [x] api call -> status reporting
- [x] api call -> train job (upload res to s3)
- [x] api call -> answer/predict job (fetch trained model from s3)
- [x] jobs table ttl so we dont need to clean it up manually
- [blocked] implement full api set (blocked on followups / cookies)
- [x] monitoring & alerting (sqs dlq sends to slack, lambda to sentry)
- [x] infrastructure code
- [x] api gateway
- [x] LFS for /shared
- [x] CORS headers
- [x] secure headers


# Intro

This is a serverless service that can train mentors and answer questions:

![high l evel architecture](./classifier-service.drawio.png)

The code was generated using the `aws-python-docker` template from the [Serverless framework](https://www.serverless.com/).

For detailed instructions, please refer to the [documentation](https://www.serverless.com/framework/docs/providers/aws/).

## Deployment instructions

There's no cicd pipeline yet, it must be deployed manually

> **Requirements**: Docker. In order to build images locally and push them to ECR, you need to have Docker installed on your local machine. Please refer to [official documentation](https://docs.docker.com/get-docker/).
> **Requirements**: npm. Run once `npm ci` to get all the tools.

In order to deploy the service, run the following command:

```
sls deploy -s <stage>
# where stage is one of dev|qa|prod
```

# Monitoring

All lambdas use sentry to report issues. If processing fails, SQS will move messages to corresponding DLQ,
and there're alarms that monitor DLQs and send message to alerting topic (currently forwards to slack).


# Manual Testing

sls deploy builds a docker image: `<acc>.dkr.ecr.<region>.amazonaws.com/serverless-mentor-classifier-service-<stage>` which can be started and invoked locally:
```
docker run -e SHARED_ROOT=/app/shared -e GRAPHQL_ENDPOINT=https://v2.mentorpal.org/graphql -e API_SECRET=... --rm -p 9000:8080 <image_name>
curl -XPOST "http://localhost:9000/2015-03-31/functions/http_train/invocations" -d '{"mentor":"<id>"}'
```


After successful deployment, you can test the service remotely by using the following command:

```
sls invoke --function http_train -p <event payload>
```

To test the api via api gateway (dev is the stage):

```bash
curl https://g2x9qy4f86.execute-api.us-east-1.amazonaws.com/dev/train \
  --data-raw '{"mentor":"6109d2a86e6fa01e5bf3219f"}'
curl https://g2x9qy4f86.execute-api.us-east-1.amazonaws.com/dev/questions?mentor=6109d2a86e6fa01e5bf3219f&query=what+do+you+think+about+serverless
curl https://g2x9qy4f86.execute-api.us-east-1.amazonaws.com/dev/trainingdata/6109d2a86e6fa01e5bf3219f
curl https://g2x9qy4f86.execute-api.us-east-1.amazonaws.com/dev/train/status/5e09da8f-d8cc-4d19-80d8-d94b28741a58
```

## Asynchronous triggers

In order to run handlers for asynchronous event triggers locally, e.g. events fired by `SNS` or `SQS`, execute `sls invoke --local -f <function>`. To define a custom event payload, create a `*event.json` file and point to its path with `sls invoke --local -f <function> -p <path_to_event.json>`. Be sure to commit a `.dist` version of it for other developers to be used.

**Example**

```
predict.py -> handler to test
predict-event.json -> your local copy of event.json.dist, which is ignored by git
predict-event.json.dist -> reference event for other developers to be copied and used locally
```

## Debugging

To debug in VS Code, use this config:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: Current File",
      "type": "python",
      "request": "launch",
      "program": "${file}",
      "justMyCode": false,
      "env": {
        "GRAPHQL_ENDPOINT": "https://v2.mentorpal.org/graphql",
        "API_SECRET": "<redacted>",
        "AWS_REGION": "us-east-1",
        "SHARED_ROOT": "shared",
        "JOBS_TABLE_NAME": "classifier-jobs-dev",
      },
      "console": "integratedTerminal"
    }
  ]
}
```


# Resources

 - https://www.serverless.com/guides/aws-http-apis
 - https://www.serverless.com/framework/docs/providers/aws/guide/serverless.yml
 - https://www.serverless.com/framework/docs/providers/aws/events/apigateway
 - https://www.serverless.com/blog/container-support-for-lambda
 - https://dev.to/aws-builders/container-images-for-aws-lambda-with-python-286c
