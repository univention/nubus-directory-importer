FROM python:3.7-bookworm

RUN apt update && \
    DEBIAN_FRONTEND=noninteractive apt install -y libsasl2-dev python3-dev \
        libldap2-dev libssl-dev ldap-utils slapd

RUN ulimit -n 1024
COPY . /udm-directory-connector

WORKDIR /udm-directory-connector

RUN python3 setup.py install

CMD ["resources/test.sh"]
