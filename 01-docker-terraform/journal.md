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

3) docker pull : downloads an image from Docker Hub without running it, e.g. docker pull ubuntu

no tag means :latest, so docker pull ubuntu = docker pull ubuntu:latest
docker run also pulls automatically if the image is not found locally

4) docker images : lists the images stored locally (name:tag, id, size)

images with the same layers are stored once, so the sizes in the list are not additive (docker system df shows the real total)

5) docker build : builds an image from the Dockerfile

`flags` : -t name:tag gives the image its name, e.g. docker build -t av:we .

the last argument is the build context: the folder whose files are sent to Docker for the build
. means the current folder, so we run the command from the folder that contains the Dockerfile
COPY can only see files inside the build context, which is why the lesson has its own uv project
docker run uses the name from -t, e.g. docker run -it --rm av:we 4 (a name that was never built gives "pull access denied")


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

docker build -t test:pandas(or any other name) .

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


`03` Postgres + pgAdmin + ingest container on one Docker network

Tutorial: https://github.com/alexeygrigorev/workshops/tree/main/dezoomcamp-docker
Folder: run EVERY command from `lessons/02-virtual-env-pipelines`
(the `$(pwd)/ny_taxi_postgres_data` path depends on it).

The goal: 3 containers that talk to each other.

```
                       pg-network
  ┌───────────────────────────────────────────────────────┐
  │  pgdatabase (postgres:18)   <── pgadmin (pgadmin4)    │
  │        ^                                              │
  │        └──────────────────── taxi_ingest:v001         │
  └───────────────────────────────────────────────────────┘
        ^ port 5432                ^ port 8085
        my machine (pgcli, jupyter, uv run ...)
```

Why a network ?
-> On the default `bridge` network containers can NOT find each other by name.
   On a network we create ourselves, every container can reach the others
   using their `--name` as the host name (Docker does the DNS).

The rule for `--pg-host` / "Host name" :

1) from MY MACHINE (pgcli, jupyter, `uv run python ingest_data.py`) -> `localhost`
   (it goes through `-p 5432:5432`)
2) from ANOTHER CONTAINER on pg-network (pgAdmin, taxi_ingest) -> `pgdatabase`
   (inside a container, `localhost` means the container itself, not Postgres)


Step 0 : clean start

docker ps -a                          # anything still running / stopped ?
docker stop <name>                    # stop any old postgres that holds port 5432
docker rm <name>                      # remove stopped leftovers

Only ONE postgres can use port 5432 and the `ny_taxi_postgres_data` folder at a time.


Step 1 : build the ingest image

The Dockerfile in this folder copies `ingest_data.py` and has
`ENTRYPOINT ["python", "ingest_data.py"]`, so arguments after the image name go to the script.

docker build -t taxi_ingest:v001 .

(after changing ingest_data.py or pyproject.toml -> `uv lock`, then build again)


Step 2 : create the network (only once, it stays until `docker network rm pg-network`)

docker network create pg-network
docker network ls                     # pg-network should be in the list

If it says "already exists" -> fine, skip.


Step 3 : start Postgres on the network   (terminal 1, leave it running)

```bash
docker run -it --rm \
  -e POSTGRES_USER="root" \
  -e POSTGRES_PASSWORD="root" \
  -e POSTGRES_DB="ny_taxi" \
  -v $(pwd)/ny_taxi_postgres_data:/var/lib/postgresql \
  -p 5432:5432 \
  --network=pg-network \
  --name pgdatabase \
  postgres:18
```

`flags` : -e                sets env variables: user, password and database that postgres creates
          -v                where the data is stored, so the tables survive when the container is deleted
                            (bind mount or named volume, see the comparison below)
          -p 5432:5432      host port : container port, so my machine can reach it as localhost:5432
          --network         joins pg-network
          --name pgdatabase the name other containers use as host name
          --rm              container is deleted on stop (the data is safe in the folder),
                            so the name `pgdatabase` is free again for the next run

Where the data lives : bind mount (what I use) vs named volume (what the tutorial uses)

The ONLY difference in the command is the `-v` line. The `./` (or `$(pwd)/`) makes it a folder path,
without it Docker treats the left side as a volume name.

