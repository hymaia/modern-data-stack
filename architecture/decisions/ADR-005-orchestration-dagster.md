# ADR-005: Dagster comme orchestrateur de pipelines

## Statut
Accepté

## Contexte
La plateforme a besoin d'un orchestrateur pour piloter les pipelines de données : jobs dbt,
jobs Polars, et potentiellement Spark ou des triggers Airbyte. Comme pour les autres outils,
le choix doit être représentatif du marché et servir de référence méthodologique pour
les projets clients Hymaia. L'outil doit aussi être suffisamment simple à déployer sur
Kubernetes pour ne pas alourdir inutilement la plateforme.

## Décision
Dagster (v1.12.17) est déployé sur EKS dans le namespace `dagster` comme orchestrateur central.

Choisi pour le découvrir et parce qu'il est plus simple à déployer qu'Airflow sur Kubernetes.
Comme tous les outils de la plateforme, il est interchangeable — un Airflow peut être déployé
à la place ou en parallèle si le besoin se présente.

Le code utilisateur est packagé dans des images ECR distinctes et déployé comme "code location"
indépendante du daemon Dagster (voir ADR-015 pour le pattern de structuration des projets).
L'état des runs est persisté dans Aurora PostgreSQL Serverless v2.

## Options considérées

| Option | Pour | Contre |
|--------|------|--------|
| **Dagster** ✅ | Asset-centric, lineage natif, plus simple à déployer sur K8s qu'Airflow, moderne | Moins mature qu'Airflow, écosystème plus petit |
| Apache Airflow | Standard historique, très large écosystème | DAG-centric, déploiement K8s plus complexe, UX plus daté |
| Prefect | Cloud-native, simple | Non évalué |
| Temporal | Très robuste pour les workflows génériques | Complexe, pas orienté data |

## Conséquences

**Positives :** Déploiement K8s simplifié. Approche asset-centric plus lisible pour les
pipelines data. Outil rencontré de plus en plus chez les clients. Pattern de projet
structuré autour de Dagster (voir ADR-015).

**Compromis / Risques :** Communauté plus petite qu'Airflow. Moins de ressources disponibles
en cas de problème complexe. Interchangeable par conception si Airflow s'avère nécessaire
chez un client.
