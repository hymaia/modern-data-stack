with source as (
    select * from {{ source('github', 'repositories') }}
),

     renamed as (
         select
             id                                          as repository_id,
             name                                        as repository_name,
             full_name,
             description,
    language,
    stargazers_count                            as stars_count,
    forks_count,
    open_issues_count,
    cast(created_at as timestamp)               as created_at,
    cast(updated_at as timestamp)               as updated_at,
    visibility,
    default_branch
from source
    )

select * from renamed
