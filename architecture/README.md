# Modern Data Platform — Documentation architecture

> Ce document s'adresse à toute personne souhaitant comprendre l'esprit de cette data platform,
> apprendre à l'utiliser, ou s'en inspirer pour un projet client chez Hymaia.

---

## Philosophie

**La méthodologie prime sur l'outil.**

Cette plateforme n'est pas un produit livrable figé. C'est une **référence méthodologique** :
elle modélise ce à quoi il faut penser pour construire une data platform moderne —
l'ingestion, le stockage, la transformation, l'orchestration, la restitution, la sécurité,
le déploiement — en utilisant des outils populaires et représentatifs du marché.

Chaque outil choisi peut être remplacé. Ce qui compte, c'est de comprendre **pourquoi**
il est là, **quel problème** il résout, et **comment** le remplacer si le contexte client
l'exige.

La couche d'exécution est Kubernetes — cloud-agnostique par conception. L'infra sous-jacente
est AWS, mais le cœur applicatif peut être transposé sur GCP, Azure ou on-premise.

---

## Vue d'ensemble

```
Sources externes
      │
      ▼
┌─────────────┐     ┌─────────────────────────────────────────┐
│   Airbyte   │────▶│  S3 raw  ──▶  S3 staging  ──▶  S3 mart  │
│ (ingestion) │     │         Glue Catalog (métadonnées)      │
└─────────────┘     └─────────────────────────────────────────┘
                              │               │
                    ┌─────────┘               └──────────┐
                    ▼                                     ▼
             ┌─────────────┐                       ┌──────────────┐
             │   Dagster   │                       │    Athena    │
             │(orchestrat.)│                       │ (moteur SQL) │
             └─────┬───────┘                       └─────┬────────┘
                   │                                     │
            ┌──────┴──────┐                             ▼
            ▼             ▼                       ┌────────────┐
          dbt           Spark                     │  Metabase  │
       (SQL mart)     / Polars                    │    (BI)    │
                    (processing)                  └────────────┘
```

Tout est déployé sur **EKS** via **ArgoCD** (GitOps) depuis ce repo GitHub.
Les secrets transitent par **AWS Secrets Manager** → **External Secrets Operator** → K8s Secrets.

---

## Les couches de la plateforme

### 1. Ingestion — Airbyte
Connecte des sources externes (bases de données, APIs, SaaS) vers la couche `raw` du Data Lake.
300+ connecteurs disponibles. Les modalités (full refresh vs incremental, format) dépendent
du connecteur et du besoin projet.

### 2. Data Lake — S3 + Glue Catalog
Architecture **Médaillon** en 3 couches S3, toutes chiffrées et versionnées :

| Couche | Bucket | Contenu |
|--------|--------|---------|
| **raw** | `hymaia-datalake-raw` | Données brutes telles que reçues des sources |
| **staging** | `hymaia-datalake-staging` | Données nettoyées, typées, conformées |
| **mart** | `hymaia-datalake-mart` | Agrégats métier prêts pour la BI |

Le **Glue Catalog** enregistre les schémas de chaque couche — tous les outils s'y réfèrent
pour découvrir les tables sans connaître les chemins S3.

### 3. Transformation — dbt
Transforme les données de `staging` vers `mart` via des modèles SQL, exécutés sur
**Amazon Athena**. dbt apporte les tests, la documentation et le lineage sur les modèles.

### 4. Processing — Spark / Polars
Pour les traitements nécessitant plus que du SQL :
- **Spark Operator** pour les volumes distribués (node group dédié sur SPOT)
- **Polars** pour les volumes intermédiaires en single-node (plus simple, plus rapide à démarrer)

### 5. Orchestration — Dagster
Orchestre l'ensemble des pipelines (dbt, Polars, Spark). Chaque projet est packagé dans
une image Docker déployée comme **code location** indépendante — ce qui permet de mettre
à jour un projet sans toucher aux autres ni au daemon Dagster.

### 6. Restitution — Metabase
Interface BI connectée à Athena pour explorer les données de la couche `mart`.
*Outil intermédiaire — la cible à terme est un outil conversationnel basé sur LLM.*

### 7. Déploiement — ArgoCD (GitOps)
Chaque outil est décrit comme une `Application` ArgoCD pointant sur `apps/<outil>/`
dans ce repo. ArgoCD garantit que l'état du cluster correspond en permanence à ce qui
est dans Git (`selfHeal: true`). Toute modification passe par une PR.

