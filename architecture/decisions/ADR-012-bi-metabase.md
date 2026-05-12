# ADR-012: Metabase pour la BI et la visualisation

## Statut
Accepté — évolution prévue vers un outil IA conversationnel

## Contexte
La plateforme a besoin d'une couche de restitution permettant d'exploiter les données
de la couche `mart`. L'outil doit être représentatif des pratiques actuelles du marché
et permettre de valider les patterns de connexion BI → Athena → S3.

À terme, la cible est un outil de **data conversationnelle** permettant d'interagir
avec la donnée via un LLM — une direction que Metabase ne couvre pas nativement.
Metabase est donc une étape intermédiaire : utiliser l'outil en interne pour en
comprendre les forces et limites avant de définir ce que doit être la couche BI cible.

## Décision
Metabase (v2.24.2) est déployé sur EKS dans le namespace `metabase`. Choisi pour sa
popularité et sa présence chez des clients Hymaia.

Il se connecte à Amazon Athena via IRSA, avec un accès restreint à la couche `mart`.
Cette restriction est une pratique testée en interne — elle sera évaluée et challengée
avec le recul de l'usage réel avant d'être formalisée comme standard.

## Options considérées

| Option | Pour | Contre |
|--------|------|--------|
| **Metabase** ✅ | Populaire, accessible, OSS, self-hosted, rencontré chez des clients | Pas de capacités IA/LLM natives |
| Superset | OSS, très complet, plus flexible | UX moins intuitive, plus complexe à opérer |
| Tableau / Power BI | Standard entreprise | Coût, vendor lock-in, pas cloud-native |
| Outil BI conversationnel (LLM) | Cible à terme — interaction naturelle avec la donnée | Marché encore émergent, outils à évaluer |

## Conséquences

**Positives :** Validation des patterns de connexion Athena → BI. Outil connu du marché,
utile comme référence pour les clients. Retour d'expérience interne qui guidera le choix
de l'outil cible.

**Compromis / Risques :** Metabase n'est pas la cible finale. L'investissement sur cet
outil est volontairement limité — l'objectif est d'apprendre et d'évaluer, pas de
construire une solution BI pérenne sur cette base.
