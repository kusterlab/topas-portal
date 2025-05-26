FROM python:3.9.21-slim-bookworm AS dev

ARG DEBIAN_FRONTEND=noninteractive

#######################
# Python dependencies #
#######################

ENV HOME  /root/flask-backend/
WORKDIR /root/flask-backend/

# see https://github.com/python-poetry/poetry/issues/1427
ENV LANG C.UTF-8

RUN pip install -U pip
RUN pip install poetry==1.8.3
RUN pip install gunicorn   # for using gunicorn

ADD ./pyproject.toml /root/flask-backend/pyproject.toml
ADD ./poetry.lock /root/flask-backend/poetry.lock

# poetry useses virtualenvs by default -> we want to create a .venv folder
RUN poetry config virtualenvs.in-project true
RUN poetry install  --without dev --extras "pgsql"

###################
# Add Python code #
###################

FROM python:3.9.21-slim-bookworm AS deploy

COPY --from=dev /root/flask-backend/.venv /root/flask-backend/.venv
ENV PATH="/root/flask-backend/.venv/bin:$PATH"

ADD ./ /root/flask-backend
WORKDIR /root/flask-backend
#CMD ["sh","./gunicorn.sh"]    # for using gunicorn
CMD [ "python3", "-u", "./app.py"]
ENTRYPOINT []

