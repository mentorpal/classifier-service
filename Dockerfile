FROM public.ecr.aws/lambda/python:3.8

WORKDIR /app

ENV PYTHONPATH /app
ENV PATH="/app/bin:${PATH}"

COPY shared shared
COPY pyproject.toml poetry.lock ./
COPY *.py ./
COPY module module

# sls does not support docker build --squash, and the image is 6GB
# so to avoid multiple layers lets do everything in one:
RUN python -m pip install --upgrade pip \
    && pip install --upgrade poetry \
    && poetry config virtualenvs.create false \
    && poetry install --no-dev \
    && pip install --upgrade poethepoet \
# not sure why tomlkit isnt installed in the first place:
    && pip install --upgrade poetry \
    && poetry run poe force-cpu-only \
    && poetry cache clear $(poetry cache list) --all -n \
    # seems like poetry and pip caches
    # are not clearing no matter what so force delete:
    && rm -rf /root/.cache/* pyproject.toml poetry.lock \
    && pip uninstall -y poetry poethepoet
