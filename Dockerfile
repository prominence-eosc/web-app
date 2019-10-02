FROM alpine:latest
RUN apk add --no-cache gcc \
                       musl-dev \
                       linux-headers \
                       uwsgi-python \
                       uwsgi-http \
                       python \
                       python-dev \
                       py-requests \
                       py-requests-oauthlib \
                       py-flask \
                       py-futures \
                       py-pip 

RUN mkdir /prominence
COPY app /prominence/app
COPY prominence.py /prominence/

ENTRYPOINT ["/usr/sbin/uwsgi", \
            "--plugins-dir", "/usr/lib/uwsgi", \
            "--plugins", "http,python", \
            "--http-socket", ":5000", \
            "--threads", "2", \
            "--uid", "uwsgi", \
            "--manage-script-name", \
            "--master", \
            "--chdir", "/prominence", \
            "--mount", "/=prominence:app"]
