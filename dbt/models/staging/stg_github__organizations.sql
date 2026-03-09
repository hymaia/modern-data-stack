with source as (
    select * from {{ source('github', 'organizations') }}
),

     renamed as (
         select
             id                                          as organization_id,
             login                                       as organization_login,
             description,
             public_repos,
             followers,
             cast(created_at as timestamp)               as created_at
         from source
     )

select * from renamed
