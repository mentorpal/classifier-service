# This software is Copyright ©️ 2020 The University of Southern California. All Rights Reserved.
# Permission to use, copy, modify, and distribute this software and its documentation for educational, research and non-profit purposes, without fee, and without a written agreement is hereby granted, provided that the above copyright notice and subject to the full license file found in the root of this software deliverable. Permission to make commercial use of this software may be obtained by contacting:  USC Stevens Center for Innovation University of Southern California 1150 S. Olive Street, Suite 2300, Los Angeles, CA 90115, USA Email: accounting@stevens.usc.edu
#
# The full terms of this copyright and license should always be found in the root directory of this software deliverable as "license.txt" and if these terms are not found with this software, please contact the USC Stevens Center for the full license.
#
#
from os import environ
from typing import Dict
import pylru
from .predict import TransformersQuestionClassifierPrediction


class Entry:
    def __init__(self, classifier: TransformersQuestionClassifierPrediction):
        self.classifier = classifier
        self.last_trained_at = self.classifier.get_last_trained_at()


class Dao:
    def __init__(self, shared_root: str, data_root: str):
        self.shared_root = shared_root
        self.data_root = data_root
        self.cache = pylru.lrucache(int(environ.get("CACHE_MAX_SIZE", "1000")))

    def find_classifier(
        self, mentor_id: str, auth_headers: Dict[str, str] = {}
    ) -> TransformersQuestionClassifierPrediction:
        if mentor_id in self.cache:
            e = self.cache[mentor_id]
            if e and e.last_trained_at >= e.classifier.get_last_trained_at():
                return e.classifier
        c = TransformersQuestionClassifierPrediction(
            mentor_id, self.data_root, auth_headers
        )
        self.cache[mentor_id] = Entry(c)
        return c