### 8. Sécurité — External Secrets Operator + IRSA
- Les secrets (mots de passe, tokens) sont stockés dans **AWS Secrets Manager** et jamais
  en clair dans Git ni dans les manifests K8s.
- Chaque outil dispose d'un **rôle IAM dédié via IRSA** avec les permissions minimales
  nécessaires — pas de credentials AWS partagés.

---

## Démarrer un projet ETL sur cette plateforme

La plateforme propose un **template de projet** à 3 dossiers :

```
mon-projet-etl/
├── infra/          # Terraform : ressources AWS spécifiques au projet (IRSA, ECR…)
├── orchestration/  # Code Dagster : assets, jobs, schedules → image ECR
└── <stack>/        # Code métier selon la stack choisie → image ECR
```

**Stacks disponibles :**
- `dbt + Athena` orchestré par Dagster → voir [`dbt/`](../dbt/) + [`orchestration-dagster/`](../orchestration-dagster/)
- `Spark` orchestré par Dagster → voir [`spark-vs-polars/`](../spark-vs-polars/)
- `Polars` orchestré par Dagster → voir [`spark-vs-polars/`](../spark-vs-polars/)

> **Note :** ces exemples sont actuellement dans ce repo pour faciliter l'exploration.
> L'organisation cible est **1 repo par projet**, indépendant de ce repo plateforme.

---

## Décisions d'architecture (ADRs)

Les choix techniques sont documentés sous forme d'**ADRs** (Architecture Decision Records)
dans [`decisions/`](./decisions/). Chaque ADR décrit le contexte, la décision, les alternatives
évaluées et les conséquences.

| ADR                                                                                     | Décision                                                               |
|-----------------------------------------------------------------------------------------|------------------------------------------------------------------------|
| [ADR-001](./decisions/ADR-001-cloud-provider.md)                                        | AWS comme cloud provider, région `eu-west-1`                           |
| [ADR-002](./decisions/ADR-002-kubernetes-eks-spot.md)                                   | EKS + SPOT instances comme plateforme de déploiement                   |
| [ADR-003](./decisions/ADR-003-gitops-argocd.md)                                         | ArgoCD pour le déploiement GitOps                                      |
| [ADR-004](./decisions/ADR-004-ingestion-airbyte.md)                                     | Airbyte pour l'ingestion                                               |
| [ADR-005](./decisions/ADR-005-orchestration-dagster.md)                                 | Dagster comme orchestrateur                                            |
| [ADR-006](./decisions/ADR-006-transformation-dbt.md)                                    | dbt pour les transformations SQL                                       |
| [ADR-007](./decisions/ADR-007-datalake-medallion-s3.md)                                 | Architecture Médaillon sur S3                                          |
| [ADR-008](./decisions/ADR-008-metastore-glue-catalog.md)                                | AWS Glue Catalog comme metastore                                       |
| [ADR-009](./decisions/ADR-009-query-engine-athena.md)                                   | Amazon Athena comme moteur SQL                                         |
| [ADR-010](./decisions/ADR-010-processing-spark-operator.md)                             | Spark Operator pour le traitement distribué                            |
| [ADR-011](./decisions/ADR-011-processing-polars.md)                                     | Polars pour les volumes intermédiaires                                 |
| [ADR-012](./decisions/ADR-012-bi-metabase.md)                                           | Metabase pour la BI (évolution LLM prévue)                             |
| [ADR-013](./decisions/ADR-013-aurora-postgresql-serverless.md)                          | Aurora PostgreSQL Serverless v2 pour les outils                        |
| [ADR-014](./decisions/ADR-014-secrets-external-secrets-operator.md)                     | External Secrets Operator pour les secrets                             |
| [ADR-015](./decisions/ADR-015-project-template-dagster-code-location.md)                | Template projet ETL + organisation multi-repo                          |
| [ADR-016](./decisions/ADR-016-sensitive-data-s3-prefix-isolation.md)                    | Isolation de la donnée sensible par préfixe S3 et base Glue dédiée     |
| [ADR-017](./decisions/ADR-017-sensitive-data-athena-workgroup-as-single-entry-point.md) | Athena workgroup dédié comme point d'accès unique à la donnée sensible |
| [ADR-018](./decisions/ADR-018-sensitive-data-irsa-job-vs-human-role.md)                 | Séparation stricte entre rôle IRSA des jobs et rôle humain SSO         |
| [ADR-019](./decisions/ADR-019-sensitive-data-schema-contract-dbt.md)                    | Contrat de schéma public via dbt pour les données sensibles            |
| [ADR-020](./decisions/ADR-020-sensitive-data-synthetic-data-for-dev.md)                 | Données synthétiques générées par Dagster pour le développement        |
| [ADR-021](./decisions/ADR-021-nl-query-nao-as-nl-sql-tool.md)                           | Nao comme outil de requêtes en langage naturel (NL→SQL sur Athena)     |
| [ADR-022](./decisions/ADR-022-nl-query-dbt-persist-docs-glue-enrichment.md)             | dbt persist_docs pour enrichir le Glue Catalog comme contexte pour Nao |
| [ADR-023](./decisions/ADR-023-nl-query-dbt-metricflow-semantic-models.md)               | dbt MetricFlow pour la définition des métriques métier                 |

