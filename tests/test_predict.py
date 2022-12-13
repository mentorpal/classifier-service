# flake8: noqa
# todo until all tests are implemented
#
# This software is Copyright ©️ 2020 The University of Southern California. All Rights Reserved.
# Permission to use, copy, modify, and distribute this software and its documentation for educational, research and non-profit purposes, without fee, and without a written agreement is hereby granted, provided that the above copyright notice and subject to the full license file found in the root of this software deliverable. Permission to make commercial use of this software may be obtained by contacting:  USC Stevens Center for Innovation University of Southern California 1150 S. Olive Street, Suite 2300, Los Angeles, CA 90115, USA Email: accounting@stevens.usc.edu
#
# The full terms of this copyright and license should always be found in the root directory of this software deliverable as "license.txt" and if these terms are not found with this software, please contact the USC Stevens Center for the full license.
#
from os import path, environ
from typing import Dict, List

import json
import pytest
import responses

from module.mentor import Media
from module.api import OFF_TOPIC_THRESHOLD_DEFAULT
from module.classifier.arch.lr_transformer import TransformersQuestionClassifierTraining
from module.classifier.predict import TransformersQuestionClassifierPrediction
from .helpers import fixture_path
from .fixtures import sbert_encodings


@pytest.fixture(autouse=True)
def python_path_env(monkeypatch, shared_root):
    monkeypatch.setenv("GRAPHQL_ENDPOINT", "http://graphql")
    monkeypatch.setenv("SBERT_ENDPOINT", "http://sbert")


@pytest.fixture(scope="module")
def data_root() -> str:
    return fixture_path("data")


def _ensure_trained(mentor_id: str, shared_root: str, output_dir: str) -> None:
    """
    NOTE: we don't want this test to do any training.
    But for the case that there's no trained model,
    it's more convienient to just train it here.
    Once it has been trained, it should be committed
    and then subsequent runs of the test
    will use the fixture/trained model
    """
    if path.isdir(
        path.join(output_dir, mentor_id, "module.classifier.arch.lr_transformer")
    ):
        return
    training = TransformersQuestionClassifierTraining(
        mentor_id, shared_root, output_dir
    )
    training.train()


@responses.activate
@pytest.mark.parametrize(
    "mentor_id,question,expected_answer_id,expected_answer,expected_media",
    [
        (
            "clint",
            "What is your name?",
            "62709347a2fa682085cdbd1c",
            "Clinton Anderson.",
            {
                "web_media": {
                    "type": "video",
                    "tag": "web",
                    "url": "https://videourl.org/614993b2a8bc838230c159ed/web.mp4",
                },
                "mobile_media": {
                    "type": "video",
                    "tag": "mobile",
                    "url": "https://videourl.org/614993b2a8bc838230c159ed/mobile.mp4",
                },
                "vtt_media": {
                    "type": "subtitles",
                    "tag": "en",
                    "url": "https://videourl.org/614993b2a8bc838230c159ed/en.vtt",
                },
            },
        ),
        (
            "clint",
            "How old are you now?",
            "62709347a2fa682085cdbd43",
            "I'm 41 years old.",
            {
                "web_media": {
                    "type": "video",
                    "tag": "web",
                    "url": "https://videourl.org/61499bb0a8bc8333bac1629e/web.mp4",
                },
                "mobile_media": {
                    "type": "video",
                    "tag": "mobile",
                    "url": "https://videourl.org/61499bb0a8bc8333bac1629e/mobile.mp4",
                },
                "vtt_media": {
                    "type": "subtitles",
                    "tag": "en",
                    "url": "https://videourl.org/61499bb0a8bc8333bac1629e/en.vtt",
                },
            },
        ),
        (
            "clint",
            "Who are you?",
            "62709347a2fa682085cdbd1c",
            "Clinton Anderson.",
            {
                "web_media": {
                    "type": "video",
                    "tag": "web",
                    "url": "https://videourl.org/614993b2a8bc838230c159ed/web.mp4",
                },
                "mobile_media": {
                    "type": "video",
                    "tag": "mobile",
                    "url": "https://videourl.org/614993b2a8bc838230c159ed/mobile.mp4",
                },
                "vtt_media": {
                    "type": "subtitles",
                    "tag": "en",
                    "url": "https://videourl.org/614993b2a8bc838230c159ed/en.vtt",
                },
            },
        ),
        (
            "clint",
            "What's your age?",
            "62709347a2fa682085cdbd43",
            "I'm 41 years old.",
            {
                "web_media": {
                    "type": "video",
                    "tag": "web",
                    "url": "https://videourl.org/61499bb0a8bc8333bac1629e/web.mp4",
                },
                "mobile_media": {
                    "type": "video",
                    "tag": "mobile",
                    "url": "https://videourl.org/61499bb0a8bc8333bac1629e/mobile.mp4",
                },
                "vtt_media": {
                    "type": "subtitles",
                    "tag": "en",
                    "url": "https://videourl.org/61499bb0a8bc8333bac1629e/en.vtt",
                },
            },
        ),
    ],
)
def test_gets_answer_for_exact_match_and_paraphrases(
    data_root: str,
    shared_root: str,
    mentor_id: str,
    question: str,
    expected_answer_id: str,
    expected_answer: str,
    expected_media: Dict[str, Media],
):
    with open(fixture_path("graphql/{}.json".format(mentor_id))) as f:
        data = json.load(f)
    responses.add(responses.POST, "http://graphql", json=data, status=200)
    responses.add(
        responses.GET,
        "http://sbert/encode",
        json={"query": question, "encoding": sbert_encodings[question]},
        status=200,
    )
    _ensure_trained(mentor_id, shared_root, data_root)
    classifier = TransformersQuestionClassifierPrediction(mentor_id, data_root)
    result = classifier.evaluate(question, "123")
    assert result.answer_id == expected_answer_id
    assert result.answer_text == expected_answer
    assert result.answer_media == expected_media
    assert result.highest_confidence > 0.8  # investigate why its not 1.0
    assert result.feedback_id is not None


