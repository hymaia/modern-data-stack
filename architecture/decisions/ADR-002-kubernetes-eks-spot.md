# ADR-002: EKS (Kubernetes) comme plateforme de déploiement, avec SPOT instances

## Statut
Accepté

## Contexte
Hymaia accompagne des clients avec des besoins data très variés. L'objectif de cette plateforme
est de constituer une **référence méthodologique** — comprendre les briques nécessaires à une
data platform, les problématiques à anticiper, les patterns à maîtriser — plutôt que de livrer
un produit figé sur un cloud donné.

Il fallait donc un runtime d'exécution suffisamment **générique** pour :
- héberger des outils hétérogènes (ingestion, orchestration, processing, BI)
- s'adapter à différents cloud providers selon le contexte client
- éviter le vendor lock-in sur la couche d'exécution, même si l'infra sous-jacente est AWS

## Décision
Tous les outils de la plateforme sont déployés sur un cluster EKS managé (Kubernetes 1.35).

**Kubernetes** est choisi comme couche d'exécution centrale car il est cloud-agnostique :
le cœur de la plateforme peut être transposé sur GKE, AKS ou un cluster on-premise sans
réécriture majeure. La méthodologie et les patterns restent valables quel que soit le provider.

**SPOT instances** sur les deux node groups pour réduire les coûts :
- **main** (`t3a/m5/m6 xlarge`, 0–5 nœuds) : outils et orchestration
- **spark** (`m5a/m6a/m6i 4xlarge`, 0–10 nœuds) : workloads distribués — ce node group
  illustre le pattern de création d'un pool dédié pour un besoin spécifique (benchmark sur
  ~10 milliards de lignes dans `spark-vs-polars`)

Le risque d'interruption SPOT est acceptable car :
- les jobs sont batch (déclenchés ~1 fois/jour), pas de processus long-lived
- les outils déployés (Airbyte, Dagster…) ont de la réplication intégrée
- un pool on-demand peut être créé ponctuellement si un workload critique l'exige

**Autoscaling schedulé** pour minimiser les coûts sur un environnement non-prod :
scale-up à 8h, scale-down à 19h (Europe/Paris). Les plages horaires sont ajustables selon
les besoins sans impact architectural.

## Options considérées

| Option | Pour | Contre |
|--------|------|--------|
| **EKS SPOT** ✅ | Cloud-agnostique, coût réduit, adapté aux jobs batch, réplication des outils | Complexité K8s, interruptions possibles |
| EKS On-Demand | Stabilité maximale | Coût 3× plus élevé pour un env non-prod |
| ECS Fargate | Serverless, simple à opérer | Vendor lock-in AWS, moins générique pour les clients Hymaia |
| EC2 standalone | Contrôle total | Ops lourd, pas de scheduling, pas portable |

## Conséquences

**Positives :** Plateforme portable — le cœur applicatif n'est pas lié à AWS. Pattern réutilisable
pour les clients Hymaia quel que soit leur cloud. Coût maîtrisé grâce aux SPOT + autoscaling.
Flexibilité pour créer des pools de nœuds spécialisés à la demande.

**Compromis / Risques :** Kubernetes ajoute une complexité opérationnelle non négligeable
(IRSA, namespaces, Helm, ArgoCD…). Les interruptions SPOT nécessitent que chaque outil
soit configuré avec des stratégies de retry/réplication adéquates.