| | A) bind mount (mine) | B) named volume (tutorial) |
|---|---|---|
| `-v` line | `-v $(pwd)/ny_taxi_postgres_data:/var/lib/postgresql` | `-v ny_taxi_postgres_data:/var/lib/postgresql` |
| left side is | a path to a folder | a name |
| data is stored in | ./ny_taxi_postgres_data, next to my code | a place Docker manages (/var/lib/docker/volumes/...) |
| see it with | `ls -la ny_taxi_postgres_data` | `docker volume ls` |
| tutorial says | "Direct mapping to host filesystem, more control" | "Managed by Docker, easier" |
| catch | on Linux the files are owned by root (I can't delete them without sudo) and they sit inside the repo -> must be in .gitignore (it is: `**/ny_taxi_postgres_data/`) | the data is not visible in my project folder |
| delete the data | `sudo rm -rf ny_taxi_postgres_data` | `docker volume rm ny_taxi_postgres_data` |
| docker-compose.yaml | `- "./ny_taxi_postgres_data:/var/lib/postgresql:rw"` (NOT listed under `volumes:` at the bottom) | `- "ny_taxi_postgres_data:/var/lib/postgresql:rw"` AND listed under `volumes:` at the bottom |

IMPORTANT: A and B are two DIFFERENT databases. My tables (yellow_taxi_trips_2021_1 / _2021_2)
are in A. Switching to B gives an EMPTY ny_taxi -> run the ingest (Step 6) again.
In docker compose, B also gets the project prefix: `02-virtual-env-pipelines_ny_taxi_postgres_data`,
so it is not even the same volume as the manual `docker run` with B.

pgAdmin (Step 4) always uses a named volume (`pgadmin_data`): there is no old data to keep, and
pgAdmin runs as user 5050 inside the container, so a folder created by Docker (owned by root)
would give "Permission denied".

Ready when the log says: `database system is ready to accept connections`

Check (terminal 2):

docker network inspect pg-network --format '{{range .Containers}}{{.Name}} {{end}}'
-> must print `pgdatabase`. If not, STOP here, nothing else will work.


Step 4 : start pgAdmin on the network   (terminal 2, leave it running)

```bash
docker run -it --rm \
  -e PGADMIN_DEFAULT_EMAIL="admin@admin.com" \
  -e PGADMIN_DEFAULT_PASSWORD="root" \
  -v pgadmin_data:/var/lib/pgadmin \
  -p 8085:80 \
  --network=pg-network \
  --name pgadmin \
  dpage/pgadmin4
```

`flags` : -e        the login for the pgAdmin website (NOT the postgres login)
          -v        named volume: pgAdmin remembers the login and the registered server.
                    Without it, the server has to be registered again after every restart.
          -p 8085:80 pgAdmin listens on 80 inside, I open 8085 in the browser

The first start takes 30-60 s. Ready when the log says: `Listening at: http://[::]:80`
Opening the browser before that -> "this site can't be reached". Just wait and reload.


Step 5 : connect pgAdmin to Postgres (in the browser)

1) open http://localhost:8085  (http, not https)
2) log in : admin@admin.com / root
3) the Servers list is EMPTY: logging in to pgAdmin does not connect it to any database yet
4) right click Servers -> Register -> Server...
   General tab    : Name = Local Docker   (only a label)
   Connection tab : Host name/address = pgdatabase
                    Port                = 5432
                    Maintenance db      = ny_taxi
                    Username            = root
                    Password            = root
                    Save password       = on
   -> Save
5) browse : Local Docker -> Databases -> ny_taxi -> Schemas -> public -> Tables
6) run SQL : right click ny_taxi -> Query Tool

```sql
SELECT COUNT(*) FROM yellow_taxi_trips_2021_1;
SELECT * FROM yellow_taxi_trips_2021_1 LIMIT 10;
```

New tables do not show up by themselves -> right click Tables -> Refresh.


Step 6 : run the ingest as a container   (terminal 3)

```bash
docker run -it --rm \
  --network=pg-network \
  taxi_ingest:v001 \
    --pg-user=root \
    --pg-pass=root \
    --pg-host=pgdatabase \
    --pg-port=5432 \
    --pg-db=ny_taxi \
    --target-table=yellow_taxi_trips_2021_2 \
    --year=2021 \
    --month=2 \
    --chunksize=100000
```

Everything BEFORE `taxi_ingest:v001` is for docker, everything AFTER goes to ingest_data.py.
`--rm` so a finished/failed run does not leave a stopped container behind.

Output: `Table yellow_taxi_trips_2021_2 created` ... `done ingesting to yellow_taxi_trips_2021_2` (~2 min)

Check in pgAdmin (Query Tool):

SELECT COUNT(*) FROM yellow_taxi_trips_2021_2;     -> 1371708   (query only after `done ingesting`)

Same script from my machine instead of Docker (no network needed, host is localhost):

uv run python ingest_data.py --pg-host=localhost --target-table=yellow_taxi_trips_2021_1 --year=2021 --month=1

Or connect with pgcli from my machine:

uv run pgcli -h localhost -p 5432 -u root -d ny_taxi      # \dt lists the tables


Step 7 : stop everything

Ctrl+C in terminals 1 and 2, or:

docker stop pgdatabase pgadmin

Both were started with `--rm`, so they are also deleted. The data stays in
./ny_taxi_postgres_data (or the ny_taxi_postgres_data volume with option B) and in the pgadmin_data volume. To start again -> Step 3 and Step 4
(Steps 1 and 2 only when the image changed / the network was removed).


Errors I hit in this part (port taken, name not resolved, pgAdmin not reachable, ...) -> see debug.md (03)