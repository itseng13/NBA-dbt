with source as (
    select * from {{ source('nba_raw', 'NBA_PLAYERS') }}
),

renamed as (
    select
        raw_data:id::integer          as player_id,
        raw_data:first_name::text     as first_name,
        raw_data:last_name::text      as last_name,
        raw_data:position::text       as position,
        raw_data:height::text         as height,
        raw_data:weight::text         as weight,
        raw_data:jersey_number::text  as jersey_number,
        raw_data:college::text        as college,
        raw_data:country::text        as country,
        raw_data:draft_year::integer  as draft_year,
        raw_data:draft_round::integer as draft_round,
        raw_data:draft_number::integer as draft_number,
        raw_data:team:id::integer     as team_id,
        _loaded_at
    from source
)

select * from renamed