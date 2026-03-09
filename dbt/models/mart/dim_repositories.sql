select
    repository_id,
    repository_name,
    full_name,
    description,
    language,
    stars_count,
    forks_count,
    open_issues_count,
    visibility,
    default_branch,
    created_at,
    updated_at
from {{ ref('stg_github__repositories') }}
