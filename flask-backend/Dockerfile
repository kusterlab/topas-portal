FROM node:14.18.3-bullseye AS dev

ARG DEBIAN_FRONTEND=noninteractive

#######################
# Python dependencies #
#######################

# https://github.com/pyenv/pyenv/wiki#suggested-build-environment
# https://github.com/pyenv/pyenv/wiki/common-build-problems#prerequisites
ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update && \
    apt-get --no-install-recommends -y install \
      git \
      ca-certificates \
      build-essential \
      libssl-dev \
      zlib1g-dev \
      libbz2-dev \
      libreadline-dev \
      libsqlite3-dev \
      curl \
      llvm \
      libncurses5-dev \
      libncursesw5-dev \
      xz-utils \
      tk-dev \
      libffi-dev \
      liblzma-dev \
    && \
    rm -rf \
      /var/lib/apt/lists/* \
      /usr/share/doc \
      /usr/share/doc-base \
      /usr/share/man \
      /usr/share/locale \
      /usr/share/zoneinfo

## PYENV FOR MODERN PYTHON
# https://github.com/jprjr/docker-pyenv/blob/master/Dockerfile
# This allows an easy installation
ENV HOME  /root/flask-backend/
ENV PYENV_ROOT $HOME/.pyenv
ENV PATH $PYENV_ROOT/shims:$PYENV_ROOT/bin:$PATH

RUN git clone https://github.com/pyenv/pyenv.git ~/.pyenv
##### THIS IS JUST FOR BEING INSIDE THE CONTAINER - NOT FOR INSTALLATION
RUN echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc
RUN echo 'export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc
RUN echo 'eval "$(pyenv init -)"' >> ~/.bashrc

WORKDIR /root/flask-backend/
RUN pyenv install 3.9.12
RUN pyenv local 3.9.12
RUN pyenv rehash

# see https://github.com/python-poetry/poetry/issues/1427
ENV LANG C.UTF-8

RUN pip install -U pip
RUN pip install poetry>=1.8.3
RUN pip install gunicorn   # for using gunicorn

ADD ./pyproject.toml /root/flask-backend/pyproject.toml
ADD ./poetry.lock /root/flask-backend/poetry.lock

# poetry useses virtualenvs by default -> we want global installation
RUN poetry config virtualenvs.create false
RUN poetry install  --without dev --extras "pgsql"

###################
# Add Python code #
###################

ADD ./ /root/flask-backend
WORKDIR /root/flask-backend
#CMD ["sh","./gunicorn.sh"]    # for using gunicorn
CMD [ "python3", "-u", "./app.py"]
ENTRYPOINT []

