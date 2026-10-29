## IndexError on sys.argv[1] in pipeline.py  (01)
- **Error:** `IndexError: list index out of range` on `month = sys.argv[1]`
- **Checked:** the `Arguments:` print showed the list only contained the script path
- **Cause:** ran `uv run python pipeline.py` without passing a value, so `sys.argv` had only index 0
- **Fix:** pass the argument on the command line: `uv run python pipeline.py 12`
- **Lesson:** `sys.argv[0]` is always the script itself; anything typed after the script name starts at index 1, and every value arrives as a string


## Cause:           (02)
  
  1. The `.` in `docker build .` means "use only this folder". My `uv.lock` was in the main repo folder, so Docker couldn't see it.
  2. `uv init` connected this folder to the main repo project instead of making a separate one (it said so in its first output line), so no `.python-version` was created here.
  3. `pyproject.toml` had a `[build-system]` section, which tells uv the folder is a library. uv then looked for library code that doesn't exist.
  4. I changed `pyproject.toml` without running `uv lock`, so the lock file no longer matched, and `--locked` stopped the build.
- **Lesson:**
  - The Python version in `.python-version` must match the one in the Dockerfile's `FROM` line.

## Port 5432 already allocated  (03)
- **Error:** `Bind for 0.0.0.0:5432 failed: port is already allocated` when starting `pgdatabase`
- **Checked:** `docker ps` showed an older postgres container (`zen_spence`) still up on 5432
- **Cause:** I had started postgres earlier with `docker run -it ...` without `--name` and `--network`; it was still running, so the port was taken
- **Fix:** `docker stop zen_spence && docker rm zen_spence`, then start `pgdatabase` again
- **Lesson:** only one container can publish a host port. Also, two postgres servers must never use the same data folder at the same time


## Ingest container can't resolve 'pgdatabase'  (03)
- **Error:** `psycopg.OperationalError: failed to resolve host 'pgdatabase': [Errno -3] Temporary failure in name resolution`
- **Checked:** `docker network inspect pg-network --format '{{range .Containers}}{{.Name}} {{end}}'` printed nothing
- **Cause:** the ingest container was on pg-network, but `pgdatabase` never started (the port error above), so there was no container with that name on the network
- **Fix:** start `pgdatabase` with `--network=pg-network --name pgdatabase`, check it shows up in the network, then run the ingest again
- **Lesson:** a container name only works as a host name if that container is running on the SAME user-created network. From my machine use `localhost`, from another container use the container name


## Leftover stopped container after a failed ingest  (03)
- **Error:** `docker ps -a` showed `thirsty_chatelet` (taxi_ingest) `Exited (1)`
- **Cause:** ran the ingest with `docker run -it` without `--rm`, so the failed container stayed
- **Fix:** `docker rm thirsty_chatelet`
- **Lesson:** use `--rm` for one-off runs (ingest, checks). Without `--name`, Docker gives random names like `zen_spence`, which makes them easy to forget


## pgAdmin: "localhost:8085 can't be reached"  (03)
- **Error:** browser couldn't open http://localhost:8085 right after `docker run ... dpage/pgadmin4`
- **Checked:** `docker ps` showed pgadmin Up with `0.0.0.0:8085->80/tcp`; `docker logs pgadmin` showed it was still initialising
- **Cause:** on the first start pgAdmin builds its internal database (30-60 s) before the web server listens
- **Fix:** wait for `Listening at: http://[::]:80` in the logs, then reload (use http, not https)
- **Lesson:** "Up" in `docker ps` means the container runs, not that the app inside is ready -> check the logs


## pgAdmin: Servers list is empty  (03)
- **Error:** logged in to pgAdmin, but there was nothing under Servers to expand
- **Cause:** logging in to pgAdmin is not connecting to postgres; the server has to be registered
- **Fix:** right click Servers -> Register -> Server, host `pgdatabase`, port 5432, root/root
- **Lesson:** in pgAdmin the host is `pgdatabase`, never `localhost` (inside the pgAdmin container localhost is pgAdmin itself). Without `-v pgadmin_data:/var/lib/pgadmin` the registered server is lost on every restart


## COUNT(*) returned 1000000 instead of 1371708  (03)
- **Error:** `SELECT COUNT(*) FROM yellow_taxi_trips_2021_2` returned exactly 1000000
- **Cause:** I queried while the ingest was still running: it inserts 100000 rows per chunk, so it was 10 chunks in
- **Fix:** wait for `done ingesting to ...` and query again -> 1371708
- **Lesson:** a suspiciously round number = a chunked job that hasn't finished


## Two different databases: bind mount vs named volume  (03)
- **Error:** none, but `docker volume ls` showed a volume `ny_taxi_postgres_data` (~1 GB) that no container used
- **Checked:** volume created at 14:39, folder `./ny_taxi_postgres_data` at 11:37. Started the volume on another port (`-p 5433:5432 --name pgcheck`) and compared `\dt` and `COUNT(*)`: it had only 2 tables, both also in the folder
- **Cause:** during the day I ran postgres with both `-v $(pwd)/ny_taxi_postgres_data:...` (bind mount, folder) and `-v ny_taxi_postgres_data:...` (named volume). The only difference is the `$(pwd)/` / `./`, but they are two separate databases
- **Fix:** kept the folder (it had everything), `docker volume rm ny_taxi_postgres_data`
- **Lesson:** in `-v`, a path (starts with `./`, `/` or `$(pwd)/`) = folder on my disk; a plain name = Docker volume. In docker compose a named volume also gets the project prefix (`02-virtual-env-pipelines_...`), so it's yet another database
