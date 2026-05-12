# ADR-013: Aurora PostgreSQL Serverless v2 pour les bases des outils

## Statut
Accepté

## Contexte
Airbyte, Dagster et Metabase nécessitent chacun une base de données relationnelle pour
persister leur état applicatif (état des syncs, historique des runs, config BI…).
Il faut une solution managée, économique sur un environnement d'expérimentation, et
suffisamment proche d'une vraie production pour que l'expérience acquise soit transférable.

## Décision
Chaque outil dispose de son propre cluster Aurora PostgreSQL Serverless v2 (engine 16.4),
isolé dans le VPC privé du cluster EKS.

**Isolation par outil** : chaque base est indépendante — pas de couplage entre outils,
suppression ou migration facilitée, pattern proche de ce qu'on ferait en production.

**Scale-to-zero** (auto-pause après 360s d'inactivité, 0–2 ACU) : solution la moins
chère possible sur un environnement d'expérimentation. Le cold start n'est pas un
problème dans ce contexte — si ça l'était, on retirerait l'auto-pause au prix d'un
coût légèrement plus élevé.

L'objectif est d'expérimenter avec une solution robuste et proche de la prod pour
en tirer de l'expérience, pas de livrer un service haute disponibilité.

## Options considérées

| Option | Pour | Contre |
|--------|------|--------|
| **Aurora Serverless v2** ✅ | Managé, scale-to-zero, PostgreSQL compatible, proche prod | Cold start possible (acceptable ici), coût légèrement > RDS standard à charge constante |
| RDS PostgreSQL standard | Simple, prévisible | Toujours allumé = coût même à l'arrêt |
| PostgreSQL sur K8s (CloudNativePG) | Même cluster, contrôle total | Backup, HA et ops à gérer manuellement |
| SQLite (Metabase uniquement) | Zéro infra | Pas adapté multi-utilisateurs, non robuste |

## Conséquences

**Positives :** Coût minimal sur un environnement d'expérimentation (scale-to-zero).
Isolation totale entre outils. Pattern robuste et transférable en production réelle.
Zéro ops de maintenance (managé AWS).

**Compromis / Risques :** Cold start au réveil de l'instance (quelques secondes) — non
problématique pour des jobs batch mais à surveiller si un outil devient sensible aux
timeouts de connexion.
