# TODO

- implement full api set
- infrastructure code (s3 buckets, api gateway)
- api call -> train jobs (plus status reporting)
- LFS for /shared
- CORS headers
- secure headers
- authentication & authorization
- dns name for the api gateway plus base path mapping
- sentry
- remove panda from fetch_training_data and use csv
- separate set of requirements for api lambdas (if they could be made small)
- logging
- monitoring
- alerting

# Serverless - AWS Python Docker

This project has been generated using the `aws-python-docker` template from the [Serverless framework](https://www.serverless.com/).

For detailed instructions, please refer to the [documentation](https://www.serverless.com/framework/docs/providers/aws/).

## Deployment instructions

> **Requirements**: Docker. In order to build images locally and push them to ECR, you need to have Docker installed on your local machine. Please refer to [official documentation](https://docs.docker.com/get-docker/).

In order to deploy your service, run the following command

```
sls deploy -s dev
```

## Testing locally

sls deploy builds a docker image: `<acc>.dkr.ecr.<region>.amazonaws.com/serverless-mentor-classifier-service-<stage>` which can be started and invoked locally:
```
docker run -e SHARED_ROOT=/app/shared -e GRAPHQL_ENDPOINT=https://v2.mentorpal.org/graphql -e API_SECRET=... --rm -p 9000:8080 <image_name>
curl -XPOST "http://localhost:9000/2015-03-31/functions/function/invocations" -d '{"param1":"parameter 1 value"}'
```

## Test your service

After successful deployment, you can test the service remotely by using the following command:

```
sls invoke --function train-mentor
```

# Resources

 - https://www.serverless.com/blog/container-support-for-lambda
 - https://dev.to/aws-builders/container-images-for-aws-lambda-with-python-286c
 - https://www.serverless.com/framework/docs/providers/aws/guide/serverless.yml