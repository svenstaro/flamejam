FROM alpine:3

WORKDIR /app

ENV CONFIG_TYPE=production

# We copy the requirements here and then install the deps in order to make
# better use of Docker caching which goes top to bottom. This means that if we
# did it otherwise, we'd have to rebuild everything without caching each time
# the code changes.
COPY pyproject.toml /app/
RUN apk add --no-cache curl build-base python3-dev git libffi-dev postgresql-dev linux-headers libressl-dev && \
    curl -sSL https://raw.githubusercontent.com/sdispater/poetry/master/get-poetry.py | python3 && \
    ln -s /usr/bin/python3 /usr/bin/python && \
    ln -s /root/.poetry/bin/poetry /usr/bin/poetry && \
    poetry install && \
    apk del build-base linux-headers

# Clean the repo just in case the repo that built this Docker container wasn't
# tidy.
COPY . /app
RUN git clean -dfx
EXPOSE 8080
VOLUME ["/etc/flamejam/flamejam.cfg"]
ENTRYPOINT ["poetry", "run", "uwsgi", "uwsgi_prod.ini"]