@responses.activate
@pytest.mark.parametrize(
    "mentor_id,question,expected_answer_id,expected_answer,expected_media",
    [
        (
            "clint",
            "What's your name?",
            "62709347a2fa682085cdbd1c",
            "Clinton Anderson.",
            {
                "web_media": {
                    "type": "video",
                    "tag": "web",
                    "url": "https://videourl.org/614993b2a8bc838230c159ed/web.mp4",
                },
                "mobile_media": {
                    "type": "video",
                    "tag": "mobile",
                    "url": "https://videourl.org/614993b2a8bc838230c159ed/mobile.mp4",
                },
                "vtt_media": {
                    "type": "subtitles",
                    "tag": "en",
                    "url": "https://videourl.org/614993b2a8bc838230c159ed/en.vtt",
                },
            },
        ),
        (
            "clint",
            "Tell me your name",
            "62709347a2fa682085cdbd1c",
            "Clinton Anderson.",
            {
                "web_media": {
                    "type": "video",
                    "tag": "web",
                    "url": "https://videourl.org/614993b2a8bc838230c159ed/web.mp4",
                },
                "mobile_media": {
                    "type": "video",
                    "tag": "mobile",
                    "url": "https://videourl.org/614993b2a8bc838230c159ed/mobile.mp4",
                },
                "vtt_media": {
                    "type": "subtitles",
                    "tag": "en",
                    "url": "https://videourl.org/614993b2a8bc838230c159ed/en.vtt",
                },
            },
        ),
    ],
)
def test_predicts_answer(
    data_root: str,
    shared_root: str,
    mentor_id: str,
    question: str,
    expected_answer_id: str,
    expected_answer: str,
    expected_media: List[Media],
):
    with open(fixture_path("graphql/{}.json".format(mentor_id))) as f:
        data = json.load(f)
    responses.add(responses.POST, "http://graphql/", json=data, status=200)
    responses.add(
        responses.GET,
        "http://sbert/encode",
        json={"query": question, "encoding": sbert_encodings[question]},
        status=200,
    )
    _ensure_trained(mentor_id, shared_root, data_root)
    classifier = TransformersQuestionClassifierPrediction(mentor_id, data_root)
    result = classifier.evaluate(question, "123")
    assert result.answer_id == expected_answer_id
    assert result.answer_text == expected_answer
    assert result.answer_media == expected_media
    assert result.highest_confidence != 1
    assert result.feedback_id is not None


def _test_gets_off_topic(
    monkeypatch,
    data_root: str,
    shared_root: str,
    mentor_id: str,
    question: str,
    expected_answer_id: str,
    expected_answer: str,
):
    monkeypatch.setenv("OFF_TOPIC_THRESHOLD", "1.0")  # everything is offtopic
    with open(fixture_path("graphql/{}.json".format(mentor_id))) as f:
        data = json.load(f)
    responses.add(responses.POST, "http://graphql/", json=data, status=200)
    responses.add(
        responses.GET,
        "http://sbert/encode",
        json={"query": question, "encoding": sbert_encodings[question]},
        status=200,
    )
    _ensure_trained(mentor_id, shared_root, data_root)
    classifier = TransformersQuestionClassifierPrediction(mentor_id, data_root)
    result = classifier.evaluate(question, "123")

    assert result.answer_id == expected_answer_id
    assert result.answer_text == expected_answer


@responses.activate
@pytest.mark.parametrize(
    "mentor_id,question,expected_answer_id,expected_answer",
    [
        (
            "clint",
            "According to all known laws of aviation, there is no way a bee should be able to fly. Its wings are too small to get its fat little body off the ground. The bee, of course, flies anyway because bees don't care what humans think is impossible.",
            "6270eb5aa2fa682085fd126d",
            "That's a great question, unfortunately, I never recorded an answer for that.",
        )
    ],
)
def test_gets_off_topic(
    monkeypatch,
    data_root: str,
    shared_root: str,
    mentor_id: str,
    question: str,
    expected_answer_id: str,
    expected_answer: str,
):
    _test_gets_off_topic(
        monkeypatch,
        data_root,
        shared_root,
        mentor_id,
        question,
        expected_answer_id,
        expected_answer,
    )


@responses.activate
@pytest.mark.parametrize(
    "mentor_id,question,expected_answer_id,expected_answer",
    [
        (
            "mentor_has_no_offtopic",
            "According to all known laws of aviation, there is no way a bee should be able to fly. Its wings are too small to get its fat little body off the ground. The bee, of course, flies anyway because bees don't care what humans think is impossible.",
            "_OFF_TOPIC_",
            "_OFF_TOPIC_",
        )
    ],
)
def test_gets_off_topic_for_user_with_no_offtopic_response(
    monkeypatch,
    data_root: str,
    shared_root: str,
    mentor_id: str,
    question: str,
    expected_answer_id: str,
    expected_answer: str,
):
    _test_gets_off_topic(
        monkeypatch,
        data_root,
        shared_root,
        mentor_id,
        question,
        expected_answer_id,
        expected_answer,
    )
