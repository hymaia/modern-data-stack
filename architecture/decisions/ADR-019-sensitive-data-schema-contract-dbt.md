# ADR-019: Contrat de schéma public via dbt pour les données sensibles

## Statut
Proposé

## Contexte
Les développeurs qui écrivent des pipelines sur la donnée sensible (ADR-018) ont
besoin de connaître la structure des données pour écrire du code correct : noms
de colonnes, types, relations entre tables, sémantique métier.

Sans accès à la donnée réelle (ADR-016, ADR-018), la seule façon de leur
transmettre cette information est de la documenter explicitement. La question
est : où cette documentation vit-elle, et qui la maintient ?

## Décision
Le schéma des tables sensibles est documenté dans les fichiers `_schema.yml` de
dbt comme pour toute autre table de la plateforme. Ces fichiers constituent le
**contrat de données** public : ils décrivent la structure sans exposer de valeurs.

```yaml
models:
  - name: payroll
    description: "1 ligne par employé par mois de paie"
    config:
      meta:
        sensitivity: restricted
        owner: hymaia-hr-team
    columns:
      - name: employee_id
        description: "Identifiant anonymisé de l'employé"
      - name: department
        description: "Département Hymaia (Engineering, Sales, Ops…)"
      - name: gross_salary
        description: "Salaire brut mensuel en euros"
      - name: net_salary
        description: "Salaire net mensuel en euros"
      - name: month
        description: "Premier jour du mois concerné (YYYY-MM-01)"
```

Ce fichier est dans Git, accessible à tous les développeurs, et constitue la
référence pour écrire les transformations, les tests et la documentation.

La propriété (`owner`) et le niveau de sensibilité (`sensitivity`) sont taggés
dans les métadonnées dbt — ils alimentent la documentation auto-générée et
peuvent être exploités par un outil de data catalog à l'avenir.

## Options considérées

| Option | Pour | Contre |
|--------|------|--------|
| **_schema.yml dbt** ✅ | Dans Git, versionné, même outil que le reste, génère la doc automatiquement | Nécessite une discipline de documentation — le schéma doit être maintenu à jour |
| Confluence / Notion | Accessible à tous, facile à écrire | Découplé du code, peut être désynchronisé, pas versionné avec le pipeline |
| README dans le repo | Simple | Pas structuré, pas exploitable par des outils |
| Accès en lecture seule à Glue Catalog | Directement à jour | Glue ne contient que les noms/types, pas la sémantique métier |

## Conséquences

**Positives :** Un développeur peut écrire et tester un pipeline complet en ne
consultant que les fichiers `_schema.yml` et les données synthétiques (ADR-020),
sans jamais avoir besoin d'accéder à la donnée réelle. Le schéma est la source de
vérité unique, partagée entre les équipes RH (qui valident) et les équipes data
(qui implémentent). Il est versionné, diffable en PR, et exploitable par des outils
de data catalog futurs.

**Compromis / Risques :** La qualité du contrat dépend de la rigueur de
documentation. Si l'équipe RH modifie la source de données (nouveau champ, renommage)
sans mettre à jour le `_schema.yml`, le contrat se désynchronise. Mitigation :
les tests dbt (`not_null`, `accepted_values`, relationships) échouent en CI dès
qu'un champ attendu disparaît ou change de type — ce qui force la mise à jour du contrat.
