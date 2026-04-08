with stg_teams as (
    select * from {{ ref('stg_teams') }}
)

select
    team_id,
    team_name,
    full_name,
    abbreviation,
    city,
    conference,
    division
from stg_teams
