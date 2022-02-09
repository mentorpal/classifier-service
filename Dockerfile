FROM public.ecr.aws/lambda/python:3.8

WORKDIR /app

ENV PYTHONPATH /app
ENV PATH="/app/bin:${PATH}"

COPY shared shared
RUN python -m pip install --upgrade pip
RUN pip install --upgrade poetry \
    && poetry config virtualenvs.create false
COPY pyproject.toml poetry.lock ./
RUN poetry install --no-dev
RUN pip install --upgrade poethepoet
# not sure why tomlkit isnt installed in the first place:
RUN pip install --upgrade poetry
RUN poetry run poe force-cpu-only
RUN poetry cache clear $(poetry cache list) --all -n \
    # seems like poetry and pip caches
    # are not clearing no matter what so force delete:
    && rm -rf /root/.cache/* pyproject.toml poetry.lock \
    && pip uninstall -y poetry poethepoet
COPY *.py ./
COPY module module

# You can overwrite command in `serverless.yml` template
# CMD ["/app/train.handler"]
CMD ["train.handler"]
