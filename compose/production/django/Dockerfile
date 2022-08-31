ARG PYTHON_VERSION=3.9-slim-bullseye
# define an alias for the specfic python version used in this file.
FROM python:${PYTHON_VERSION} as python

ENV PYTHONIOENCODING UTF-8
ENV LC_ALL en_US.UTF-8

#RUN mkdir -p /root/.pip/ && \
#    echo "[global]\nindex-url = https://pypi.tuna.tsinghua.edu.cn/simple" > /root/.pip/pip.conf && \
#    sed -i 's@/security.ubuntu.com/@/registry.docker-cn.com/g@' /etc/apt/sources.list && \
#    sed -i 's/http:\/\/archive.ubuntu.com\/ubuntu\//http:\/\/mirrors.163.com\/ubuntu\//g' /etc/apt/sources.list && \
#    apt-get clean && \
#    apt-get update && \

# Requirements are installed here to ensure they will be cached.
COPY ./requirements /requirements
RUN python -m pip install -i http://mirrors.aliyun.com/pypi/simple/ --trusted-host=mirrors.aliyun.com --upgrade pip
RUN python -m pip install -i http://mirrors.aliyun.com/pypi/simple/ --trusted-host=mirrors.aliyun.com --no-cache-dir -r /requirements/production.txt

COPY ./compose/production/django/entrypoint /entrypoint
COPY ./compose/production/django/start /start

RUN sed -i 's/\r//' /entrypoint && chmod +x /entrypoint \
  && sed -i 's/\r//' /start && chmod +x /start

RUN mkdir -p /logs
RUN mkdir -p /u01/main
WORKDIR /u01/main
COPY . .

ENTRYPOINT ["/entrypoint"]
