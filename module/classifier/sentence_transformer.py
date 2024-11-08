# This software is Copyright ©️ 2020 The University of Southern California. All Rights Reserved.
# Permission to use, copy, modify, and distribute this software and its documentation for educational, research and non-profit purposes, without fee, and without a written agreement is hereby granted, provided that the above copyright notice and subject to the full license file found in the root of this software deliverable. Permission to make commercial use of this software may be obtained by contacting:  USC Stevens Center for Innovation University of Southern California 1150 S. Olive Street, Suite 2300, Los Angeles, CA 90115, USA Email: accounting@stevens.usc.edu
#
# The full terms of this copyright and license should always be found in the root directory of this software deliverable as "license.txt" and if these terms are not found with this software, please contact the USC Stevens Center for the full license.
#
#
from os import path
from sentence_transformers import SentenceTransformer
from typing import Dict
import torch

SENTENCE_TRANSFORMER_MODELS: Dict[str, SentenceTransformer] = {}


def find_or_load_sentence_transformer(file_path: str) -> SentenceTransformer:
    abs_path = path.abspath(file_path)
    if abs_path not in SENTENCE_TRANSFORMER_MODELS:
        SENTENCE_TRANSFORMER_MODELS[abs_path] = SentenceTransformer(
            path.join(file_path, "distilbert-base-nli-mean-tokens"), device="cpu"
        )
    model = SENTENCE_TRANSFORMER_MODELS[abs_path]
    quantized = torch.quantization.quantize_dynamic(
        model,
        {
            torch.nn.Embedding: torch.quantization.qconfig.float_qparams_weight_only_qconfig
        },
        dtype=torch.qint8,
    )
    return quantized
