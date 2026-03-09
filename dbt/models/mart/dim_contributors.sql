with commits as (
    select distinct
        author_login,
        author_name,
        author_email
    from {{ ref('stg_github__commits') }}
),

     prs as (
         select distinct
             author_login
         from {{ ref('stg_github__pull_requests') }}
     ),

     issues as (
         select distinct
             author_login
         from {{ ref('stg_github__issues') }}
     ),

     all_contributors as (
         select author_login from commits
         union
         select author_login from prs
         union
         select author_login from issues
     ),

     enriched as (
         select
             a.author_login                              as contributor_login,
             c.author_name,
             c.author_email,
             count(distinct cm.commit_sha)               as total_commits,
             count(distinct pr.pr_id)                    as total_prs,
             count(distinct i.issue_id)                  as total_issues_opened,
             min(cm.committed_at)                        as first_commit_at,
             max(cm.committed_at)                        as last_commit_at
         from all_contributors a
                  left join commits c
                            on a.author_login = c.author_login
                  left join {{ ref('stg_github__commits') }} cm
on a.author_login = cm.author_login
    left join {{ ref('stg_github__pull_requests') }} pr
    on a.author_login = pr.author_login
    left join {{ ref('stg_github__issues') }} i
    on a.author_login = i.author_login
group by 1, 2, 3
    )

select * from enriched
