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
export $(cat config/tapdone3.txt)
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
sudo docker start
sudo ./bin/build.sh 
sudo docker rm -f /tapdone
sudo ./bin/run.sh
```
## or launch from supervisord
### Compile supervisord config
```
cd to project folder
cd config
python convert_config.py
cat tapdone3_supervisord.txt 
copy paste to evironment parameter in supervisord config
```
### launch supervisord locally
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
aws configure
*** obtain vars from config/tapdone3_not_server.txt ***
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

## App files
```
  -  backend
	  	manager.py - db initialization commands will be launched from here
		README.md - readme
		requirements - for pip
		service - main code folder
			api.py - Flask api urls definitions
			api_test.py
			app.py - Flask app initialization
			base.py - Database base class for Flask projects models
			config.py - maps config from constants to it's names in library functions
			__init__.py
			__pycache__
			shared - Flask db for apps
			slack.py - aiohttp microservice, gets tokens spawns threads with chatbot
			templates - front-ends templates are stored here because frontend folder is blocked for write
			user - SlackTeam and User models for flask apps
			utils 
				ai.py - functions for api ai
				calendar.py - functions for Google calendar
				__init__.py
				lib.py - misc functions (db get_and_create)
				__pycache__
  -  bin - scripts
		build.sh - build docker container
		cleanup.sh - remove temporary files
		run.sh - start docker container
		run-tapdone.sh - run in supervisord on amazon
		uploadconfig.sh - amazon configs
  -  config
		client_secrets.json - secrets for Google calendar app authorization
		convert_config.py - converting tapdone3.txt to taptodone3_supervisord.txt
		Dockerfile
		gunicorn.conf 
		nginx.conf
		supervisord.conf
		tapdone3_not_server.txt - config for amazon deploy, not used as environment variables
		tapdone3_supervisord.txt - environment variable value for supervisord.conf
		tapdone3.txt - configs which are used as environment variables  
  -  frontend - folder for frontend which is blocked for write
  -  README.md
  -  supervisord_local.conf - config template for launching supervisord locally for testings
  -  venv - virtual environment folder  
  -  version.json
