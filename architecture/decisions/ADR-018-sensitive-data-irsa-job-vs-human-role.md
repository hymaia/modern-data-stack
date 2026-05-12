# ADR-018: Séparation stricte entre rôle IRSA des jobs et rôle humain SSO

## Statut
Proposé

## Contexte
Les pipelines de traitement (dbt, Spark, Polars) doivent lire la donnée sensible
brute pour la transformer — c'est leur raison d'être. Mais les développeurs qui
écrivent et maintiennent ces pipelines ne doivent pas pouvoir lire cette même
donnée brute.

Ces deux contraintes semblent opposées. Elles ne le sont pas si l'on distingue
l'identité du **code qui tourne** de l'identité de **la personne qui a écrit ce code**.

La plateforme utilise déjà IRSA (IAM Roles for Service Accounts) pour donner à
chaque outil K8s un rôle IAM dédié, distinct des rôles humains. Ce mécanisme
s'applique naturellement aux pipelines sensibles.

## Décision
Les pipelines accédant à la donnée sensible tournent sous un **rôle IRSA dédié**
(`dbt-sensitive-reader`, `spark-sensitive-reader`, etc.) qui est le seul à posséder
`s3:GetObject` sur `sensitive/*`.

Les développeurs accèdent à la plateforme via leur identité SSO (IAM Identity
Center). Cette identité n'inclut **jamais** le rôle IRSA des jobs — elle ne peut
pas être assumée manuellement. Un développeur ne peut pas "devenir" le rôle du job.

Le flux est : dev écrit le code → PR → review → merge → Dagster lance le job sous
son rôle IRSA → le job lit la donnée sensible. Le dev ne voit que le code, les
logs Dagster et les métriques — jamais les valeurs.

Le rôle IRSA du job est contraint en **écriture** : il ne peut écrire que dans
`sensitive/*`, pas dans `public/*`. Un job ne peut pas copier de la donnée sensible
vers un endroit accessible aux humains.

## Options considérées

| Option | Pour | Contre |
|--------|------|--------|
| **IRSA dédié par job, deny pour humains** ✅ | Réutilise IRSA existant, séparation claire, auditabilité Dagster | Le dev peut écrire du code qui logue des valeurs — risque résiduel organisationnel |
| Accès dev en lecture avec anonymisation à la volée | Le dev peut tester sur des données réelles masquées | Complexité technique élevée, masquage imparfait possible |
| Aucun accès humain ET aucun accès job direct (tout via API) | Contrôle maximum | Sur-engineering pour ce cas d'usage |

## Conséquences

**Positives :** Séparation nette entre identité humaine et identité de service,
cohérente avec le pattern IRSA déjà en place sur la plateforme. Les jobs Dagster
sont le seul intermédiaire entre la donnée sensible et les transformations.
Transposable chez les clients sans dépendance AWS : c'est un pattern IAM générique.

**Compromis / Risques :** Risque résiduel : un développeur peut écrire un job qui
affiche (`print`, `log`) des valeurs sensibles dans les logs Dagster, ou qui copie
la donnée vers un préfixe public via une étape intermédiaire dans un autre service.
Ce risque est mitigé par deux mesures organisationnelles : (1) toute modification
d'un pipeline sensible passe par une PR avec revue obligatoire, (2) le rôle IRSA
du job est en écriture uniquement sur `sensitive/*` — il ne peut pas écrire dans
`public/*`, ce qui bloque la fuite directe par copie S3.
