FROM ubuntu:22.04

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV TZ=Asia/Aqtobe

COPY requirements.txt .

RUN apt-get update && \
    apt-get install -yqq --no-install-recommends libreoffice python3.11 python3-pip tzdata default-jre libreoffice-java-common && \
    python3.11 -m pip install -r requirements.txt && \
    ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone && \
    dpkg-reconfigure --frontend noninteractive tzdata \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*


WORKDIR /pocket-moodle
COPY . /pocket-moodle

EXPOSE 8080

RUN adduser -u 5678 --disabled-password --gecos "" appuser && chown -R appuser /pocket-moodle
USER appuser

CMD ["python3.11", "main.py"]
