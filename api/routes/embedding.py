import base64

import numpy as np
import tiktoken
from fastapi import APIRouter, Depends
from openai.types.create_embedding_response import Usage

from api.config import config
from api.models import EMBEDDED_MODEL
from api.routes.utils import check_api_key
from api.utils.protocol import EmbeddingCreateParams, Embedding, CreateEmbeddingResponse

embedding_router = APIRouter()


@embedding_router.post("/embeddings", dependencies=[Depends(check_api_key)])
@embedding_router.post("/engines/{model_name}/embeddings", dependencies=[Depends(check_api_key)])
async def create_embeddings(request: EmbeddingCreateParams, model_name: str = None):
    """Creates embeddings for the text"""
    if request.model is None:
        request.model = model_name

    request.input = request.input
    if isinstance(request.input, str):
        request.input = [request.input]
    elif isinstance(request.input, list):
        if isinstance(request.input[0], int):
            decoding = tiktoken.model.encoding_for_model(request.model)
            request.input = [decoding.decode(request.input)]
        elif isinstance(request.input[0], list):
            decoding = tiktoken.model.encoding_for_model(request.model)
            request.input = [decoding.decode(text) for text in request.input]

    # https://huggingface.co/BAAI/bge-large-zh
    if EMBEDDED_MODEL is not None:
        if "bge" in config.EMBEDDING_NAME.lower():
            instruction = ""
            if "zh" in config.EMBEDDING_NAME.lower():
                instruction = "为这个句子生成表示以用于检索相关文章："
            elif "en" in config.EMBEDDING_NAME.lower():
                instruction = "Represent this sentence for searching relevant passages: "
            request.input = [instruction + q for q in request.input]

    data, total_tokens = [], 0
    batches = [
        request.input[i: i + 1024] for i in range(0, len(request.input), 1024)
    ]
    for num_batch, batch in enumerate(batches):
        token_num = sum([len(i) for i in batch])
        vecs = EMBEDDED_MODEL.encode(batch, normalize_embeddings=True)

        bs, dim = vecs.shape
        if config.EMBEDDING_SIZE is not None and config.EMBEDDING_SIZE > dim:
            zeros = np.zeros((bs, config.EMBEDDING_SIZE - dim))
            vecs = np.c_[vecs, zeros]

        if request.encoding_format == "base64":
            vecs = [base64.b64encode(v.tobytes()).decode("utf-8") for v in vecs]
        else:
            vecs = vecs.tolist()

        for i, embed in enumerate(vecs):
            data.append(
                Embedding(index=num_batch * 1024 + i, object="embedding", embedding=embed)
            )

        total_tokens += token_num

    return CreateEmbeddingResponse(
        data=data,
        model=request.model,
        object="list",
        usage=Usage(prompt_tokens=total_tokens, total_tokens=total_tokens),
    )
