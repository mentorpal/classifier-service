#
# This software is Copyright ©️ 2020 The University of Southern California. All Rights Reserved.
# Permission to use, copy, modify, and distribute this software and its documentation for educational, research and non-profit purposes, without fee, and without a written agreement is hereby granted, provided that the above copyright notice and subject to the full license file found in the root of this software deliverable. Permission to make commercial use of this software may be obtained by contacting:  USC Stevens Center for Innovation University of Southern California 1150 S. Olive Street, Suite 2300, Los Angeles, CA 90115, USA Email: accounting@stevens.usc.edu
#
# The full terms of this copyright and license should always be found in the root directory of this software deliverable as "license.txt" and if these terms are not found with this software, please contact the USC Stevens Center for the full license.
#
from typing import Dict, List
from module.classifier.ner import FollowupQuestion, NamedEntities
from .types import AnswerInfo
from .api import fetch_category, fetch_mentor_answers_and_name


def generate_followups(
    category: str,
    headers: Dict[str, str] = {},
) -> List[FollowupQuestion]:
    data = fetch_category(category, headers=headers)
    me = data.get("me")
    if me is None:
        raise Exception("failed to fetch category answers")
    category_answer = me.get("categoryAnswers", [])
    category_answers = [
        AnswerInfo(
            answer_text=answer_data.get("answerText") or "",
            question_text=answer_data.get("questionText") or "",
        )
        for answer_data in category_answer
    ]
    all_answered, name = fetch_mentor_answers_and_name(headers=headers)
    followups = NamedEntities(category_answers, name).generate_questions(
        all_answered
    )
    return followups
