with source as (
    select * from {{ source('github', 'issues') }}
),

     renamed as (
         select
             id                                                          as issue_id,
             number                                                      as issue_number,
             title,
             state,
             json_extract_scalar(user, '$.login')                       as author_login,
             user_id                                                     as author_id,
             created_at,
             closed_at,
             repository                                                  as repository_name,
             pull_request is not null                                    as is_pull_request
         from source
         where pull_request is null
     )

select * from renamed
