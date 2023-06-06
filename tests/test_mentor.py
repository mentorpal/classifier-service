#
# This software is Copyright ©️ 2020 The University of Southern California. All Rights Reserved.
# Permission to use, copy, modify, and distribute this software and its documentation for educational, research and non-profit purposes, without fee, and without a written agreement is hereby granted, provided that the above copyright notice and subject to the full license file found in the root of this software deliverable. Permission to make commercial use of this software may be obtained by contacting:  USC Stevens Center for Innovation University of Southern California 1150 S. Olive Street, Suite 2300, Los Angeles, CA 90115, USA Email: accounting@stevens.usc.edu
#
# The full terms of this copyright and license should always be found in the root directory of this software deliverable as "license.txt" and if these terms are not found with this software, please contact the USC Stevens Center for the full license.
#
import json
import responses
import pytest
from module.mentor import Mentor
from .helpers import fixture_path
import re


@responses.activate
@pytest.mark.parametrize(
    "mentor_id,expected_data_file",
    [("clint", "clint_expected_loaded_mentor_data")],
)
def test_loads_mentor_from_api(mentor_id, expected_data_file):
    with open(fixture_path("graphql/{}.json".format(mentor_id))) as f:
        data = json.load(f)
    with open(fixture_path("graphql/clint_graded_user_questions.json")) as f:
        graded_user_questions_data = json.load(f)
    with open(fixture_path("graphql/{}.json".format(expected_data_file))) as f:
        expected_data = json.load(f)
    responses.add(responses.POST, re.compile(".*"), json=data, status=200)
    responses.add(
        responses.POST, re.compile(".*"), json=graded_user_questions_data, status=200
    )
    m = Mentor(mentor_id)
    assert m.id == mentor_id
    assert m.topics == expected_data["topics"]
    assert m.utterances_by_type == expected_data["utterances_by_type"]
    assert m.questions_by_id == expected_data["questions_by_id"]
    assert m.questions_by_text == expected_data["questions_by_text"]
    assert m.questions_by_answer == expected_data["questions_by_answer"]
