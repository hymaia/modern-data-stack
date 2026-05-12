# ADR-008: AWS Glue Catalog comme metastore

## Statut
Accepté

## Contexte
Le Data Lake S3 a besoin d'un catalogue de métadonnées pour que les outils (Airbyte, Spark,
dbt, Metabase) puissent découvrir et requêter les tables sans connaître les chemins S3
sous-jacents. Un catalogue commun garantit la cohérence des schémas entre les couches.

## Décision
AWS Glue Catalog est utilisé comme catalogue de métadonnées central pour les 3 couches
du Data Lake. C'est le choix par défaut sur AWS lorsqu'on utilise Athena — il s'est
imposé naturellement pour avancer vite plutôt que comme résultat d'une évaluation
comparative approfondie.

Trois databases sont créées (`hymaia_datalake_raw`, `_staging`, `_mart`), accessibles
par tous les outils via des politiques IRSA dédiées.

Comme pour l'ensemble des outils de la plateforme, ce qui compte est la méthodologie
derrière l'usage d'un catalogue (schéma, discovery, gouvernance) — un autre catalogue
(Hive Metastore, Unity Catalog…) peut être substitué si le contexte client le requiert.

## Options considérées

| Option | Pour | Contre |
|--------|------|--------|
| **Glue Catalog** ✅ | Natif AWS, intégré Athena/Spark/Airbyte, serverless, zéro ops | Lié à AWS, fonctionnalités de gouvernance limitées |
| Apache Hive Metastore | Standard OSS, portable | Serveur à opérer sur K8s |
| Unity Catalog (Databricks) | Gouvernance fine, lineage | Vendor lock-in Databricks |
| Pas de catalogue | Simplicité | Pas de découvrabilité, couplage sur les chemins S3 |

## Conséquences

**Positives :** Zéro infrastructure à opérer. Intégration native avec Athena, Spark et
les outils AWS. Découvrabilité immédiate des tables entre couches.

**Compromis / Risques :** Couplage au provider AWS (contrairement à Hive Metastore qui
est portable). Les fonctionnalités de gouvernance avancée (data contracts, fine-grained
access control) nécessiteraient un outil complémentaire.
