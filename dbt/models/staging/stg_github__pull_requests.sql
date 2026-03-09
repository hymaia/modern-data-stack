with source as (
    select * from {{ source('github', 'pull_requests') }}
),

     renamed as (
         select
             id                                                          as pr_id,
             number                                                      as pr_number,
             title,
             state,
             json_extract_scalar(user, '$.login')                       as author_login,
             cast(created_at as timestamp)    as created_at,
             cast(updated_at as timestamp)    as updated_at,
             cast(closed_at as timestamp)     as closed_at,
             cast(merged_at as timestamp)     as merged_at,
             json_extract_scalar(base, '$.repo.name')                   as repository_name,
             merged_at is not null                                       as is_merged,
             date_diff('hour', created_at, merged_at)                   as hours_to_merge
         from source
     )

select * from renamed
