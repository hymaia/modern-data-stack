# ADR-015: Structure de projet ETL en mono-repo et pattern de code location Dagster

## Statut
Proposé — non encore formalisé, à consolider avec l'évolution du repo vers la plateforme centrale Hymaia

## Contexte
La plateforme doit être utilisable par n'importe quel développeur Hymaia pour créer
rapidement un projet ETL, quelle que soit la stack choisie. Sans convention commune,
chaque projet aurait une structure différente, rendant difficiles la montée en compétence,
la revue de code et la réutilisation entre projets et entre clients.

Par ailleurs, le repo actuel `modern-data-stack` est un PoC personnel (noms de domaine
`fcussac`, déploiement sur un compte AWS individuel) — il doit évoluer vers une
**plateforme centrale Hymaia**, générique, utilisable par toutes les équipes sur
tout type de projet client.

## Décision
Chaque projet ETL suit une structure mono-repo standard à 3 dossiers :

```
mon-projet-etl/
├── infra/          # Terraform spécifique au projet (ressources AWS, IRSA…)
├── orchestration/  # Code Dagster (assets, jobs, schedules) → image ECR
└── <stack>/        # Code métier (ex: dbt/, spark/, polars/) → image ECR
```

Des **stacks préconfigurées** sont proposées comme templates de démarrage.
La liste n'est pas arrêtée — elle sera enrichie selon les besoins rencontrés en
mission et en interne :
- `dbt + Athena` orchestré par Dagster
- `Spark` orchestré par Dagster
- `Polars` orchestré par Dagster
- *(à venir selon les besoins)*

Chaque stack correspond à une ou plusieurs images ECR déployées comme **code locations**
distinctes dans Dagster, ce qui découple les cycles de déploiement du code métier
du daemon Dagster et des autres projets.

**Organisation repo cible :**
- **1 repo `data-platform`** : infra K8s, outils (Airbyte, Dagster, Spark Operator,
  Metabase…), ArgoCD apps — générique, sans valeurs spécifiques à un individu ou un client
- **1 repo par projet ETL** : suit le template à 3 dossiers, indépendant de la plateforme

La visibilité (public / privé) est laissée à l'appréciation de chaque équipe selon le
contexte projet ou client.

## Options considérées

| Option | Pour | Contre |
|--------|------|--------|
| **Template 3 dossiers + code locations** ✅ | Convention claire, cycle de déploiement découplé, réutilisable entre clients | Pas encore formalisé — structure implicite dans le repo actuel |
| Multi-repo sans convention | Liberté totale | Pas de cohérence, onboarding difficile |
| Tout dans le repo `data-platform` | Centralisation pratique | Couplage plateforme / projets, non scalable |
| Code location unique pour tous les projets | Simple | Déploiement couplé, risque de régression croisée |

## Conséquences

**Positives :** Onboarding rapide sur un nouveau projet ETL. Séparation claire entre
la plateforme (infrastructure partagée) et les projets (code métier). Pattern
directement transférable et démontrable chez les clients Hymaia.

**Compromis / Risques :** Le repo actuel mélange encore plateforme et exemples de projets
(`spark-vs-polars`, `dbt`, `orchestration-dagster`) — une migration vers la structure
cible est nécessaire. Il manque également une **CI/CD** pour automatiser le build des
images ECR et le déploiement des code locations, ce qui est un prérequis avant de
proposer ce pattern à grande échelle.


## Options considérées

| Option | Pour | Contre |
|--------|------|--------|
| **Mono-repo structuré + code locations** ✅ | Convention claire, cycle de déploiement découplé, template réutilisable | Couplage entre data platform et projets dans un même repo (état actuel, à faire évoluer) |
| Multi-repo (1 repo data platform + 1 repo par projet) | Séparation claire des responsabilités, cycles de vie indépendants | Plus de friction initiale, coordination entre repos |
| Tout dans le repo `modern-data-stack` | Centralisation pratique pour démarrer | Non scalable, couplage fort entre la plateforme et les projets |
| Code location unique pour tous les projets | Simple | Cycle de déploiement couplé, risque de régression croisée |

## Conséquences

**Positives :** Convention claire qui permet à n'importe quel développeur Hymaia de
démarrer un projet ETL rapidement avec une stack préconfigurée. Chaque code location
Dagster se déploie indépendamment. Pattern directement transférable chez les clients.

**Compromis / Risques :** Dans l'état actuel du repo, les projets exemples (`spark-vs-polars`,
`dbt`, `orchestration-dagster`) cohabitent avec la data platform dans le même repo —
ce qui est pratique pour démarrer mais crée du couplage. L'évolution cible est :
**1 repo `data-platform`** (infra + outils K8s) + **1 repo par projet ETL** suivant
le template à 3 dossiers.