```
## Useful commands

```
docker images
docker ps -a
./bin/build.sh
./bin/run.sh
open http://`docker-machine ip default`/api/v1/health
./bin/cleanup.sh
```

## Compile dependancies
```
pip-compile backend/requirements/shared.in --output-file backend/requirements/shared.txt 
```

## Launch slack team registration

open http://ec2-34-212-103-70.us-west-2.compute.amazonaws.com/api/v1/register_slack_team
register slack team
add tapdone_bot to dm as in https://docs.google.com/document/d/1SHUAwvk2ZVQel5igwMDjdnGSb0rAcLNO6QuxG6DoNt0/edit#bookmark=id.2kklkqohtgpk

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

---

### Prepapring ELB from "scratch"

Creating new load balancer [1](https://www.dropbox.com/s/u11jacdajcycp7b/Screenshot%202017-07-30%2012.08.45.png?dl=0), we will do "Application" type [2](https://www.dropbox.com/s/erz56u0a9fifwd6/Screenshot%202017-07-30%2012.09.15.png?dl=0), will monitor all available "us-west" zones [3](https://www.dropbox.com/s/mfcsbksdy1mkb3x/Screenshot%202017-07-30%2012.09.59.png?dl=0), going to request new certificate from ACM [4](https://www.dropbox.com/s/6e1eo4als8d2lm7/Screenshot%202017-07-30%2012.51.25.png?dl=0), adding a bunch of subdomains [5](https://www.dropbox.com/s/4rovayoanvzcorc/Screenshot%202017-07-30%2012.51.47.png?dl=0), and after validation via email [6](https://www.dropbox.com/s/ln2olg97dos4enk/Screenshot%202017-07-30%2012.53.20.png?dl=0), all certificates are ready [7](https://www.dropbox.com/s/v0nfe93zypp7zud/Screenshot%202017-07-30%2012.56.32.png?dl=0). Now choosing the right certificate [8](https://www.dropbox.com/s/k02npl1ezj9lupp/Screenshot%202017-07-30%2012.57.05.png?dl=0), default security group [9](https://www.dropbox.com/s/gb3lh9zlfdbkf8q/Screenshot%202017-07-30%2012.57.19.png?dl=0), default "target group" [10](https://www.dropbox.com/s/2jm91noznt89c1y/Screenshot%202017-07-30%2012.58.01.png?dl=0), let's force adding exsiting instance to it [11](https://www.dropbox.com/s/60mrn1ti8e3sgqr/Screenshot%202017-07-30%2012.58.24.png?dl=0), final review [12](https://www.dropbox.com/s/bnle6onwpsizegt/Screenshot%202017-07-30%2012.58.34.png?dl=0) and we are good to go [13](https://www.dropbox.com/s/fiv619s9eiw3ad0/Screenshot%202017-07-30%2012.58.44.png?dl=0). Fixing GoDaddy's CNAME record [14](https://www.dropbox.com/s/nqj7b7eoeqbfwmn/Screenshot%202017-07-30%2013.01.26.png?dl=0), and all is working just fine [15](https://www.dropbox.com/s/nqj7b7eoeqbfwmn/Screenshot%202017-07-30%2013.01.26.png?dl=0). You can see instances in Target groups [16](https://www.dropbox.com/s/ixarxg0riv9uslo/Screenshot%202017-07-30%2013.08.55.png?dl=0), also updated proper health check rule [17](https://www.dropbox.com/s/lt3xm8kga25s94x/Screenshot%202017-07-30%2013.19.55.png?dl=0). All is ready at this point.

### Running locally

Prepare environment (usually often overlooked):
```
pyenv global 3.6.0
pyenv local 3.6.0
pip install --upgrade pip
pip install pip-tools
```
Prepare dependencies:
```
cd ~/Dropbox/Code/tapdone3/
pip-compile backend/requirements/shared.in --output-file backend/requirements/shared.txt 
pip-compile backend/requirements/dev.in --output-file backend/requirements/dev.txt
```
Starting docker and checking our running stuff:
```
docker-machine start
docker ps -a
```
Building docker container, cleanup:
```
cd ~/Dropbox/Code/tapdone3/
./bin/build.sh
docker rm -f /tapdone
```
Checking that image correctly generated (will be on top):
Also, check nothing is running
```
docker images
docker ps -a
```
Running the instance:
```
cd ~/Dropbox/Code/tapdone3/
./bin/run.sh
```
Opening in browser (check if it's running first tho):
```
docker ps -a
open http://`docker-machine ip default`/api/health
```
Stopping the instance:
```
docker ps -a
docker stop [CONTAINER ID]
```

### Deploying to AWS

Let's prepare everything locally:
```
aws ecr get-login --region us-west-2
```
It'll return long few lines, this is the command you need to run next:
```
docker login -u AWS -p eyJwY...WSJ9 -e none https://424467247636.dkr.ecr.us-west-2.amazonaws.com
```
Assuming you build the image already, check that you have it:
```
docker images
```
It's going to be in "opagrp/tapdone" with tag "latest". 
Now let's tag it for push:
```
docker tag opagrp/tapdone:latest 424467247636.dkr.ecr.us-west-2.amazonaws.com/tapdone3:latest
```
Checking with:
```
docker images
```
will show it on the very top, same [TAG ID].
Now you can push it to repository:
```
docker push 424467247636.dkr.ecr.us-west-2.amazonaws.com/tapdone3:latest
```
Going to [ECS Container - Repositories](https://us-west-2.console.aws.amazon.com/ecs/home?region=us-west-2#/repositories/tapdone3#images;tagStatus=ALL) you can confirm that it's on the top.
Start with [ECS Container - Clusters](https://us-west-2.console.aws.amazon.com/ecs/home?region=us-west-2#/clusters). Assuming we killed all clusters, start new one [1](https://www.dropbox.com/s/hff4pjb8cb5vi6l/Screenshot%202017-08-01%2019.14.59.png?dl=0), [2](https://www.dropbox.com/s/u4o16b9k82glmdw/Screenshot%202017-08-01%2019.15.52.png?dl=0), [3](https://www.dropbox.com/s/mbk3f80rbup1cnu/Screenshot%202017-08-01%2019.16.12.png?dl=0). Then we continue on [ECS Container - Task Definition](https://us-west-2.console.aws.amazon.com/ecs/home?region=us-west-2#/taskDefinitions). Few steps [4](https://www.dropbox.com/s/ecy8oacqxx39xsa/Screenshot%202017-08-01%2019.17.08.png?dl=0), [5](https://www.dropbox.com/s/s8c8fncijbwc1vx/Screenshot%202017-08-01%2019.19.05.png?dl=0), [6](https://www.dropbox.com/s/1wgnwrb8bhlq8uc/Screenshot%202017-08-01%2019.19.16.png?dl=0), [7](https://www.dropbox.com/s/yyymfn8o54qk4p0/Screenshot%202017-08-01%2019.19.32.png?dl=0), [8](https://www.dropbox.com/s/l37eo1t51qodjp9/Screenshot%202017-08-01%2019.19.55.png?dl=0). Going back to [ECS Container - Clusters](https://us-west-2.console.aws.amazon.com/ecs/home?region=us-west-2#/clusters) to create service [9](https://www.dropbox.com/s/o1r7i12m9a9kchs/Screenshot%202017-08-01%2019.21.00.png?dl=0), [10](https://www.dropbox.com/s/g94cogsll9gztg1/Screenshot%202017-08-01%2019.21.20.png?dl=0), [11](https://www.dropbox.com/s/xrdjfmevm3iqjmd/Screenshot%202017-08-01%2019.21.46.png?dl=0), [12](https://www.dropbox.com/s/2vlqnfkxat82xju/Screenshot%202017-08-01%2019.21.59.png?dl=0). Starting the task [13](https://www.dropbox.com/s/aychnch1yqirepz/Screenshot%202017-08-01%2019.22.55.png?dl=0), [14](https://www.dropbox.com/s/e0kw2a6f0zgijlu/Screenshot%202017-08-01%2019.23.17.png?dl=0).
Should be fine and can check here:
```
open https://tapdone3.test.opagrp.com/api/health
```
If it doesn't open, can go and check that instances is added properly to [EC2 Load Balancing - Target Groups](https://us-west-2.console.aws.amazon.com/ec2/v2/home?region=us-west-2#TargetGroups:).