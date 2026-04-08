with stg_games as (
    select * from {{ ref('stg_games') }}
),

stg_teams as (
    select * from {{ ref('stg_teams') }}
),

final as (
    select
        g.game_id,
        g.game_date,
        g.season,
        g.is_postseason,
        g.home_team_id,
        ht.full_name                                    as home_team_name,
        g.home_team_score,
        g.visitor_team_id,
        vt.full_name                                    as visitor_team_name,
        g.visitor_team_score,
        g.winning_team_id,
        case
            when g.winning_team_id = g.home_team_id
            then 'home'
            else 'away'
        end                                             as winning_side,
        abs(g.home_team_score - g.visitor_team_score)  as point_differential
    from stg_games g
    left join stg_teams ht on g.home_team_id = ht.team_id
    left join stg_teams vt on g.visitor_team_id = vt.team_id
)

select * from final