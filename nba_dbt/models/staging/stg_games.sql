with source as (
    select * from {{ source('nba_raw', 'NBA_GAMES') }}
),

renamed as (
    select
        raw_data:id::integer              as game_id,
        raw_data:date::date               as game_date,
        raw_data:season::integer          as season,
        raw_data:status::text             as status,
        raw_data:postseason::boolean      as is_postseason,
        raw_data:home_team:id::integer    as home_team_id,
        raw_data:home_team_score::integer as home_team_score,
        raw_data:visitor_team:id::integer as visitor_team_id,
        raw_data:visitor_team_score::integer as visitor_team_score,
        case 
            when raw_data:home_team_score::integer > raw_data:visitor_team_score::integer 
            then raw_data:home_team:id::integer
            else raw_data:visitor_team:id::integer
        end                               as winning_team_id,
        _loaded_at
    from source
    where raw_data:status::text = 'Final'
)

select * from renamed