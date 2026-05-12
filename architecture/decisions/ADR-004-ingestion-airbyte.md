# ADR-004: Airbyte pour l'ingestion de données

## Statut
Accepté

## Contexte
La plateforme a besoin d'un outil d'ingestion capable de connecter des sources externes
(bases de données, APIs, SaaS…) vers le Data Lake S3. L'outil doit être représentatif
de ce que l'on rencontre chez les clients Hymaia, afin que la plateforme serve aussi
de terrain d'apprentissage et de référence méthodologique.

Les connecteurs spécifiques et les modalités de chargement (full refresh vs incremental,
format de fichier) dépendent du contexte de chaque projet et ne sont pas fixés au niveau
de l'architecture.

## Décision
Airbyte (v2.0.19) est déployé sur EKS dans le namespace `airbyte`. C'est l'outil
d'ingestion de référence de la plateforme, choisi pour sa popularité sur le marché
et sa présence récurrente chez les clients Hymaia.

La plateforme étant conçue comme une référence méthodologique et non un produit figé,
n'importe quel outil équivalent peut être ajouté ou substitué à tout moment
(déploiement via ArgoCD, namespace dédié, IRSA propre).

Son état est persisté dans Aurora PostgreSQL Serverless v2. Les credentials sont
injectés via External Secrets Operator depuis AWS Secrets Manager.

## Options considérées

| Option | Pour | Contre |
|--------|------|--------|
| **Airbyte** ✅ | Populaire, 300+ connecteurs, OSS, déjà rencontré chez des clients | Lourd en ressources, complexité de déploiement sur K8s |
| Fivetran | Fiable, zéro maintenance | Coût élevé, vendor lock-in, non self-hosted |
| Singer / Meltano | Léger, OSS | Moins de connecteurs maintenus, plus de maintenance custom |
| Scripts custom | Flexibilité totale | Pas de monitoring natif, maintenance élevée, pas réutilisable |

## Conséquences

**Positives :** Outil représentatif du marché — maîtriser Airbyte sur cette plateforme
est directement transférable chez les clients. 300+ connecteurs disponibles sans
développement custom. Déployé sur K8s comme les autres outils, cohérent avec l'approche.

**Compromis / Risques :** Airbyte est l'un des outils les plus gourmands en ressources
du cluster. L'outil étant interchangeable par conception, ce n'est pas un problème
bloquant, mais il faut en être conscient lors du sizing du node group `main`.
