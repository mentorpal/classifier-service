# This software is Copyright ©️ 2020 The University of Southern California. All Rights Reserved.
# Permission to use, copy, modify, and distribute this software and its documentation for educational, research and non-profit purposes, without fee, and without a written agreement is hereby granted, provided that the above copyright notice and subject to the full license file found in the root of this software deliverable. Permission to make commercial use of this software may be obtained by contacting:  USC Stevens Center for Innovation University of Southern California 1150 S. Olive Street, Suite 2300, Los Angeles, CA 90115, USA Email: accounting@stevens.usc.edu
#
# The full terms of this copyright and license should always be found in the root directory of this software deliverable as "license.txt" and if these terms are not found with this software, please contact the USC Stevens Center for the full license.
#
#
import logging
import random
import joblib
import numpy
from typing import Union, Tuple
from module.classifier import (
    AnswerMedia,
    mentor_model_path,
    ARCH_LR_TRANSFORMER,
    QuestionClassiferPredictionResult,
    Media,
)
from module.api import create_user_question, get_off_topic_threshold, sbert_encode
from module.mentor import Mentor
from module.utils import file_last_updated_at, sanitize_string

AnswerIdTextAndMedia = Tuple[str, str, str, Media, Media, Media]


class TransformersQuestionClassifierPrediction:
    def __init__(self, mentor: Union[str, Mentor], data_path: str):
        if isinstance(mentor, str):
            logging.info("loading mentor id {}...".format(mentor))
            mentor = Mentor(mentor)
        assert isinstance(
            mentor, Mentor
        ), "invalid type for mentor (expected mentor.Mentor or string id for a mentor, encountered {}".format(
            type(mentor)
        )
        self.mentor = mentor
        self.model_file = mentor_model_path(
            data_path, mentor.id, ARCH_LR_TRANSFORMER, "model.pkl"
        )
        self.model = self.__load_model()

    def evaluate(
        self,
        question: str,
        chat_session_id: str,
        canned_question_match_disabled: bool = False,
    ) -> QuestionClassiferPredictionResult:

        sanitized_question = sanitize_string(question)
        if not canned_question_match_disabled:
            if (
                sanitized_question in self.mentor.manual_question_mappings
                or sanitized_question in self.mentor.questions_by_text
            ):
                q = (
                    self.mentor.manual_question_mappings[sanitized_question]
                    if sanitized_question in self.mentor.manual_question_mappings
                    else self.mentor.questions_by_text[sanitized_question]
                )
                answer_id = q["answer_id"]
                answer = q["answer"]
                markdown_answer = q["markdown_answer"]
                answer_media = q["answer_media"]
                feedback_id = create_user_question(
                    self.mentor.id,
                    question,
                    answer_id,
                    chat_session_id,
                    "PARAPHRASE"
                    if sanitized_question != sanitize_string(q["question_text"])
                    else "EXACT",
                    1.0,
                )
                return QuestionClassiferPredictionResult(
                    answer_id, answer, markdown_answer, answer_media, 1.0, feedback_id
                )
        encoding_json = sbert_encode(question)
        embedded_question = numpy.array(encoding_json["encoding"])
        (
            answer_id,
            answer,
            markdownAnswer,
            answer_media,
            highest_confidence,
        ) = self.__get_prediction(embedded_question)
        feedback_id = create_user_question(
            self.mentor.id,
            question,
            answer_id,
            chat_session_id,
            "OFF_TOPIC"
            if highest_confidence < get_off_topic_threshold()
            else "CLASSIFIER",
            highest_confidence,
        )
        if highest_confidence < get_off_topic_threshold():
            answer_id, answer, markdownAnswer, answer_media = self.__get_offtopic()
        return QuestionClassiferPredictionResult(
            answer_id,
            answer,
            markdownAnswer,
            answer_media,
            highest_confidence,
            feedback_id,
        )

    def get_last_trained_at(self) -> float:
        return file_last_updated_at(self.model_file)

    def __load_model(self):
        logging.info("loading model from path {}...".format(self.model_file))
        return joblib.load(self.model_file)

    def __get_prediction(
        self, embedded_question
    ) -> Tuple[str, str, str, AnswerMedia, float]:
        prediction = self.model.predict([embedded_question])
        decision = self.model.decision_function([embedded_question])
        if type(decision[0]) == numpy.ndarray:
            highest_confidence = max(decision[0])
        else:
            # edge-case - just a single number:
            highest_confidence = decision[0]
        answer = self.mentor.answer_id_by_answer[prediction[0]]
        answer_text = answer["transcript"]
        answer_markdown_text = answer["markdownTranscript"]
        answer_key = sanitize_string(answer_text)
        answer_media = self.mentor.questions_by_answer[answer_key].get("answer_media")
        return (
            prediction[0],
            answer_text,
            answer_markdown_text,
            answer_media,
            float(highest_confidence),
        )

    def __get_offtopic(self) -> AnswerIdTextAndMedia:
        try:
            id, text, markdownText, answer_media = random.choice(
                self.mentor.utterances_by_type["_OFF_TOPIC_"]
            )
            return (id, text, markdownText, answer_media)
        except KeyError:
            return ("_OFF_TOPIC_", "_OFF_TOPIC_", "_OFF_TOPIC_", {})
