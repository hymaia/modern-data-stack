# ADR-003: ArgoCD pour le déploiement GitOps des outils

## Statut
Accepté

## Contexte
Avec plusieurs outils déployés sur Kubernetes (Airbyte, Dagster, Spark, Metabase), il faut
un mécanisme fiable pour garantir que ce qui tourne dans le cluster correspond exactement à
ce qui est décrit dans le code. Sans reconciliation continue, des modifications manuelles
ou des drifts silencieux rendent l'état réel du cluster imprévisible.

Par ailleurs, certains paramètres de configuration des outils (endpoints RDS, ARN de
certificats, ARN de rôles IAM) sont des outputs Terraform. Il faut un moyen de les propager
jusqu'aux Helm charts sans intervention manuelle.

## Décision
ArgoCD (v3.0.5) est déployé sur EKS comme contrôleur GitOps. Chaque outil est décrit comme
une `Application` ArgoCD pointant sur `apps/<outil>/` dans le repo `hymaia/modern-data-stack`,
branche `main`, avec synchronisation automatique (`prune: true`, `selfHeal: true`).

**`selfHeal: true`** est un choix délibéré et cohérent avec la philosophie GitOps : Git est
la seule source de vérité. Toute modification manuelle dans le cluster est automatiquement
écrasée. Si un changement est nécessaire, il passe par Git.

**Pattern Terraform → `values.yaml` → Git → ArgoCD :** Terraform génère les `values.yaml`
des Helm charts (avec les endpoints RDS, ARN de certificats, ARN IAM…) et les écrit
directement dans le repo. Ce pattern assure que les dépendances AWS sont toujours
reflétées dans la configuration K8s sans étape manuelle. C'est un choix pragmatique —
on aurait pu séparer infra et config dans deux repos distincts — mais l'essentiel est
le concept : un seul repo comme source de vérité.

## Options considérées

| Option | Pour | Contre |
|--------|------|--------|
| **ArgoCD** ✅ | GitOps natif, UI claire, reconciliation continue, large adoption | Outil supplémentaire à opérer sur le cluster |
| Flux CD | Léger, GitOps natif | Non évalué (non connu à l'époque du choix) |
| Helm direct depuis Terraform | Simple, tout-en-un | Pas de reconciliation continue, drift possible, pas d'UI d'état |
| `kubectl apply` en CI/CD | Simple | Pas d'état désiré maintenu, pas de self-heal |

## Conséquences

**Positives :** État du cluster toujours cohérent avec Git. Visibilité complète sur ce qui
est déployé via l'UI ArgoCD. Les dépendances AWS (outputs Terraform) se propagent
automatiquement jusqu'aux outils K8s. Pattern réutilisable chez les clients Hymaia.

**Compromis / Risques :** Le mono-repo Terraform + config ArgoCD crée un couplage entre
l'infra et la config applicative. Une meilleure séparation (multi-repo) serait plus propre
à grande échelle, mais le concept reste le même. Toute intervention manuelle sur le cluster
est impossible sans passer par Git, ce qui peut ralentir le debugging en urgence.
