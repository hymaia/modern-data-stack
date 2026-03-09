with source as (
    select * from {{ source('github', 'commits') }}
),

     renamed as (
         select
             sha                                                                         as commit_sha,
             json_extract_scalar(commit, '$.author.name')                               as author_name,
             json_extract_scalar(commit, '$.author.email')                              as author_email,
             date_parse(
                     json_extract_scalar(commit, '$.author.date'),
                     '%Y-%m-%dT%H:%i:%SZ'
             )                                                                          as committed_at,
             json_extract_scalar(commit, '$.message')                                   as message,
             json_extract_scalar(author, '$.login')                                     as author_login,
             repository                                                                  as repository_name,
             html_url                                                                    as commit_url,
             branch                                                                      as branch
         from source
     )

select * from renamed
