FROM ubuntu:22.04

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV TZ=Asia/Almaty

COPY requirements.txt .

RUN apt-get update && \
    apt-get install -yqq --no-install-recommends libreoffice python3 python3-pip systemd && \
    pip3 install -r requirements.txt && \
    timedatectl set-timezone ${TZ}

WORKDIR /pocket-moodle
COPY . /pocket-moodle

EXPOSE 8080

RUN adduser -u 5678 --disabled-password --gecos "" appuser && chown -R appuser /pocket-moodle
USER appuser

CMD ["python3", "main.py"]
