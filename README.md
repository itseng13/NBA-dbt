# NBA Analytics Pipeline

An end-to-end analytics engineering pipeline built to analyze NBA team performance across the 2024-25 regular season. This project demonstrates a production-style ELT architecture using Python, Snowflake, and dbt Core.

## Architecture

Data flows from the balldontlie REST API through three layers:

```
balldontlie API → Python ingestion → Snowflake RAW → dbt Staging → dbt Marts
```

**Raw layer:** Full JSON payloads loaded as VARIANT columns in Snowflake. No transformation — source data preserved exactly as received.

**Staging layer:** One model per source table. JSON unpacked, columns cast to appropriate types, renamed consistently, and filtered for data quality.

**Marts layer:** Business-ready dimension and fact tables built using Kimball dimensional modeling principles.

## DAG

<img width="1828" height="1588" alt="image" src="https://github.com/user-attachments/assets/b6c0c172-83d3-4253-ab50-498b10a8ea17" />

## Project Structure

```
nba_dbt/
├── models/
│   ├── staging/
│   │   ├── stg_teams.sql
│   │   ├── stg_players.sql
│   │   ├── stg_games.sql
│   │   └── schema.yml
│   └── marts/
│       ├── dim_teams.sql
│       ├── fct_games.sql
│       ├── fct_team_season_stats.sql
│       └── schema.yml
├── dbt_project.yml
└── load_raw.py
```

## Models

| Model | Layer | Description |
|---|---|---|
| `stg_teams` | Staging | 30 NBA teams with conference and division attributes |
| `stg_players` | Staging | Active players with team and draft information |
| `stg_games` | Staging | 2024-25 regular season and playoff game results |
| `dim_teams` | Marts | Team dimension table — one row per team |
| `fct_games` | Marts | Game-level fact table with scores, winning team, and point differential |
| `fct_team_season_stats` | Marts | Season-level team stats aggregated by home/away splits |

## Business Questions Answered

**Which teams had the best win percentage in the 2024-25 regular season?**
```sql
select team_name, total_wins, total_losses, win_pct
from fct_team_season_stats
order by win_pct desc
limit 10;
```

**How did home vs away performance compare by team?**
```sql
select
    team_name,
    home_wins,
    home_losses,
    away_wins,
    away_losses
from fct_team_season_stats
order by total_wins desc;
```

**Which conference scored more points on average?**
```sql
select
    conference,
    round(avg(avg_points_scored), 1) as avg_points_scored
from fct_team_season_stats
group by conference;
```

## Testing

24 data tests across all models including `unique`, `not_null`, `accepted_values`, and `relationships` tests.

```bash
dbt test
```

## Tech Stack

- **Ingestion:** Python (`requests`, `snowflake-connector-python`)
- **Warehouse:** Snowflake
- **Transformation:** dbt Core 1.11
- **Source API:** balldontlie.io (NBA stats)

## Setup

1. Clone the repo
2. Create a Snowflake account and run the setup SQL:
```sql
CREATE DATABASE NBA_DEV;
CREATE SCHEMA NBA_DEV.RAW;
CREATE SCHEMA NBA_DEV.STAGING;
CREATE SCHEMA NBA_DEV.MARTS;
```
3. Create a `.env` file with your credentials (see `.env.example`)
4. Install dependencies: `pip3 install requests snowflake-connector-python python-dotenv dbt-snowflake`
5. Run ingestion: `python3 load_raw.py`
6. Run dbt: `dbt run && dbt test`
