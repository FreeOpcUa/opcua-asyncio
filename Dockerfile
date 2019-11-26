FROM python:3.8

RUN pip install asyncua

CMD uaserver
