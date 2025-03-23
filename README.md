# Pocket Moodle Service

## Overview
This is a main telegram bot service that manages all commands to a bot, provides notifications on new/updated deadlines/grades from LMS Moodle.
Also functionality to upload to submition boxes in Moodle course


## Prerequisites
- Docker

## Running the Service

### 1. Clone the Repository
```bash
git clone https://github.com/AITUSAIT/pocket-moodle.git
cd pocket-moodle
```

### 2. provide environment variables
```
TOKEN="bot token"

TEST="0" //0 or 1 when 1 only commands from users that provided in Admin table are not ignored

PM_HOST="host to pocket-moodle-api"
PM_TOKEN="token" //tocken from servers table to be able to send request to pocket-moodle-api

TZ="Asia/Aqtobe"
```

### 3. Build docker image
```bash
docker build --env .env --tag <image tag> .
```

### 4. Run docker container
```bash
docker run --env-file .env -d <image tag>
```

## License
This project is licensed under the GNU General Public License. See the `LICENSE` file for more details.
