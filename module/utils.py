# This software is Copyright ©️ 2020 The University of Southern California. All Rights Reserved.
# Permission to use, copy, modify, and distribute this software and its documentation for educational, research and non-profit purposes, without fee, and without a written agreement is hereby granted, provided that the above copyright notice and subject to the full license file found in the root of this software deliverable. Permission to make commercial use of this software may be obtained by contacting:  USC Stevens Center for Innovation University of Southern California 1150 S. Olive Street, Suite 2300, Los Angeles, CA 90115, USA Email: accounting@stevens.usc.edu
#
# The full terms of this copyright and license should always be found in the root directory of this software deliverable as "license.txt" and if these terms are not found with this software, please contact the USC Stevens Center for the full license.
#
#

import json
from module.logger import get_logger
from os import _Environ, environ
from typing import Any, Dict, Union, List
from pathlib import Path
import queue
from threading import Thread
import requests
from dataclasses import dataclass
import logging

log = get_logger()
SBERT_ENDPOINT = environ.get("SBERT_ENDPOINT")
GRAPHQL_ENDPOINT = environ.get("GRAPHQL_ENDPOINT")
API_SECRET = environ.get("API_SECRET")
SECRET_HEADER_NAME = environ.get("SECRET_HEADER_NAME")
SECRET_HEADER_VALUE = environ.get("SECRET_HEADER_VALUE")


def load_sentry():
    if environ.get("IS_SENTRY_ENABLED", "") == "true":
        log.info("SENTRY enabled, calling init")
        import sentry_sdk  # NOQA E402
        from sentry_sdk.integrations.aws_lambda import AwsLambdaIntegration  # NOQA E402

        sentry_sdk.init(
            dsn=environ.get("SENTRY_DSN_MENTOR_CLASSIFIER"),
            # include project so issues can be filtered in sentry:
            environment=environ.get("PYTHON_ENV"),
            integrations=[AwsLambdaIntegration(timeout_warning=True)],
            # Set traces_sample_rate to 1.0 to capture 100%
            # of transactions for performance monitoring.
            traces_sample_rate=0.20,
            debug=environ.get("SENTRY_DEBUG_CLASSIFIER", "") == "true",
        )


def is_authorized(mentor, token):
    return (
        token["role"] == "CONTENT_MANAGER"
        or token["role"] == "SUPER_CONTENT_MANAGER"
        or token["role"] == "ADMIN"
        or token["role"] == "SUPER_CONTENT_MANAGER"
        or token["role"] == "SUPER_ADMIN"
        or mentor in token["mentorIds"]
    )


def create_json_response(status, data, event, headers={}):
    body = {"data": data}
    append_cors_headers(headers, event)
    append_secure_headers(headers)
    response = {"statusCode": status, "body": json.dumps(body), "headers": headers}
    return response


def require_env(n: str) -> str:
    env_val = environ.get(n, "")
    if not env_val:
        raise EnvironmentError(f"missing required env var {n}")
    return env_val


def append_secure_headers(headers):
    secure = {
        "content-security-policy": "upgrade-insecure-requests;",
        "referrer-policy": "no-referrer-when-downgrade",
        "strict-transport-security": "max-age=31536000",
        "x-content-type-options": "nosniff",
        "x-frame-options": "SAMEORIGIN",
        "x-xss-protection": "1; mode=block",
    }
    for h in secure:
        headers[h] = secure[h]


def append_cors_headers(headers, event):
    origin = environ.get("CORS_ORIGIN", "*")
    # TODO specify allowed list of origins and if event["headers"]["origin"] is one of them then allow it
    # if "origin" in event["headers"] and getenv.array('CORS_ORIGIN').includes(event["headers"]["origin"]):
    #     origin = event["headers"]["origin"]

    headers["Access-Control-Allow-Origin"] = origin
    headers["Access-Control-Allow-Origin"] = "*"
    headers["Access-Control-Allow-Headers"] = "GET,PUT,POST,DELETE,OPTIONS"
    headers["Access-Control-Allow-Methods"] = (
        "Authorization,Origin,Accept,Accept-Language,Content-Language,Content-Type"
    )


def use_average_embedding() -> bool:
    return props_to_bool("AVERAGE_EMBEDDING", environ)


def use_semantic_deduplication() -> bool:
    return props_to_bool("SEMANTIC_DEDUP", environ)


def extract_alphanumeric(input_string: str) -> str:
    from string import ascii_letters, digits, whitespace

    return "".join(
        [ch for ch in input_string if ch in (ascii_letters + digits + whitespace)]
    )


def get_shared_root() -> str:
    return environ.get("SHARED_ROOT") or "shared"


def file_last_updated_at(file_path: str) -> int:
    return int(Path(file_path).stat().st_mtime)


def normalize_strings(strings: List[str]) -> List[str]:
    ret = []
    for string in strings:
        string = sanitize_string(string)
        ret.append(string)
    return ret


def sanitize_string(input_string: str) -> str:
    input_string = input_string.strip()
    input_string = input_string.casefold()
    input_string = input_string.replace("\u00a0", " ")
    input_string = extract_alphanumeric(input_string)
    return input_string


def props_to_bool(
    name: str, props: Union[Dict[str, Any], _Environ], dft: bool = False
) -> bool:
    if not (props and name in props):
        return dft
    v = props[name]
    return str(v).lower() in ["1", "t", "true"]


@dataclass
class SbertCosSimReq:
    answers_text: str
    entity_text: str


def thread_sbert_cos_reqs(req: List[SbertCosSimReq], no_workers):
    class Worker(Thread):
        def __init__(self, request_queue):
            Thread.__init__(self)
            self.queue = request_queue
            self.results = []

        def run(self):
            while True:
                content = self.queue.get()
                if content == "":
                    break
                headers = {
                    "Authorization": f"Bearer {API_SECRET}",
                    f"{SECRET_HEADER_NAME}": f"{SECRET_HEADER_VALUE}",
                }
                res = requests.post(
                    f"{SBERT_ENDPOINT}/encode/cos_sim_weight",
                    json={"a": content.answers_text, "b": content.entity_text},
                    headers=headers,
                )
                res.raise_for_status()
                logging.debug(res.json())
                self.results.append(
                    {
                        "entity_text": content.entity_text,
                        "cos_sim_weight": res.json()["cos_sim_weight"],
                    }
                )
                self.queue.task_done()

    # Create queue and add req params
    q = queue.Queue()
    for r in req:
        q.put(r)

    # Workers keep working till they receive an empty string
    for _ in range(no_workers):
        q.put("")

    # Create workers and add to the queue
    workers = []
    for _ in range(no_workers):
        worker = Worker(q)
        worker.start()
        workers.append(worker)
    # Join workers to wait till they finished
    for worker in workers:
        worker.join()

    # Combine results from all workers
    r = []
    for worker in workers:
        r.extend(worker.results)

    # convert list into dict
    dict = {
        key: value
        for (key, value) in list(
            map(lambda result: (result["entity_text"], result["cos_sim_weight"]), r)
        )
    }
    return dict
