FROM python:3.13-slim
ENV POETRY_VIRTUALENVS_CREATE=false

RUN apt-get update && apt-get install -y build-essential

WORKDIR /main

COPY pyproject.toml poetry.lock ./
COPY republica_facil/ ./republica_facil
COPY README.md ./

RUN pip install --no-cache-dir poetry
RUN poetry config installer.max-workers 10
RUN poetry install --no-interaction --no-ansi --without dev

EXPOSE 8000

CMD ["poetry", "run", "fastapi", "dev", "republica_facil/main.py", "--host", "0.0.0.0"]