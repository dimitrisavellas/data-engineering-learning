# Data Engineering Zoomcamp

My notes, experiments, and homework for the
[DataTalks.Club Data Engineering Zoomcamp](https://github.com/DataTalksClub/data-engineering-zoomcamp),
done self-paced on a Linux (Ubuntu) machine.

## Progress

- [ ] 01 Docker & Terraform
- [ ] 02 Workflow Orchestration
- [ ] 03 Data Warehouse
- [ ] 04 Analytics Engineering
- [ ] 05 Data Platforms
- [ ] 06 Batch Processing
- [ ] 07 Streaming
- [ ] Capstone project

## Structure

Each module folder contains:

- `lessons/`: code from the lectures and my own experiments based on them
- `homework/`: completed homework
- `journal.md`: notes and observations
- `debug.md`: problems I hit, their cause, and the fix

`patterns.md` at the root collects lessons that repeat across modules.

## Setup

Python environment is managed with [uv](https://docs.astral.sh/uv/).

```bash
uv sync                  # base dependencies
uv sync --group <name>   # extra dependencies for a specific module
```

Services like Postgres, Kestra, and Kafka run in Docker.

## Workflow

One branch per module, merged into `main` through a pull request.
CI checks Python (ruff) and Terraform formatting on every PR.
