# ADR-001: AWS comme cloud provider

## Statut
Accepté

## Contexte
Hymaia utilise à la fois AWS et GCP selon les projets. Pour cette data platform, le choix
du cloud provider revenait à l'auteur du projet, qui devait sélectionner l'environnement
dans lequel il serait le plus productif et autonome.

## Décision
AWS est le cloud provider unique de la plateforme, région `eu-west-1` (Irlande).

Le choix d'AWS repose sur la maîtrise technique de l'auteur du projet sur ce provider.
`eu-west-1` est choisi car c'est la région européenne qui reçoit les nouvelles fonctionnalités
AWS en premier, ce qui réduit le risque de bloquer sur un service non encore disponible.

Le domaine `fcussac.app.hymaia.com` y est hébergé via Route 53.

## Options considérées

| Option | Pour | Contre |
|--------|------|--------|
| **AWS** ✅ | Maîtrise de l'équipe, services data matures (Athena, Glue, Aurora Serverless), `eu-west-1` en avance sur les releases EU | Pas le seul provider utilisé chez Hymaia |
| GCP | Également maîtrisé chez Hymaia, BigQuery très compétitif pour la BI | Moins de maîtrise personnelle de l'auteur |
| Azure | — | Pas de compétence spécifique dans l'équipe |
| On-premise | — | Ops lourd, pas adapté à un projet data moderne |

## Conséquences

**Positives :** Vitesse d'exécution maximale — l'auteur connaît les services, les patterns IAM,
et les subtilités AWS. Accès aux dernières fonctionnalités en Europe via `eu-west-1`.

**Compromis / Risques :** La plateforme n'est pas portable sur GCP (BigQuery, Dataproc…)
sans réécriture significative. Si un autre membre de l'équipe Hymaia (plus GCP-oriented)
reprend le projet, il y aura une courbe d'apprentissage.
