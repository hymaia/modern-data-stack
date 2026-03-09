with prs as (
    select * from {{ ref('stg_github__pull_requests') }}
),

     repos as (
         select * from {{ ref('dim_repositories') }}
     )

select
    pr.pr_id,
    pr.pr_number,
    pr.title,
    pr.state,
    pr.author_login,
    pr.is_merged,
    pr.hours_to_merge,
    cast(pr.created_at as timestamp)                as created_at,
    cast(pr.merged_at as timestamp)                 as merged_at,
    cast(pr.closed_at as timestamp)                 as closed_at,
    date_trunc('week', cast(pr.created_at as timestamp))    as created_week,
    date_trunc('month', cast(pr.created_at as timestamp))   as created_month,
    r.repository_id,
    r.repository_name,
    r.language
from prs pr
         left join repos r
                   on pr.repository_name = r.repository_name
