FROM public.ecr.aws/lambda/python:3.12

WORKDIR /app

ENV PYTHONPATH /app
ENV PATH="/app/bin:${PATH}"

COPY shared shared
COPY pyproject.toml poetry.lock ./
COPY *.py ./
COPY module module

# sls does not support docker build --squash, i filed an issue:
# https://github.com/serverless/serverless/issues/10712
# the image is 6GB so to avoid multiple layers lets do everything in one:
# TODO try `pip --no-cache-dir`
RUN python -m pip install --upgrade pip \
    && pip install --no-cache-dir --upgrade poetry \
    && poetry config virtualenvs.create false \
    && poetry install --without dev --no-root \
    # # poetry installs full torch because its transformers dependency:
    # this will install just the cpu (no cuda) version of torch:
    && pip install torch==1.9.1+cpu torchvision==0.10.1+cpu -f https://download.pytorch.org/whl/torch_stable.html \
    # force delete poetry and pip caches
    && rm -rf /root/.cache/* pyproject.toml poetry.lock \
# TODO this leaves all poetry pip dependencies installed
    && pip uninstall -y poetry virtualenv pyparsing
