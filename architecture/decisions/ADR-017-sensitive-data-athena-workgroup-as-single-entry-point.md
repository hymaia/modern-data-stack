# ADR-017: Athena workgroup dédié comme point d'accès unique à la donnée sensible

## Statut
Proposé

## Contexte
L'audit des accès à la donnée est assuré par le module `tracking-data-access`
(Terraform), qui log les requêtes Athena dans une table `audit.read_actions`.
Ce système couvre les requêtes passant par Athena, mais pas les accès S3 directs.

Or, le rôle `athena_user_role` accorde actuellement `s3:GetObject` sur tous les
buckets, y compris le préfixe `sensitive/` (ADR-016). Toute personne assumant ce
rôle peut lire les fichiers Parquet directement via le SDK AWS ou la console S3,
sans passer par Athena et sans laisser de trace dans l'audit.

Pour que l'audit existant soit réellement exhaustif sur la donnée sensible, il faut
que tout accès à cette donnée transite obligatoirement par Athena.

## Décision
Un **workgroup Athena dédié** (`sensitive-data`) est créé avec
`enforce_workgroup_configuration = true`. Toutes les requêtes sur `sensitive_mart`
doivent utiliser ce workgroup.

La **bucket policy** du préfixe `sensitive/` est modifiée pour n'autoriser
`s3:GetObject` qu'au service Athena (`Principal: athena.amazonaws.com`) et aux
rôles IRSA des jobs de traitement (Spark, Polars, dbt). Les rôles humains SSO
n'ont plus d'accès S3 direct sur ce préfixe.

Le module `tracking-data-access` existant est étendu pour couvrir le workgroup
`sensitive-data` — aucune modification du module, juste un second appel pointant
sur ce workgroup.

## Options considérées

| Option | Pour | Contre |
|--------|------|--------|
| **Workgroup Athena dédié + deny S3 direct** ✅ | Réutilise l'audit existant, zéro nouveau service, point de contrôle unique non contournable | Nécessite de modifier la bucket policy et le rôle IAM existant |
| CloudTrail data events sur S3 | Couvre aussi l'accès S3 direct | Génère un volume de logs important, plus coûteux, moins lisible que les logs Athena |
| AWS Lake Formation | Point de contrôle centralisé natif AWS | Lock-in AWS fort, complexité opérationnelle élevée, non retenu (voir sensitive-data-access.md) |

## Conséquences

**Positives :** L'audit `tracking-data-access` existant devient exhaustif sur la
donnée sensible dès lors que S3 direct est bloqué. Toute requête est tracée avec
l'identité SSO de l'appelant, le SQL exécuté et le timestamp. Aucun contournement
possible sans déclencher un `AccessDenied` loggé par CloudTrail.

**Compromis / Risques :** Les jobs de traitement (dbt, Spark, Polars) ont toujours
un accès S3 direct via leurs rôles IRSA — c'est intentionnel (voir ADR-018). Leur
accès n'est pas tracé via Athena mais via les logs Dagster et les runs Kubernetes.
L'accès S3 direct par les jobs est une surface d'audit plus faible que pour les
humains, acceptée en échange des performances de traitement.
