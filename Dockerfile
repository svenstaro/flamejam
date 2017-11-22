FROM alpine:3.6

WORKDIR /app

# We copy the requirements here and then install the deps in order to make
# better use of Docker caching which goes top to bottom. This means that if we
# did it otherwise, we'd have to rebuild everything without caching each time
# the code changes.
COPY requirements.txt dev-requirements.txt /app/
RUN apk add --no-cache build-base make python3-dev git libffi-dev postgresql-dev linux-headers \
	libressl-dev && \
    pip3 install pip -r requirements.txt -r dev-requirements.txt && \
    apk del build-base linux-headers

# Clean the repo just in case the repo that built this Docker container wasn't
# tidy.
COPY . /app
RUN git clean -dfx
EXPOSE 8080
ENTRYPOINT ["uwsgi", "deploy/uwsgi.ini"]
