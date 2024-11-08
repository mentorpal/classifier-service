# This software is Copyright ©️ 2020 The University of Southern California. All Rights Reserved.
# Permission to use, copy, modify, and distribute this software and its documentation for educational, research and non-profit purposes, without fee, and without a written agreement is hereby granted, provided that the above copyright notice and subject to the full license file found in the root of this software deliverable. Permission to make commercial use of this software may be obtained by contacting:  USC Stevens Center for Innovation University of Southern California 1150 S. Olive Street, Suite 2300, Los Angeles, CA 90115, USA Email: accounting@stevens.usc.edu
#
# The full terms of this copyright and license should always be found in the root directory of this software deliverable as "license.txt" and if these terms are not found with this software, please contact the USC Stevens Center for the full license.
#
#
import json
import os
import csv
from io import StringIO
import requests
from timeit import default_timer as timer
from datetime import timedelta
from typing import Dict, List, TypedDict, Tuple
from .types import AnswerInfo
import logging

OFF_TOPIC_THRESHOLD_DEFAULT = -0.631
# SBERT_ENDPOINT = os.environ.get("SBERT_ENDPOINT")
# GRAPHQL_ENDPOINT = os.environ.get("GRAPHQL_ENDPOINT")
API_SECRET = os.environ.get("API_SECRET")
SECRET_HEADER_NAME = os.environ.get("SECRET_HEADER_NAME")
SECRET_HEADER_VALUE = os.environ.get("SECRET_HEADER_VALUE")


class GQLQueryBody(TypedDict):
    query: str
    variables: dict


def get_off_topic_threshold() -> float:
    try:
        return (
            float(str(os.environ.get("OFF_TOPIC_THRESHOLD") or ""))
            if "OFF_TOPIC_THRESHOLD" in os.environ
            else OFF_TOPIC_THRESHOLD_DEFAULT
        )
    except ValueError:
        return OFF_TOPIC_THRESHOLD_DEFAULT


def sbert_encode(question: str):
    headers = {
        "Authorization": f"Bearer {API_SECRET}",
        f"{SECRET_HEADER_NAME}": f"{SECRET_HEADER_VALUE}",
    }
    start = timer()
    res = requests.get(
        f"{os.environ.get('SBERT_ENDPOINT')}/encode",
        params={"query": question},
        headers=headers,
    )
    end = timer()
    logging.info("sbert encode execution time: %s", timedelta(seconds=end - start))
    res.raise_for_status()
    return res.json()


def sbert_cos_sim_weight(a: str, b: str) -> float:
    headers = {
        "Authorization": f"Bearer {API_SECRET}",
        f"{SECRET_HEADER_NAME}": f"{SECRET_HEADER_VALUE}",
    }
    start = timer()
    res = requests.post(
        f"{os.environ.get('SBERT_ENDPOINT')}/encode/cos_sim_weight",
        json={"a": a, "b": b},
        headers=headers,
    )
    end = timer()
    logging.info("sbert cos weight execution time: %s", timedelta(seconds=end - start))
    res.raise_for_status()
    logging.debug(res.json())
    return res.json()["cos_sim_weight"]


def sbert_paraphrase(sentences: list) -> float:
    headers = {
        "Authorization": f"Bearer {API_SECRET}",
        f"{SECRET_HEADER_NAME}": f"{SECRET_HEADER_VALUE}",
    }
    start = timer()
    res = requests.post(
        f"{os.environ.get('SBERT_ENDPOINT')}/paraphrase",
        json={"sentences": sentences},
        headers=headers,
    )
    end = timer()
    logging.info("sbert paraphrase execution time: %s", timedelta(seconds=end - start))
    res.raise_for_status()
    logging.debug(res.json())
    return res.json()["pairs"]


GQL_QUERY_MENTOR = """
query Mentor($id: ID!) {
    mentor(id: $id) {
        mentorType
        subjects {
            name
        }
        topics {
            name
        }
        questions {
            question {
                _id
            }
            topics {
                name
            }
        }
        answers {
            _id
            status
            transcript
            markdownTranscript
            question {
                _id
                question
                type
                name
                paraphrases
            }
            webMedia {
                type
                tag
                url
                transparentVideoUrl
            }
            mobileMedia {
                type
                tag
                url
                transparentVideoUrl
            }
            vttMedia {
                type
                tag
                url
            }
            externalVideoIds{
                wistiaId
            }
        }
        orphanedCompleteAnswers {
            _id
            status
            transcript
            markdownTranscript
            question {
                _id
                question
                type
                name
                paraphrases
            }
            webMedia {
                type
                tag
                url
                transparentVideoUrl
            }
            mobileMedia {
                type
                tag
                url
                transparentVideoUrl
            }
            vttMedia {
                type
                tag
                url
            }
            externalVideoIds{
                wistiaId
            }
        }
    }
}
"""