---

## Objectifs à venir

La plateforme actuelle couvre l'ingestion, la transformation, l'orchestration et la
restitution de **données non-sensibles**, accessibles par défaut à tous les collaborateurs.
Deux axes d'évolution majeurs sont documentés sous forme de feuilles de route progressives,
dans l'esprit du manga *Dr. Stone* : chaque niveau est autonome et déployable en production
indépendamment du suivant.

### 🗣️ Requêtes en langage naturel — [nl-query-architecture.md](./nl-query-architecture.md)

Permettre à n'importe quel collaborateur d'interroger la donnée en français, sans SQL,
sans formation technique. La feuille de route s'articule en 5 niveaux :

| Niveau                  | Nom                             | Résultat                                                |
|-------------------------|---------------------------------|---------------------------------------------------------|
| **1 — La Torche**       | Premier dialogue avec la donnée | Nao connecté à Athena — NL→SQL opérationnel             |
| **2 — Le Feu Maîtrisé** | Enrichissement du vocabulaire   | dbt `persist_docs` → Glue enrichi → meilleures réponses |
| **3 — La Forge**        | Métriques cohérentes            | dbt MetricFlow — "CA" a une seule définition            |
| **4 — L'Acier**         | Semantic layer API              | Cube.dev sur EKS — métriques exposées en API            |
| **5 — L'Armure**        | Mémoire conversationnelle       | pgvector + RAG — la plateforme se souvient              |

Décisions associées : [ADR-021](./decisions/ADR-021-nl-query-nao-as-nl-sql-tool.md),
[ADR-022](./decisions/ADR-022-nl-query-dbt-persist-docs-glue-enrichment.md),
[ADR-023](./decisions/ADR-023-nl-query-dbt-metricflow-semantic-models.md).

### 🔐 Ingestion de données sensibles — [sensitive-data-access.md](./sensitive-data-access.md)

Intégrer dans la plateforme des données à accès restreint (paie, TJ, données RH),
accessibles uniquement aux personnes identifiées, avec traçabilité complète et
sans fuite possible via les jobs de traitement. La feuille de route s'articule
en 4 niveaux :

| Niveau                | Nom                             | Résultat                                                                        |
|-----------------------|---------------------------------|---------------------------------------------------------------------------------|
| **1 — La Frontière**  | Isolation des données sensibles | Préfixe S3 dédié + base Glue séparée + accès Athena bloqué par défaut           |
| **2 — Les Deux Clés** | Séparation humains / machines   | IRSA job ≠ rôle humain SSO — les jobs accèdent, les devs n'accèdent pas         |
| **3 — La Maquette**   | Développement sans accès réel   | Contrat de schéma dbt + données synthétiques dans un préfixe `sensitive_dev/`   |
| **4 — Les Clés**      | Auditabilité complète           | Chiffrement par préfixe + traçabilité de chaque accès dans `audit.read_actions` |

Décisions associées : [ADR-016](./decisions/ADR-016-sensitive-data-s3-prefix-isolation.md),
[ADR-017](./decisions/ADR-017-sensitive-data-athena-workgroup-as-single-entry-point.md),
[ADR-018](./decisions/ADR-018-sensitive-data-irsa-job-vs-human-role.md),
[ADR-019](./decisions/ADR-019-sensitive-data-schema-contract-dbt.md),
[ADR-020](./decisions/ADR-020-sensitive-data-synthetic-data-for-dev.md).

### Améliorations techniques en attente

- [ ] Extraire les projets exemples (`dbt/`, `spark-vs-polars/`, `orchestration-dagster/`)
      dans leurs propres repos selon le template ADR-015
- [ ] Rendre le repo générique (supprimer les valeurs personnelles : domaine `fcussac`,
      compte AWS individuel)
- [ ] Mettre en place une CI/CD pour le build des images ECR et le déploiement des code locations
