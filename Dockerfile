FROM ubuntu:22.04

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV TZ=Asia/Almaty

COPY requirements.txt .

RUN apt-get update && \
    apt-get install -yqq --no-install-recommends libreoffice python3 python3-pip tzdata && \
    pip3 install -r requirements.txt && \
    ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone && \
    dpkg-reconfigure --frontend noninteractive tzdata

WORKDIR /pocket-moodle
COPY . /pocket-moodle

EXPOSE 8080

RUN adduser -u 5678 --disabled-password --gecos "" appuser && chown -R appuser /pocket-moodle
USER appuser

CMD ["python3", "main.py"]
