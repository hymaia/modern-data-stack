# ADR-022: dbt persist_docs pour enrichir le Glue Catalog comme contexte pour Nao

## Statut
Proposé

## Contexte
Nao génère du SQL en s'appuyant sur le contexte de schéma qu'il lit depuis le
Glue Catalog (noms de tables, noms de colonnes, types de données). Dans l'état
actuel, le Glue Catalog ne contient que des informations techniques : le nom
de colonne `amt_ht` ne dit rien à un LLM sur ce qu'il représente. Le résultat
est une génération SQL fragile, avec des risques d'utilisation de la mauvaise
colonne ou d'une logique incorrecte.

Les descriptions métier existent déjà partiellement dans les fichiers `_schema.yml`
de dbt — mais elles n'ont pas encore été propagées vers Glue. La question est :
comment enrichir le contexte disponible à Nao sans ajouter un nouveau service
ni modifier la configuration de Nao elle-même ?

## Décision
La configuration `persist_docs` est activée dans `dbt_project.yml` :

```yaml
models:
  +persist_docs:
    relations: true   # description du modèle → commentaire de table dans Glue
    columns:  true    # description de colonne → commentaire de colonne dans Glue
```

À chaque `dbt run`, dbt pousse automatiquement les descriptions des modèles et
des colonnes vers le Glue Catalog comme commentaires. Nao, qui lit le Glue Catalog
à chaque session, bénéficie immédiatement d'un contexte enrichi sans aucune
modification de sa configuration.

Cette décision est couplée à une exigence de documentation : tout modèle mart
exposé via Nao **doit** avoir une description de modèle et une description pour
chaque colonne dans son `_schema.yml`. Les modèles non documentés génèrent des
réponses de qualité dégradée — c'est un signal visible qui encourage la
documentation plutôt que de la rendre optionnelle.

## Options considérées

| Option | Pour | Contre |
|--------|------|--------|
| **dbt persist_docs** ✅ | Zéro nouveau service, descriptions dans Git et versionnées, bénéfice automatique pour Nao et tous les autres outils (Metabase, Athena console) | Nécessite que les descriptions dbt soient écrites et maintenues à jour |
| Enrichissement manuel du Glue Catalog (console AWS) | Immédiat | Non versionné, désynchronisé dès le prochain `dbt run`, maintenance manuelle |
| Data catalog externe (DataHub, Atlan, OpenMetadata) | Interface dédiée, fonctionnalités de gouvernance avancées | Nouveau service à déployer et opérer, sur-engineering pour ce cas d'usage |
| Fichier de contexte JSON injecté dans Nao | Flexibilité maximale | Nao-spécifique, non réutilisable, à synchroniser manuellement avec le schéma réel |

## Conséquences

**Positives :** Le Glue Catalog devient la source de vérité enrichie, consultable
par Nao, Metabase, l'Athena console et tout futur outil. Les descriptions sont
versionnées dans Git avec le code dbt — une PR de modification de schéma inclut
naturellement la mise à jour des descriptions. L'amélioration de la qualité des
réponses de Nao est immédiate et sans configuration supplémentaire.

**Compromis / Risques :** La qualité du contexte fourni à Nao dépend directement
de la discipline de documentation des équipes data. Un modèle non documenté
donnera des réponses médiocres — ce qui est visible par les utilisateurs et
constitue une incitation naturelle à documenter. Le risque de désynchronisation
existe si `dbt run` n'est pas exécuté après une modification du `_schema.yml` :
Glue conserve alors les anciennes descriptions jusqu'au prochain run.
