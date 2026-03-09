-- Ce test échoue si des commits pointent vers un repo inexistant
select *
from {{ ref('fct_commits') }}
where repository_id is null
