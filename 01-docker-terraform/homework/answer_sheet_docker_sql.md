## Question 1. Understanding Docker images

Run docker with the `python:3.13` image. Use an entrypoint `bash` to interact with the container.

- I run : 

docker run -it --rm \
-v $(pwd)/test:/app/test \
--entrypoint=bash \
python:3.13`

Then: 

pip --version --> pip `26.2.2` 


## Question 2. Understanding Docker networking and docker-compose

Given the following `docker-compose.yaml`, what is the `hostname` and `port` that pgadmin should use to connect to the postgres database?

```yaml
services:
  db:
    container_name: postgres
    image: postgres:17-alpine
    environment:
      POSTGRES_USER: 'postgres'
      POSTGRES_PASSWORD: 'postgres'
      POSTGRES_DB: 'ny_taxi'
    ports:
      - '5433:5432'
    volumes:
      - vol-pgdata:/var/lib/postgresql/data

  pgadmin:
    container_name: pgadmin
    image: dpage/pgadmin4:latest
    environment:
      PGADMIN_DEFAULT_EMAIL: "pgadmin@pgadmin.com"
      PGADMIN_DEFAULT_PASSWORD: "pgadmin"
    ports:
      - "8080:80"
    volumes:
      - vol-pgadmin_data:/var/lib/pgadmin

volumes:
  vol-pgdata:
    name: vol-pgdata
  vol-pgadmin_data:
    name: vol-pgadmin_data
```

- postgres:5433
- localhost:5432
- db:5433
- postgres:5432
- db:5432

The correct answers are :
- `postgres:5432`
- `db:5432 `

# Explanation: 

port 5433 on my laptop forwards to port 5432 inside the container.
From my laptop (pgcli, DBeaver): I can go through the host mapping, so I use localhost:5433.


## Question 3. Counting short trips

For the trips in November 2025 (lpep_pickup_datetime between '2025-11-01' and '2025-12-01', exclusive of the upper bound), how many trips had a `trip_distance` of less than or equal to 1 mile?

- 7,853
- 8,007
- 8,254
- 8,421

Correct answer is : `8007`
solution: 

` SELECT COUNT(*)
 FROM green_taxi_trips
 WHERE lpep_pickup_datetime >= '2025-11-01'
   AND lpep_pickup_datetime < '2025-12-01'
   AND trip_distance <= 1;`


## Question 4. Longest trip for each day

Which was the pick up day with the longest trip distance? Only consider trips with `trip_distance` less than 100 miles (to exclude data errors).

Use the pick up time for your calculations.

- 2025-11-14
- 2025-11-20
- 2025-11-23
- 2025-11-25

Correct answer : `2025-11-14`
solution: 

`SELECT lpep_pickup_datetime::date AS pickup_day
 FROM green_taxi_trips
 WHERE trip_distance < 100
 ORDER BY trip_distance DESC
 LIMIT 1;`

## Question 5. Biggest pickup zone

Which was the pickup zone with the largest `total_amount` (sum of all trips) on November 18th, 2025?

- East Harlem North
- East Harlem South
- Morningside Heights
- Forest Hills

Correct answer : `East Harlem North`
solution: 

`select z."Zone", sum(t.total_amount) as total
   from green_taxi_trips t
   join zones z on t."PULocationID" = z."LocationID"
   where t.lpep_pickup_datetime::date = '2025-11-18'
   group by z."Zone"
   order by total desc limit 1;`

## Question 6. Largest tip

For the passengers picked up in the zone named "East Harlem North" in November 2025, which was the drop off zone that had the largest tip?

Note: it's `tip` , not `trip`. We need the name of the zone, not the ID.

- JFK Airport
- Yorkville West
- East Harlem North
- LaGuardia Airport

Correct answer : `Yorkville West`
solution: 

`SELECT zdo."Zone" AS dropoff_zone, MAX(t.tip_amount) AS tip
 FROM green_taxi_trips t
 JOIN zones zpu ON t."PULocationID" = zpu."LocationID"
 JOIN zones zdo ON t."DOLocationID" = zdo."LocationID"
 WHERE t.lpep_pickup_datetime >= '2025-11-01'
   AND t.lpep_pickup_datetime < '2025-12-01'
   AND zpu."Zone" = 'East Harlem North'
 GROUP BY zdo."Zone"
 ORDER BY tip DESC
 LIMIT 1;`