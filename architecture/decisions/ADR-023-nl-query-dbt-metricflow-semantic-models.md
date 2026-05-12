# ADR-023: dbt MetricFlow pour la définition des métriques métier

## Statut
Proposé

## Contexte
Même avec un Glue Catalog enrichi (ADR-022), Nao génère du SQL à partir des
descriptions de colonnes brutes. Pour une question comme "Quel est le chiffre
d'affaires du mois dernier ?", Nao doit déduire que "CA" correspond à
`SUM(amount_ht) WHERE status = 'paid'` — une logique qui n'est pas explicitement
dans les descriptions de colonnes.

Le risque est double : Nao peut calculer "CA" différemment selon comment la
question est formulée, et deux utilisateurs posant la même question peuvent
obtenir des chiffres différents. Pour des métriques critiques (CA, taux de
conversion, nombre de consultants actifs), cette incohérence est inacceptable.

La plateforme utilise déjà dbt. dbt intègre nativement MetricFlow depuis la
version 1.6, qui permet de définir des modèles sémantiques et des métriques
nommées directement dans les fichiers YAML du projet dbt.

## Décision
Les métriques métier critiques sont formalisées via **dbt MetricFlow** dans les
fichiers `_schema.yml` des modèles mart concernés.

Chaque métrique définit : son nom métier, sa description, sa formule de calcul
(agrégation, filtre), ses dimensions disponibles et ses entités de jointure.
Ces définitions sont dans Git, versionnées, testables avec `dbt test`.

```yaml
semantic_models:
  - name: orders
    model: ref('fct_orders')
    entities:
      - name: customer    type: foreign    expr: customer_id
      - name: product     type: foreign    expr: product_id
    dimensions:
      - name: ordered_at  type: time       type_params: { time_granularity: day }
      - name: region      type: categorical
      - name: channel     type: categorical
    measures:
      - name: paid_revenue
        agg: SUM
        expr: "CASE WHEN status = 'paid' THEN amount_ht END"
        description: "Montant HT des commandes au statut paid"

metrics:
  - name: revenue
    description: "CA des commandes payées, hors taxes, en euros"
    type: simple
    type_params:
      measure: paid_revenue
```

Les métriques MetricFlow sont matérialisées en **vues SQL dans le mart** via
`dbt run`. Ces vues sont la source que Nao doit utiliser pour répondre aux
questions métier — elles encapsulent la logique et ne laissent pas Nao la
recalculer librement.

Les équipes métier (finance, direction) sont associées à la validation des
définitions de métriques via la revue de PR — c'est le moment où elles confirment
que la formule correspond à leur définition métier.

## Options considérées

| Option | Pour | Contre |
|--------|------|--------|
| **dbt MetricFlow** ✅ | Natif dans dbt (déjà en place), définitions dans Git, testables, vues SQL générées automatiquement | API server MetricFlow nécessite dbt Cloud pour être exposée — en self-hosted, les métriques sont des vues SQL, pas une API de métriques |
| Cube.dev (semantic layer API) | API REST/GraphQL exploitable directement par n'importe quel outil | Nouveau service à déployer sur EKS, maintien supplémentaire, sur-engineering si Nao lit les vues dbt directement |
| Définitions métier dans Nao uniquement | Rapide à mettre en place | Non versionné dans Git, non partagé avec Metabase, risque de divergence entre outils |
| Aucune définition formelle (laisser le LLM déduire) | Zéro effort | Incohérence garantie sur les métriques critiques |

## Conséquences

**Positives :** "Revenue" a une définition unique, versionnée dans Git, validée
par les équipes métier, partagée entre Nao, Metabase et tout futur outil.
Les vues générées par MetricFlow sont interrogeables directement dans Athena —
elles servent de surfaces stables pour Nao, indépendamment des évolutions des
tables de faits sous-jacentes. Les métriques sont testables en CI (dbt test)
et documentées dans la doc dbt auto-générée.

**Compromis / Risques :** En self-hosted sans dbt Cloud, MetricFlow ne dispose
pas d'une API server pour exposer les métriques programmatiquement. Les métriques
sont disponibles comme vues SQL dans le mart — suffisant pour Nao qui les lit
via Athena, mais insuffisant pour un outil qui aurait besoin d'une API de métriques
structurée (cas d'usage Cube.dev). Si ce besoin émerge, ajouter Cube.dev devant
les vues MetricFlow existantes est une évolution naturelle sans remise en cause
du travail de définition des métriques.

Le travail principal est humain : définir formellement les métriques avec les
équipes métier prend du temps et nécessite un alignement entre data et business.
C'est intentionnel — c'est de la valeur créée une fois, qui bénéficie à tous
les outils pour toujours.
