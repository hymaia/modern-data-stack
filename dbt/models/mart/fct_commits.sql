with commits as (
    select * from {{ ref('stg_github__commits') }}
),

     repos as (
         select * from {{ ref('dim_repositories') }}
     ),

     contributors as (
         select * from {{ ref('dim_contributors') }}
     )

select
    c.commit_sha,
    c.committed_at,
    date_trunc('week', c.committed_at)              as committed_week,
    date_trunc('month', c.committed_at)             as committed_month,
    c.author_login,
    c.author_name,
    c.message,
    c.commit_url,
    r.repository_id,
    r.repository_name,
    r.language,
    r.stars_count,
    r.forks_count
from commits c
         left join repos r
                   on c.repository_name = r.repository_name
