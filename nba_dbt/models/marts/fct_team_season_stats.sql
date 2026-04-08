with fct_games as (
    select * from {{ ref('fct_games') }}
),

dim_teams as (
    select * from {{ ref('dim_teams') }}
),

home_games as (
    select
        home_team_id                                    as team_id,
        season,
        count(*)                                        as home_games_played,
        sum(case when winning_team_id = home_team_id
            then 1 else 0 end)                          as home_wins,
        sum(case when winning_team_id != home_team_id
            then 1 else 0 end)                          as home_losses,
        avg(home_team_score)                            as avg_points_scored_home,
        avg(visitor_team_score)                         as avg_points_allowed_home
    from fct_games
    where is_postseason = false
    group by home_team_id, season
),

away_games as (
    select
        visitor_team_id                                 as team_id,
        season,
        count(*)                                        as away_games_played,
        sum(case when winning_team_id = visitor_team_id
            then 1 else 0 end)                          as away_wins,
        sum(case when winning_team_id != visitor_team_id
            then 1 else 0 end)                          as away_losses,
        avg(visitor_team_score)                         as avg_points_scored_away,
        avg(home_team_score)                            as avg_points_allowed_away
    from fct_games
    where is_postseason = false
    group by visitor_team_id, season
),

final as (
    select
        t.team_id,
        t.full_name                                     as team_name,
        t.abbreviation,
        t.conference,
        t.division,
        h.season,
        h.home_games_played + a.away_games_played       as total_games,
        h.home_wins + a.away_wins                       as total_wins,
        h.home_losses + a.away_losses                   as total_losses,
        round((h.home_wins + a.away_wins) /
            nullif(h.home_games_played + a.away_games_played, 0), 3)
                                                        as win_pct,
        h.home_wins,
        h.home_losses,
        a.away_wins,
        a.away_losses,
        round(h.avg_points_scored_home, 1)              as avg_points_scored_home,
        round(a.avg_points_scored_away, 1)              as avg_points_scored_away,
        round((h.avg_points_scored_home + a.avg_points_scored_away) / 2, 1)
                                                        as avg_points_scored,
        round((h.avg_points_allowed_home + a.avg_points_allowed_away) / 2, 1)
                                                        as avg_points_allowed
    from dim_teams t
    left join home_games h on t.team_id = h.team_id
    left join away_games a on t.team_id = a.team_id
)

select * from final