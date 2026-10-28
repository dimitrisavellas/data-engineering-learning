Commands learned:

1) docker run: an instance of the docker image is created to create the container 

`flags` : -it for interactive terminal 
         
2) docker ps : to inspect what is running 

`flags` : -a to see all docker images we executed 
          -aq to see their ids 

docker rm `docker ps -aq` : deletes all containers corresponding to those ids 

How we preserve the state ? -> Volumes 

docker run -it \
    --rm \  # deletes container after exiting 
    -v $(pwd)/test:/app/test \    # left from : is the host machine path, right is the mapping into the container path 
    --entrypoint=bash \  # a flag we use so we get bash commands for flexibility instead of being dropped directly in python 
    python:3.13.11-slim   # to have python intalled everytime (slim so it doesnt take ages)