# This software is Copyright ©️ 2020 The University of Southern California. All Rights Reserved.
# Permission to use, copy, modify, and distribute this software and its documentation for educational, research and non-profit purposes, without fee, and without a written agreement is hereby granted, provided that the above copyright notice and subject to the full license file found in the root of this software deliverable. Permission to make commercial use of this software may be obtained by contacting:  USC Stevens Center for Innovation University of Southern California 1150 S. Olive Street, Suite 2300, Los Angeles, CA 90115, USA Email: accounting@stevens.usc.edu
#
# The full terms of this copyright and license should always be found in the root directory of this software deliverable as "license.txt" and if these terms are not found with this software, please contact the USC Stevens Center for the full license.
#
#
import os
from dataclasses import dataclass
from module.mentor import Media

ARCH_LR_TRANSFORMER = "module.classifier.arch.lr_transformer"


def mentor_model_path(models_path: str, mentor_id: str, arch: str, p: str = "") -> str:
    return (
        os.path.join(models_path, mentor_id, arch, p)
        if p
        else os.path.join(models_path, mentor_id, arch)
    )


@dataclass
class AnswerMedia:
    web_media: Media
    mobile_media: Media
    vtt_media: Media


@dataclass
class ExternalVideoIds:
    wistiaId: str


@dataclass
class QuestionClassiferPredictionResult:
    answer_id: str
    answer_text: str
    answer_markdown_text: str
    answer_media: AnswerMedia
    highest_confidence: float
    feedback_id: str
    external_video_ids: ExternalVideoIds
    answer_missing: bool
    question_id: str
