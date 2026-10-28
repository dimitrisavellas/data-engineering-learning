`01` Commands learned:

1) docker run: an instance of the docker image is created to create the container 

`flags` : -it for interactive terminal 
         
2) docker ps : to inspect what is running 

`flags` : -a to see all docker containers we executed, including stopped ones
          -aq to see their ids 

docker rm `docker ps -aq` : deletes all containers corresponding to those ids 

How we preserve the state ? -> Volumes 

docker run -it \
    --rm \  # deletes container after exiting 
    -v $(pwd)/test:/app/test \    # left from : is the host machine path, right is the mapping into the container path 
    --entrypoint=bash \  # a flag we use so we get bash commands for flexibility instead of being dropped directly in python 
    python:3.13.11-slim   # to have python intalled everytime (slim so it doesnt take ages)

`02` 

`02` Writing a Docker image (Dockerfile)

A Dockerfile is a recipe: each line is a step Docker runs to build the image.
The file must be named exactly `Dockerfile` (Linux is case-sensitive).

```dockerfile
# base image to build on top of
FROM python:3.13.10-slim

# copy the uv program from the official uv image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/

# folder inside the container where everything happens
WORKDIR /app

# so `python` uses the packages uv installs in /app/.venv
ENV PATH="/app/.venv/bin:$PATH" # Left of the : is the venv folder, /app/.venv/bin.
                                # Right of the : is $PATH, the container’s existing list of folders (/usr/local/bin:/usr/bin:/bin and so on).
                                # So the line means: “new PATH = venv folder, then all the old folders”.

# copy dependency files first (see caching below)
COPY "pyproject.toml" "uv.lock" ".python-version" ./

# install the exact versions from uv.lock
RUN uv sync --locked

# copy the script last
COPY pipeline.py pipeline.py

# what runs when the container starts
ENTRYPOINT ["python", "pipeline.py"]
```

Instructions:

1) FROM : the starting image
2) COPY : copies files from my folder into the image
3) WORKDIR : sets (and creates) the working folder inside the container
4) ENV : sets an environment variable
5) RUN : runs a command while building the image
6) ENTRYPOINT : the command that runs when the container starts

Why dependency files are copied before the script ?
-> Docker caches each step. If only `pipeline.py` changes, Docker reuses the
   cached `uv sync` step instead of reinstalling everything.

Build the image:

docker build -t test:pandas .

`flags` : -t name:tag for the image (tag defaults to `latest`)
          . is the build context: the only folder Docker can see. Every file
            in a COPY must be inside it.

Run it (arguments after the image name go to the script):

docker run -it --rm test:pandas 12

Rules learned the hard way (see debug.md):

1) the project's `.python-version` must match the Python in the FROM line
2) after any change to `pyproject.toml`, run `uv lock` before building
3) `--locked` stops the build if `uv.lock` doesn't match `pyproject.toml`
4) `.dockerignore` keeps files like `.venv` out of the build