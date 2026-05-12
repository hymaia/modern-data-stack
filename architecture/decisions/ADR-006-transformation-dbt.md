# ADR-006: dbt pour les transformations de données

## Statut
Accepté

## Contexte
La plateforme a besoin d'un outil de transformation pour passer des données nettoyées
(staging) aux agrégats métier (mart). L'outil doit être représentatif des pratiques
du marché data et servir de référence pour les projets clients Hymaia.

## Décision
dbt est utilisé pour les transformations SQL, avec l'adaptateur **`dbt-athena`** qui
cible Amazon Athena comme moteur d'exécution — le choix naturel sur AWS pour requêter
S3 sans infrastructure dédiée.

Choisi pour le découvrir et pour sa forte adoption sur le marché data actuel.
Comme tous les outils de la plateforme, dbt est interchangeable : un autre moteur de
transformation peut être substitué si un projet client le nécessite.

dbt est orchestré par Dagster via une code location dédiée (voir ADR-015).

## Options considérées

| Option | Pour | Contre |
|--------|------|--------|
| **dbt (Athena adapter)** ✅ | Très populaire, SQL-first, tests et documentation natifs, lineage, largement adopté chez les clients | Limitations d'Athena (pas d'UPDATE natif, latence sur petits volumes) |
| Spark SQL (dans Spark Operator) | Même infra, distribué | Moins de tooling, pas de tests natifs, overkill pour du SQL |
| SQLMesh | Moderne, performant, compatible dbt | Moins mature, écosystème plus petit |
| Scripts Python custom | Flexibilité totale | Pas de contrat de données, pas de tests, maintenance élevée |

## Conséquences

**Positives :** Outil incontournable du marché data — le maîtriser sur cette plateforme
est directement transférable chez les clients. Tests, documentation et lineage intégrés
apportent une rigueur que les scripts custom ne peuvent pas offrir facilement.

**Compromis / Risques :** L'adaptateur `dbt-athena` hérite des limitations d'Athena
(absence d'UPDATE, MERGE limité, latence sur les petites requêtes). Ces contraintes sont
acceptées dans le contexte de cette plateforme — si un projet nécessite un moteur plus
capable (ex. Spark SQL, DuckDB), l'outil peut être remplacé sans remettre en cause
l'approche dbt elle-même.
