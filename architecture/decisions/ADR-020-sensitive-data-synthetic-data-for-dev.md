# ADR-020: Données synthétiques générées par Dagster pour le développement sur données sensibles

## Statut
Proposé

## Contexte
Les développeurs ont accès au schéma des tables sensibles via les fichiers dbt
`_schema.yml` (ADR-019), mais pas aux données réelles (ADR-016, ADR-018).

Connaître le schéma est nécessaire mais insuffisant pour développer un pipeline :
il faut pouvoir exécuter le code, vérifier que les transformations produisent le
résultat attendu, et valider la logique métier (agrégations, filtres, jointures).
Sans données, le dev ne peut ni tester ni déboguer.

## Décision
Un **asset Dagster dédié** génère des données synthétiques cohérentes à partir
du schéma dbt et les dépose dans un préfixe `sensitive_dev/` accessible aux
développeurs via leur rôle SSO.

Le générateur utilise une bibliothèque de faker (Faker ou Mimesis) paramétrée
par les types et descriptions des colonnes du `_schema.yml`. Les données produites
respectent les contraintes du schéma (types, cardinalités, relations entre tables)
et sont suffisamment réalistes pour valider la logique métier.

```
sensitive_dev/payroll/           ← accessible aux devs
sensitive_dev/consultant_rates/  ← accessible aux devs
sensitive/payroll/               ← accessible aux jobs IRSA uniquement
sensitive/consultant_rates/      ← accessible aux jobs IRSA uniquement
```

Le générateur est lancé manuellement ou sur schedule dans Dagster. Il n'a accès
qu'en écriture sur `sensitive_dev/` — il ne lit pas la donnée réelle.

Les pipelines dbt et Spark/Polars sont paramétrés par une variable d'environnement
`DATA_ENV` (`dev` ou `prod`) qui détermine le préfixe source :
- `dev`  → lit dans `sensitive_dev/`, écrit dans `sensitive_dev/mart/`
- `prod` → lit dans `sensitive/`, écrit dans `sensitive/mart/`

## Options considérées

| Option | Pour | Contre |
|--------|------|--------|
| **Générateur Dagster + préfixe sensitive_dev/** ✅ | Cohérent avec la plateforme, données réalistes, aucun accès à la vraie donnée | Maintenir le générateur quand le schéma évolue |
| Anonymisation de la vraie donnée (pseudonymisation) | Données structurellement identiques à la prod | Risque de ré-identification, complexité, accès à la vraie donnée requis pour anonymiser |
| Sous-ensemble fixe de données réelles en dev | Réalisme maximum | Données réelles exposées aux devs — contraire à l'objectif |
| Pas de données en dev (tests unitaires purs) | Zéro risque de fuite | Impossible de tester les transformations end-to-end |

## Conséquences

**Positives :** Les développeurs travaillent sur un environnement fonctionnel sans
jamais toucher la donnée réelle. L'expérience de développement est identique à
celle d'un pipeline non-sensible. Le générateur est un asset Dagster comme les
autres : versionné dans Git, déployé via ArgoCD, observable dans l'UI Dagster.

Le préfixe `sensitive_dev/` peut aussi être utilisé pour les tests en CI/CD :
la pipeline génère des données synthétiques, exécute les transformations dbt,
vérifie les assertions — sans jamais toucher la prod.

**Compromis / Risques :** Le générateur doit être mis à jour à chaque évolution
du schéma. Si un nouveau champ est ajouté dans le `_schema.yml` sans mise à jour
du générateur, les tests dev passent mais la prod peut échouer sur des contraintes
non testées. Mitigation : le générateur lit directement le `_schema.yml` dbt pour
inférer les colonnes à générer — il s'auto-adapte aux ajouts de colonnes simples,
seules les nouvelles contraintes métier complexes nécessitent une mise à jour manuelle.
