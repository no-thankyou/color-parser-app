FROM python:3.9

RUN mkdir /app && python -m pip install pipenv
WORKDIR /app

ADD Pipfile /app/Pipfile
ADD Pipfile.lock /app/Pipfile.lock

RUN pipenv install --system

ADD . /app

CMD uvicorn server:app --reload --port 7000 --host 0.0.0.0