GQL_UPDATE_MENTOR_TRAINING = """
mutation UpdateMentorTraining($id: ID!) {
    updateMentorTraining(id: $id) {
        _id
    }
}
"""
GQL_CREATE_USER_QUESTION = """
mutation UserQuestionCreate($userQuestion: UserQuestionCreateInput!) {
    userQuestionCreate(userQuestion: $userQuestion) {
        _id
    }
}
"""

GQL_CATEGORY_ANSWERS = """
query CategoryAnswers($category: String!, $mentor: ID!) {
    categoryAnswers(category: $category, mentor: $mentor) {
        answerText
        questionText
    }
}
"""

GQL_ADD_OR_UPDATE_TRAIN_TASK = """
mutation TrainTaskAdd($taskDocId: ID!, $mentorId: ID!, $status: String!) {
          me{
            mentorTrainTaskAddOrUpdate(taskDocId: $taskDocId, mentorId: $mentorId, status: $status) {
              _id
              mentor
              status
            }
          }
      }
"""

GQL_QUERY_MENTOR_ANSWERS_AND_NAME = """
query Mentor($id: ID!){
        mentor(id: $id) {
            name
            answers {
                question {
                    question
                }
                transcript
            }
        }
} """

GQL_QUERY_GRADED_USER_QUESTIONS = """
query GradedUserQuestions($filter: Object!){
  userQuestions(filter:$filter, limit: 9999){
    edges{
      node{
        question
        graderAnswer{
            _id
            status
            transcript
            markdownTranscript
            externalVideoIds{
                wistiaId
            }
            webMedia {
                type
                tag
                url
                transparentVideoUrl
            }
            mobileMedia {
                type
                tag
                url
                transparentVideoUrl
            }
            vttMedia {
                type
                tag
                url
            }
            question{
            _id
            question
            type
            name
            paraphrases
            }
        }
      }
    }
  }
} """

GQL_QUERY_USER_CAN_EDIT_MENTOR = """
query MentorCanEdit($mentor: ID!){
        mentorCanEdit(mentor: $mentor)
} """


def __auth_gql(query: GQLQueryBody, headers: Dict[str, str] = {}) -> dict:
    final_headers = {**headers, f"{SECRET_HEADER_NAME}": f"{SECRET_HEADER_VALUE}"}
    # SSL is not valid for alb so have to turn off validation
    res = requests.post(
        os.environ.get("GRAPHQL_ENDPOINT"), json=query, headers=final_headers
    )
    res.raise_for_status()
    return res.json()


def query_mentor(mentor: str) -> GQLQueryBody:
    return {"query": GQL_QUERY_MENTOR, "variables": {"id": mentor}}


def query_mentor_answers_and_name(mentor: str) -> GQLQueryBody:
    return {"query": GQL_QUERY_MENTOR_ANSWERS_AND_NAME, "variables": {"id": mentor}}


def query_mentor_graded_user_questions(mentor: str) -> GQLQueryBody:
    return {
        "query": GQL_QUERY_GRADED_USER_QUESTIONS,
        "variables": {
            "filter": {"$and": [{"graderAnswer": {"$ne": None}}, {"mentor": mentor}]}
        },
    }


def query_category_answers(category: str, mentor: str) -> GQLQueryBody:
    return {
        "query": GQL_CATEGORY_ANSWERS,
        "variables": {"category": category, "mentor": mentor},
    }


def mutation_update_training(mentor: str) -> GQLQueryBody:
    return {"query": GQL_UPDATE_MENTOR_TRAINING, "variables": {"id": mentor}}


def query_user_can_edit_mentor(mentor: str) -> GQLQueryBody:
    return {"query": GQL_QUERY_USER_CAN_EDIT_MENTOR, "variables": {"mentor": mentor}}


def mutation_create_user_question(
    mentor: str,
    question: str,
    answer_id: str,
    chat_session_id: str,
    answer_type: str,
    confidence: float,
) -> GQLQueryBody:
    return {
        "query": GQL_CREATE_USER_QUESTION,
        "variables": {
            "userQuestion": {
                "mentor": mentor,
                "question": question,
                "classifierAnswer": answer_id,
                "classifierAnswerType": answer_type,
                "confidence": float(confidence),
                "chatSessionId": chat_session_id,
            }
        },
    }


