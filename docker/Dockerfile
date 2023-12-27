FROM python:3.12-alpine

WORKDIR /repo

RUN pip3 install urlwatch feedgen

COPY . /repo/

ENTRYPOINT ["python3", "/repo/urlwatch_feed/main.py"]
