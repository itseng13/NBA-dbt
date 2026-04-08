with source AS (
        SELECT *
        FROM {{source('nba_raw', 'NBA_TEAMS')}}
),

renamed AS (
    SELECT 
        raw_data:id::int AS team_id,
        raw_data:abbreviation::text AS abbreviation,
        raw_data:city::text          as city,
        raw_data:conference::text    as conference,
        raw_data:division::text      as division,
        raw_data:full_name::text     as full_name,
        raw_data:name::text          as team_name,
        _loaded_at
    FROM source
)

select * 
from renamed
where team_id is not null
    and len(trim(conference)) > 0
