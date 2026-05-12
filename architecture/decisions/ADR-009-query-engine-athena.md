# ADR-009: Amazon Athena comme moteur SQL interactif

## Statut
Accepté

## Contexte
La plateforme a besoin d'un moteur SQL pour exécuter les transformations dbt et les
requêtes BI de Metabase sur le Data Lake S3. Le moteur doit être disponible sans
infrastructure dédiée à opérer, pour rester cohérent avec l'approche coût/simplicité
de la plateforme.

## Décision
Amazon Athena (engine v3, basé sur Trino) est le moteur SQL serverless retenu.
C'est le choix par défaut sur AWS pour requêter S3 via le Glue Catalog — il s'est
imposé naturellement pour avancer vite plutôt que comme résultat d'une évaluation
comparative approfondie.

La méthodologie derrière (requêter un Data Lake via un moteur SQL découplé du stockage)
reste la même quel que soit l'outil. Un moteur alternatif (Trino self-hosted, DuckDB,
Redshift Spectrum) peut être substitué si le contexte client le nécessite.

Un workgroup dédié `hymaia-datalake-workgroup` centralise les métriques et les résultats
sont stockés dans `raw-athena-results` (TTL 30 jours).

## Options considérées

| Option | Pour | Contre |
|--------|------|--------|
| **Athena v3** ✅ | Serverless, pay-per-query, natif S3 + Glue, zéro infra | Coût au volume scanné (5$/TB), limitations SQL (pas d'UPDATE) |
| Trino self-hosted | Performances, contrôle, portable | Cluster à opérer sur K8s |
| Redshift Spectrum | Performances | Coût fixe, cluster Redshift nécessaire |
| DuckDB | Très rapide, zéro infra | Pas adapté aux requêtes multi-utilisateurs sur S3 à grande échelle |
| Spark SQL | Même infra, distribué | Latence de démarrage, pas serverless |

## Conséquences

**Positives :** Aucune infrastructure à opérer. Scaling automatique. Intégration native
avec Glue Catalog et S3. Compatible avec `dbt-athena` et le connecteur Metabase.

**Compromis / Risques :** Coût proportionnel au volume scanné — à optimiser via le
partitionnement et les formats colonaires (Parquet). Limitations SQL (pas d'UPDATE natif,
MERGE limité) héritées par dbt. Latence non adaptée aux requêtes temps-réel.
