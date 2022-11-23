FROM lambci/lambda:python3.8

USER root

ENV APP_DIR /var/task

WORKDIR $APP_DIR
