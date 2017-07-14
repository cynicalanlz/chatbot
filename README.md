## Install workflow
```
clone repo
cd to project folder
sudo apt-get install supervisord python build-essential checkinstall
wget https://www.python.org/ftp/python/3.5.2/Python-3.5.2.tgz
sudo tar xzf Python-3.5.2.tgz
cd Python-3.5.2
sudo ./configure
sudo make altinstall
python3.5 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r backend/requirements/shared.txt
pip install -r backend/requirements/dev.txt
```
## Compile dependencies
```
cd to project folder
pip-compile backend/requirements/shared.in --output-file backend/requirements/shared.txt 
pip-compile backend/requirements/dev.in --output-file backend/requirements/dev.txt
```
# Install docker
```
https://www.digitalocean.com/community/tutorials/how-to-install-and-use-docker-on-ubuntu-16-04
```

## Launch in container
```
sudo ./bin/build.sh 
sudo docker rm -f /tapdone
sudo ./bin/run.sh
```
## Launch from supervisord
```
**adapt** paths in supervisord_local.conf
cd to project folder
cd backend
supervisord -c ../supervisord_local.conf   
```



## DB initialization

```
sudo docker exec -i -t $(sudo docker ps -q) /bin/bash
python
   from sqlalchemy import create_engine
   from sqlalchemy.orm.session import sessionmaker
   from service.user.models import Base
   import os
   config = os.environ
   engine = create_engine(config['SQLALCHEMY_DATABASE_URI'])
   session_factory = sessionmaker(engine)
   session_factory.close_all() # <- don't forget to close
   Base.metadata.create_all(engine)
```

## DB reset


```
sudo docker stop $(sudo docker ps -aq)
psql \
   --host=tapdone.cznk1sm7ddt1.us-west-2.rds.amazonaws.com \
   --port=5432 \
   --username tapdone3_user \
   --password \
   --dbname=tapdone3_db

```

```
DELETE from users;
DELETE from slack_teams;
```

```
DROP TABLE users;
DROP SCHEMA public CASCADE;
CREATE SCHEMA public;
```

if needed:
```
GRANT ALL ON SCHEMA public TO postgres;
GRANT ALL ON SCHEMA public TO public;
```

## DB reset user info

```
from service.app import app, db
from service.user.models import User
db.init_app(app)

with app.app_context():
    db.session.query(User).filter_by(slid='U5ZCR2NTH').delete()
    db.session.commit()
    for item in db.session.query(User).filter_by(slid='U5ZCR2NTH'):
        print(item.id)

```

## Stop all docker instances

```
sudo docker stop $(sudo docker ps -aq)
```

## Login to single docker machine

```
sudo docker exec -i -t $(sudo docker ps -q) /bin/bash
```

## Deploy

```
aws ecr get-login
‘’remove -e none from command and execute’’
sudo ./bin/build.sh && sudo docker tag opagrp/tapdone:latest 424467247636.dkr.ecr.us-west-2.amazonaws.com/tapdone4:latest &&  sudo docker push 424467247636.dkr.ecr.us-west-2.amazonaws.com/tapdone4:latest
Перезапустить таск на кластере https://us-west-2.console.aws.amazon.com/ecs/home?region=us-west-2#/clusters/cluster1/tasks
```

## App location

http://ec2-34-212-103-70.us-west-2.compute.amazonaws.com

## App urls

Endpoints:

```
Start with: /api/v1/

register_slack_team - кнопка для регистрации новой слек команды
register_slack - сюда приходит авторизационные данные слека и записываются в бд
register_cb - регистрирует гугл пользователя
get_tokens - получает slack токены
get_user_google_auth - получает объект с авторизационными данными пользователя
```

## Docker commands

```
docker images
docker ps -a
```

## Tutorial
```

./bin/build.sh
./bin/run.sh
open http://`docker-machine ip default`/api/v1/health
```

```
./bin/cleanup.sh
```

## Compile dependancies
```
pip-compile backend/requirements/shared.in --output-file backend/requirements/shared.txt 
```

## Sample deploy script build instructions

1) Retrieve the docker login command that you can use to authenticate your Docker client to your registry:
```aws ecr get-login --region us-west-2```

2) Run the docker login command that was returned in the previous step.
3) Build your Docker image using the following command. For information on building a Docker file from scratch see the instructions here. You can skip this step if your image is already built:
```docker build -t tapdone3 .```

4) After the build completes, tag your image so you can push the image to this repository:
```docker tag tapdone3:latest 424467247636.dkr.ecr.us-west-2.amazonaws.com/tapdone3:latest```

5) Run the following command to push this image to your newly created AWS repository:
```docker push 424467247636.dkr.ecr.us-west-2.amazonaws.com/tapdone3:latest```
