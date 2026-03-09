-- Ce test échoue si une PR a une date de merge antérieure à sa création
select *
from {{ ref('stg_github__pull_requests') }}
where is_merged = true
  and merged_at < created_at