def fetch_training_data(mentor: str):
    data = fetch_mentor_data(mentor)
    data_dict = {}
    data_list = []
    answers = data.get("answers", [])
    already_complete_answers = data.get("orphanedCompleteAnswers", [])
    all_answers = [*answers, *already_complete_answers]
    for answer in all_answers:
        question = answer["question"]
        q = {
            "id": question["_id"],
            "question_text": question["question"],
            "paraphrases": question["paraphrases"],
            "answer": answer["transcript"],
            "markdownAnswer": answer["markdownTranscript"],
            "answer_id": answer["_id"],
            "answer_media": {
                "web_media": answer.get("webMedia"),
                "mobile_media": answer.get("mobileMedia"),
                "vtt_media": answer.get("vttMedia"),
            },
            "external_video_ids": answer["externalVideoIds"],
            "topics": [],
        }
        data_dict[question["_id"]] = q

    for question in data.get("questions", []):
        dict_question = data_dict.get(question["question"]["_id"], None)
        if dict_question is not None:
            for topic in question["topics"]:
                data_dict[dict_question["id"]]["topics"].append(topic["name"])
    for key in data_dict:
        question = data_dict[key]
        topics = question["topics"]
        topic_str = "|".join(topics)
        current_question = question["question_text"]
        paraphrases = question["paraphrases"]
        paraphrase_str = "|".join(paraphrases)
        answer = question["answer"]
        answer_id = key
        data_list.append(
            [answer_id, current_question, paraphrase_str, answer, topic_str]
        )

    data_csv = StringIO()
    csv_writer = csv.writer(data_csv, lineterminator="\n")
    csv_writer.writerow(["id", "question", "paraphrases", "answer", "topic"])
    csv_writer.writerows(data_list)

    return data_csv.getvalue()


def user_can_edit_mentor(mentor: str, headers: Dict[str, str] = {}) -> bool:
    tdjson = __auth_gql(query_user_can_edit_mentor(mentor), headers=headers)
    return tdjson.get("data")["mentorCanEdit"]


def fetch_mentor_data(mentor: str, headers: Dict[str, str] = {}) -> dict:
    tdjson = __auth_gql(query_mentor(mentor), headers)
    if "errors" in tdjson:
        raise Exception(json.dumps(tdjson.get("errors")))
    # print(tdjson, flush=True)
    data = tdjson["data"]["mentor"]
    return data


def fetch_mentor_answers_and_name(
    mentor: str, headers: Dict[str, str] = {}
) -> Tuple[List[AnswerInfo], str]:
    tdjson = __auth_gql(query_mentor_answers_and_name(mentor), headers=headers)
    if "errors" in tdjson:
        raise Exception(json.dumps(tdjson.get("errors")))
    data = tdjson["data"]["mentor"]
    all_answered = [
        AnswerInfo(answer["question"]["question"], answer["transcript"])
        for answer in data.get("answers", [])
    ]
    name = data["name"]
    return all_answered, name


def fetch_mentor_graded_user_questions(
    mentor: str, headers: Dict[str, str] = {}
) -> list:
    try:
        tdjson = __auth_gql(query_mentor_graded_user_questions(mentor), headers=headers)
        if "errors" in tdjson:
            raise Exception(json.dumps(tdjson.get("errors")))
        edges = tdjson["data"]["userQuestions"]["edges"]
        nodes = list(map(lambda edge: edge["node"], edges))
        valid_nodes = list(
            filter(
                lambda node: "question" in node
                and node["question"] is not None
                and "graderAnswer" in node
                and node["graderAnswer"] is not None,
                nodes,
            )
        )
        return valid_nodes
    except Exception as e:
        logging.error(e)
        return []


def fetch_category(category: str, mentor: str, headers: Dict[str, str] = {}) -> dict:
    tdjson = __auth_gql(query_category_answers(category, mentor), headers=headers)
    return tdjson.get("data") or {}


def update_training(mentor: str):
    tdjson = __auth_gql(mutation_update_training(mentor))
    if "errors" in tdjson:
        raise Exception(json.dumps(tdjson.get("errors")))


def mutation_add_or_update_train_task(
    task_id: str, mentor: str, status: str
) -> GQLQueryBody:
    return {
        "query": GQL_ADD_OR_UPDATE_TRAIN_TASK,
        "variables": {"taskDocId": task_id, "mentorId": mentor, "status": status},
    }


def add_or_update_train_task(
    task_id: str, mentor: str, status: str, headers: Dict[str, str] = {}
):
    tdjson = __auth_gql(
        mutation_add_or_update_train_task(task_id, mentor, status), headers=headers
    )
    if "errors" in tdjson:
        raise Exception(json.dumps(tdjson.get("errors")))
    data = tdjson.get("data")
    return data["me"]["mentorTrainTaskAddOrUpdate"]["_id"]


def create_user_question(
    mentor: str,
    question: str,
    answer_id: str,
    chat_session_id: str,
    answer_type: str,
    confidence: float,
) -> str:
    tdjson = __auth_gql(
        mutation_create_user_question(
            mentor, question, answer_id, chat_session_id, answer_type, confidence
        )
    )
    if "errors" in tdjson:
        raise Exception(json.dumps(tdjson.get("errors")))
    try:
        return tdjson["data"]["userQuestionCreate"]["_id"]
    except KeyError:
        return "error"
