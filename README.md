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

https://us-west-2.console.aws.amazon.com/ecs/home?region=us-west-2#/repositories/tapdone3#images;tagStatus=ALL

1) Retrieve the docker login command that you can use to authenticate your Docker client to your registry:
```aws ecr get-login --region us-west-2```

2) Run the docker login command that was returned in the previous step.
3) Build your Docker image using the following command. For information on building a Docker file from scratch see the instructions here. You can skip this step if your image is already built:
```docker build -t tapdone3 .```

4) After the build completes, tag your image so you can push the image to this repository:
```docker tag tapdone3:latest 424467247636.dkr.ecr.us-west-2.amazonaws.com/tapdone3:latest```

5) Run the following command to push this image to your newly created AWS repository:
```docker push 424467247636.dkr.ecr.us-west-2.amazonaws.com/tapdone3:latest```
