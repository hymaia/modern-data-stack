# ADR-016: Isolation de la donnée sensible par préfixe S3 et base Glue dédiée

## Statut
Proposé

## Contexte
La plateforme stocke actuellement toute la donnée dans trois buckets partagés
(`raw`, `staging`, `mart`) accessibles par défaut à tous les outils via leurs
rôles IRSA. Il n'existe pas de mécanisme empêchant un outil ou un rôle de lire
une donnée sensible déposée dans ces buckets.

L'intégration de données RH (paie des employés, taux journaliers des consultants)
nécessite une séparation stricte : ces données ne doivent être accessibles qu'à
une liste nommée de personnes et de jobs, avec un audit complet de chaque accès.

La question principale est : faut-il un bucket S3 séparé ou un préfixe dédié
dans le bucket `mart` existant ?

## Décision
La donnée sensible est isolée dans un **préfixe dédié** du bucket mart existant :
`s3://hymaia-datalake-mart/sensitive/` plutôt que dans un bucket séparé.

Une **base Glue dédiée** (`sensitive_mart`) est créée pour les tables sensibles,
distincte de `hymaia_datalake_mart`.

Le rôle IAM `athena_user_role` (actuellement trop permissif) est modifié pour
**retirer explicitement** `s3:GetObject` sur le préfixe `sensitive/*`.

## Options considérées

| Option | Pour | Contre |
|--------|------|--------|
| **Préfixe dédié dans bucket existant** ✅ | Moins d'infra à gérer, IAM par préfixe suffisant pour le contrôle d'accès | Clé KMS partagée avec la donnée non-sensible, vigilance accrue sur les wildcards IAM |
| Bucket S3 séparé | Isolation physique totale, clé KMS dédiée, surface d'erreur réduite | Un bucket supplémentaire à gérer, configuration Terraform plus lourde |

## Conséquences

**Positives :** Pas de nouveau bucket à provisionner. L'isolation est assurée
par les policies IAM sur le préfixe — suffisant pour le cas d'usage Hymaia.
La base Glue `sensitive_mart` garantit que les outils qui énumèrent les tables
(Metabase, Athena console) ne voient pas les tables sensibles sans permission explicite.

**Compromis / Risques :** La clé de chiffrement est partagée entre donnée publique
et sensible (AES-256 SSE-S3). Si une granularité de chiffrement par dataset est
requise à l'avenir, une migration vers SSE-KMS avec clé dédiée sera nécessaire.
Un wildcard mal écrit dans une policy IAM peut accidentellement exposer le préfixe
sensible — la revue des policies IAM touchant au bucket `mart` devient critique.
