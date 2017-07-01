## DB reset

```
psql \
   --host=tapdone.cznk1sm7ddt1.us-west-2.rds.amazonaws.com \
   --port=5432 \
   --username tapdone3_user \
   --password \
   --dbname=tapdone3_db
```

```
DROP SCHEMA public CASCADE;
CREATE SCHEMA public;
```

if needed:
```
GRANT ALL ON SCHEMA public TO postgres;
GRANT ALL ON SCHEMA public TO public;
```

## DB init op1

```
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

## DB init op2

```
from service.app import app, db
from service.user.models import User
db.init_app(app)

with app.app_context():    
    db.create_all()

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

## Start 

```
sudo /etc/init.d/nginx stop && sudo ./bin/build.sh && sudo docker rm -f /tapdone && sudo ./bin/run.sh
```

```
docker-machine start
`docker-machine env`
docker images
docker ps -a
```

```
./bin/build.sh
./bin/run.sh
open http://`docker-machine ip default`/api/v1/hello
```

```
./bin/cleanup.sh
```

## App location

http://ec2-34-212-103-70.us-west-2.compute.amazonaws.com

## App urls

/api/v1/register_cb

## Docker bot commands 

https://us-west-2.console.aws.amazon.com/ecs/home?region=us-west-2#/repositories/tapdone3#images;tagStatus=ALL

## Compile dependancies

pip-compile backend/requirements/shared.in --output-file backend/requirements/shared.txt 

## Sample deployt script build instructions

1) Retrieve the docker login command that you can use to authenticate your Docker client to your registry:
```aws ecr get-login --region us-west-2```

2) Run the docker login command that was returned in the previous step.
3) Build your Docker image using the following command. For information on building a Docker file from scratch see the instructions here. You can skip this step if your image is already built:
```docker build -t tapdone3 .```

4) After the build completes, tag your image so you can push the image to this repository:
```docker tag tapdone3:latest 424467247636.dkr.ecr.us-west-2.amazonaws.com/tapdone3:latest```

5) Run the following command to push this image to your newly created AWS repository:
```docker push 424467247636.dkr.ecr.us-west-2.amazonaws.com/tapdone3:latest```
