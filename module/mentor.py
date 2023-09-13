# This software is Copyright ©️ 2020 The University of Southern California. All Rights Reserved.
# Permission to use, copy, modify, and distribute this software and its documentation for educational, research and non-profit purposes, without fee, and without a written agreement is hereby granted, provided that the above copyright notice and subject to the full license file found in the root of this software deliverable. Permission to make commercial use of this software may be obtained by contacting:  USC Stevens Center for Innovation University of Southern California 1150 S. Olive Street, Suite 2300, Los Angeles, CA 90115, USA Email: accounting@stevens.usc.edu
#
# The full terms of this copyright and license should always be found in the root directory of this software deliverable as "license.txt" and if these terms are not found with this software, please contact the USC Stevens Center for the full license.
#
#
from dataclasses import dataclass

from module.api import fetch_mentor_data, fetch_mentor_graded_user_questions
from module.utils import sanitize_string
from typing import Dict


@dataclass
class Media:
    type: str
    tag: str
    url: str
    transparentVideoUrl: str = ""


class Mentor(object):
    def __init__(self, id, auth_headers: Dict[str, str] = {}):
        self.id = id
        self.topics = []
        self.utterances_by_type = {}
        self.questions_by_id = {}
        self.questions_by_text = {}
        self.questions_by_answer = {}
        self.answer_id_by_answer = {}
        self.load(auth_headers)

    def load(self, auth_headers):
        data = fetch_mentor_data(self.id, auth_headers)
        for subject in data.get("subjects", []):
            self.topics.append(subject["name"])
        for topic in data.get("topics", []):
            self.topics.append(topic["name"])
        answers = data.get("answers", [])
        already_complete_answers = data.get("orphanedCompleteAnswers", [])
        all_answers = [*answers, *already_complete_answers]
        for answer in all_answers:
            question = answer["question"]
            if answer["status"] in ["INCOMPLETE", "SKIP"]:
                continue
            if answer["status"] == "NONE":
                mentorType = data.get("mentorType", "VIDEO")
                if mentorType == "VIDEO":
                    if (
                        not (answer["transcript"] or question["name"] == "_IDLE_")
                        or not answer["webMedia"]
                        or not answer["mobileMedia"]
                        or not answer["webMedia"].get("url", "")
                        or not answer["mobileMedia"].get("url", "")
                    ):
                        continue
                else:
                    if not answer["transcript"]:
                        continue
            answer_media = {
                "web_media": answer.get("webMedia"),
                "mobile_media": answer.get("mobileMedia"),
                "vtt_media": answer.get("vttMedia"),
            }
            if question["type"] == "UTTERANCE":
                if question["name"] not in self.utterances_by_type:
                    self.utterances_by_type[question["name"]] = []
                utterance_data = [
                    answer["_id"],
                    answer["transcript"],
                    answer["markdownTranscript"],
                    answer_media,
                    answer["externalVideoIds"],
                ]
                self.utterances_by_type[question["name"]].append(utterance_data)
                continue
            q = {
                "id": question["_id"],
                "question_text": question["question"],
                "paraphrases": question["paraphrases"],
                "answer": answer["transcript"],
                "markdown_answer": answer["markdownTranscript"],
                "answer_id": answer["_id"],
                "answer_media": answer_media,
                "external_video_ids": answer["externalVideoIds"],
                "topics": [],
            }
            self.answer_id_by_answer[answer["_id"]] = {
                "transcript": answer["transcript"],
                "markdownTranscript": answer["markdownTranscript"],
            }
            self.questions_by_id[question["_id"]] = q
        # First add primary question texts
        questions = data.get("questions", [])
        questions_from_already_complete_answers = list(
            map(
                lambda x: {
                    "question": {
                        "_id": x["question"]["_id"],
                    },
                    "topics": [],
                },
                already_complete_answers,
            )
        )
        for question in [*questions, *questions_from_already_complete_answers]:
            q = self.questions_by_id.get(question["question"]["_id"], None)
            if q is not None:
                for topic in question["topics"]:
                    self.questions_by_id[q["id"]]["topics"].append(topic["name"])
                self.questions_by_text[sanitize_string(q["question_text"])] = q
                self.questions_by_answer[sanitize_string(q["answer"])] = q
                for paraphrase in q["paraphrases"]:
                    sanitized_paraphrase = sanitize_string(paraphrase)
                    if sanitized_paraphrase not in self.questions_by_text:
                        self.questions_by_text[sanitized_paraphrase] = q
        user_question_nodes = fetch_mentor_graded_user_questions(self.id)
        for user_question in user_question_nodes:
            question_asked = user_question["question"]
            target_answer_doc = user_question["graderAnswer"]
            target_question_doc = target_answer_doc["question"]
            answer_media = {
                "web_media": target_answer_doc.get("webMedia", None),
                "mobile_media": target_answer_doc.get("mobileMedia", None),
                "vtt_media": target_answer_doc.get("vttMedia", None),
            }
            external_video_ids = target_answer_doc["externalVideoIds"]
            q = {
                "id": target_question_doc["_id"],
                "question_text": target_question_doc["question"],
                "paraphrases": target_question_doc["paraphrases"],
                "answer": target_answer_doc["transcript"],
                "markdown_answer": target_answer_doc["markdownTranscript"],
                "answer_id": target_answer_doc["_id"],
                "answer_media": answer_media,
                "topics": [],
                "external_video_ids": external_video_ids,
            }
            self.questions_by_text[sanitize_string(question_asked)] = q
