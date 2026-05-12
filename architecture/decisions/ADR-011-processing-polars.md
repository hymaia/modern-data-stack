# ADR-011: Polars pour le traitement sur volumes intermédiaires

## Statut
Accepté

## Contexte
La plateforme doit illustrer une alternative à Spark pour les traitements qui ne
nécessitent pas de distribution. Polars est un framework Python de plus en plus populaire,
reconnu pour ses performances en single-node. Le montrer aux côtés de Spark permet
de comprendre quand l'un ou l'autre est pertinent.

## Décision
Des jobs Polars sont déployés dans un namespace dédié (`polars`) sur EKS, orchestrés
par Dagster. Le dossier `spark-vs-polars/` contient un exemple concret de job Polars
sur cette plateforme, à mettre en regard du job Spark équivalent.

À terme, chaque projet Polars devrait vivre dans son propre repo, indépendant du repo
de la data platform (voir ADR-015).

## Options considérées

| Option | Pour | Contre |
|--------|------|--------|
| **Polars** ✅ | Très rapide en single-node, mémoire efficace, Python natif, populaire | Pas distribué, limité au volume d'un seul nœud |
| Pandas | Universel, très grande communauté | Lent, gourmand en mémoire sur grands volumes |
| Spark (même workload) | Distribué, scalable | Overhead important pour petits volumes |
| DuckDB | Rapide, SQL natif | Non évalué dans ce contexte |

## Conséquences

**Positives :** Exemple concret et comparatif avec Spark. Polars est de plus en plus
rencontré chez les clients data. Pas besoin de node group dédié — tourne sur les nœuds
`main` existants.

**Compromis / Risques :** Limité au volume d'un seul nœud. Au-delà d'un certain seuil,
il faut basculer sur Spark — la frontière dépend du contexte projet.
