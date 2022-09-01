#
# This software is Copyright ©️ 2020 The University of Southern California. All Rights Reserved.
# Permission to use, copy, modify, and distribute this software and its documentation for educational, research and non-profit purposes, without fee, and without a written agreement is hereby granted, provided that the above copyright notice and subject to the full license file found in the root of this software deliverable. Permission to make commercial use of this software may be obtained by contacting:  USC Stevens Center for Innovation University of Southern California 1150 S. Olive Street, Suite 2300, Los Angeles, CA 90115, USA Email: accounting@stevens.usc.edu
#
# The full terms of this copyright and license should always be found in the root directory of this software deliverable as "license.txt" and if these terms are not found with this software, please contact the USC Stevens Center for the full license.
#
import pytest
import logging
import responses

from module.classifier.arch.lr_transformer import TransformersQuestionClassifierTraining
from module.classifier import ARCH_LR_TRANSFORMER
from module.classifier.predict import TransformersQuestionClassifierPrediction

from .helpers import (
    fixture_mentor_data,
    fixture_path,
    load_mentor_csv,
    load_test_csv,
    run_model_against_testset,
)
from module.types import _MentorTrainAndTestConfiguration


@pytest.fixture(scope="module")
def data_root() -> str:
    return fixture_path("data_out")


@responses.activate
@pytest.mark.parametrize(
    "training_configuration",
    [
        _MentorTrainAndTestConfiguration(
            mentor_id="clint", arch=ARCH_LR_TRANSFORMER, expected_training_accuracy=0.5
        )
    ],
)
def test_train_and_predict_transformers(
    training_configuration: _MentorTrainAndTestConfiguration,
    tmpdir,
    shared_root: str,
):
    mentor = load_mentor_csv(
        fixture_mentor_data(training_configuration.mentor_id, "data.csv")
    )
    test_set = load_test_csv(
        fixture_mentor_data(training_configuration.mentor_id, "test.csv")
    )
    data = {"data": {"mentor": mentor.to_dict()}}
    responses.add(responses.POST, "http://graphql", json=data, status=200)
    result = TransformersQuestionClassifierTraining(
        training_configuration.mentor_id,
        shared_root,
        tmpdir,
    ).train()
    assert result.accuracy >= training_configuration.expected_training_accuracy

    classifier = TransformersQuestionClassifierPrediction(
        training_configuration.mentor_id, tmpdir
    )
    test_results = run_model_against_testset(
        classifier, test_set, shared_root, responses
    )

    logging.warning(test_results.errors)
    logging.warning(
        f"percentage passed = {test_results.passing_tests}/{len(test_results.results)}"
    )
    assert len(test_results.errors) == 0
