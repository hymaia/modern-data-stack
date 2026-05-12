# ADR-021: Nao comme outil de requêtes en langage naturel

## Statut
Proposé

## Contexte
La plateforme expose la donnée via Athena et Metabase. Ces deux outils requièrent
une connaissance du SQL ou de l'interface Metabase — ils ne sont pas accessibles
aux collaborateurs non-techniques d'Hymaia (managers, équipes métier, RH, commerce).

L'objectif est de permettre à n'importe qui d'interroger la donnée en langage
naturel, sans écrire de SQL, sans apprendre un outil de BI.

Deux stratégies s'affrontent : **construire un agent custom** (FastAPI + LangChain
+ AWS Bedrock, déployé sur EKS) ou **utiliser un outil managé** qui se connecte
à la stack existante.

## Décision
**Nao** (nao.ai) est adopté comme interface de requêtes en langage naturel.

Nao est un data IDE AI-powered qui se connecte nativement à Amazon Athena, lit
le Glue Catalog pour construire son contexte de schéma, supporte les workflows
dbt, et expose une interface conversationnelle pour générer et exécuter du SQL
en langage naturel.

La connexion à Athena se fait via les credentials AWS de la plateforme (IRSA ou
clé de service dédiée). Nao ne stocke pas la donnée — il exécute les requêtes
sur l'infrastructure Athena existante et retourne les résultats.

## Options considérées

| Option | Pour | Contre |
|--------|------|--------|
| **Nao** ✅ | Connexion Athena + Glue native, supporte dbt, SOC 2 Type II, SaaS donc zéro infra à opérer, onboarding rapide | SaaS externe — les requêtes SQL et les schémas transitent par les serveurs Nao, dépendance à un prestataire tiers |
| Agent custom (FastAPI + LangChain + Bedrock) | Données ne quittent jamais AWS, contrôle total, personnalisable | Charge de développement et de maintenance élevée, LLM à provisionner, infra EKS supplémentaire |
| Metabase Questions naturelles | Déjà déployé, zéro nouveau service | Capacités NL très limitées, pas conçu pour la conversation libre |
| ThoughtSpot | Très puissant pour la NL analytics | Coût élevé, complexité d'intégration, orienté BI et non data exploration |

## Conséquences

**Positives :** Déploiement en quelques heures — connecter Nao à Athena est une
opération de configuration, pas de développement. Les collaborateurs non-techniques
accèdent à la donnée sans formation SQL. Nao bénéficie automatiquement des
améliorations de contexte apportées par dbt (ADR-022, ADR-023) sans modification
de configuration côté Nao. La charge opérationnelle est nulle (SaaS).

**Compromis / Risques :** Les requêtes SQL générées et les schémas de tables
transitent par les infrastructures Nao (SaaS externe). Pour la donnée non-sensible,
ce risque est acceptable. Pour la donnée sensible (paie, TJ), Nao ne doit pas
être connecté aux bases Glue `sensitive_mart` — l'accès à ces données reste
réservé aux outils internes (Athena direct, Metabase avec SSO). La dépendance
à Nao est réversible : si Nao disparaît ou ne convient plus, l'alternative
(agent custom) est documentée dans `nl-query-architecture.md`.
