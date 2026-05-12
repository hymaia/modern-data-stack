# ADR-010: Spark Operator (Kubeflow) pour le traitement distribué

## Statut
Accepté

## Contexte
La plateforme doit illustrer comment déployer et exécuter un job de traitement distribué.
Spark est le framework de référence du marché pour ce type de workload — le montrer
sur la plateforme permet à n'importe quel développeur Hymaia de comprendre comment
structurer et lancer un job Spark dans cet environnement.

## Décision
Le Spark Operator (Kubeflow v2.4.0) est déployé sur EKS dans le namespace `spark-operator`.
Ce choix découle directement du parti pris Kubernetes (ADR-002) : puisque tout tourne
sur K8s, le Spark Operator est la façon naturelle de soumettre des jobs Spark sans
infrastructure séparée.

Le dossier `spark-vs-polars/` du repo constitue un exemple concret de job Spark sur
cette plateforme, illustrant comment structurer un projet (voir ADR-015).

À terme, chaque projet Spark devrait vivre dans son propre repo, indépendant du repo
de la data platform.

## Options considérées

| Option | Pour | Contre |
|--------|------|--------|
| **Spark Operator sur EKS** ✅ | Cohérent avec le parti pris K8s, pas d'infra séparée | Complexité K8s, pas managé |
| EMR on EKS | Managé AWS, optimisé Spark | Coût supplémentaire, moins générique |
| EMR Serverless | Vraiment serverless, managé | Lié à AWS, hors du cluster K8s |
| AWS Glue (ETL managé) | Serverless, zéro infra | Coût, moins de contrôle sur le runtime |

## Conséquences

**Positives :** Cohérent avec l'architecture K8s. Exemple concret et reproductible pour
les équipes Hymaia. Pas de coût d'infrastructure supplémentaire.

**Compromis / Risques :** Spark Operator ajoute de la complexité. Un node group dédié
est nécessaire pour les workloads intensifs (voir ADR-002). Pour les petits volumes,
Polars est plus adapté (voir ADR-011).
