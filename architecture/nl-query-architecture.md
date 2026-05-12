# 🔬 CONVERSER AVEC SA DONNÉE — Les niveaux de civilisation

> Chaque niveau se construit sur le précédent.
> Chaque niveau est déjà utile. On peut s'arrêter à n'importe lequel.
> Basé sur la stack Hymaïa actuelle : S3 · Glue · Athena · dbt · EKS · ArgoCD.

---

```
╔══════════════════════════════════════════════════════════════════════════════╗
║  POINT DE DÉPART — Ce qu'on a déjà                                  ★ ★ ★  ║
║                                                                              ║
║   S3 mart ── Glue Catalog ── Athena ── dbt ── EKS ── ArgoCD ── ESO/IRSA     ║
║                                                                              ║
║   Les données sont là. Propres. Requêtables. Mais uniquement en SQL.         ║
╚══════════════════════════════════════════════════════════════════════════════╝

                                    │
                                    │  on monte
                                    ▼


╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║   NIVEAU  1                                                                  ║
║   ▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔                                              ║
║   « LA TORCHE »                                                              ║
║   Premier dialogue avec la donnée                                            ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝

  Ce qu'on construit
  ──────────────────
  Un agent minimal qui lit le Glue Catalog et génère du SQL via un LLM.
  Pas de nouvelles conventions. Pas de nouveau modèle de données.

  Matériaux nécessaires
  ─────────────────────
  ┌──────────────────────────────────────────────────────────────────────────┐
  │                                                                          │
  │  ① Activer AWS Bedrock dans la console                                   │
  │     Console AWS → Bedrock → Model access → Request → Claude 3 Sonnet     │
  │     Région : eu-west-1  (action manuelle, une seule fois)                │
  │                                                                          │
  │  ② Déployer le NL→SQL Agent sur EKS                                      │
  │     apps/nl-query/agent/   →  ArgoCD  (même pattern que Metabase)        │
  │     IRSA : glue:GetTables + athena:StartQueryExecution + s3:GetObject     │
  │             + bedrock:InvokeModel                                         │
  │                                                                          │
  │  ③ Déployer le Chat UI sur EKS                                           │
  │     apps/nl-query/ui/      →  ArgoCD  (Chainlit, image ECR)              │
  │                                                                          │
  └──────────────────────────────────────────────────────────────────────────┘

  Comment ça marche
  ─────────────────

   Utilisateur : "Combien de commandes hier ?"
        │
        ▼
   [ Agent ]
     └─ glue.get_tables("mart")           ← lit les tables et colonnes
     └─ LLM : schéma brut + question → SQL
     └─ Athena exécute
        │
        ▼
   "Il y a eu 1 247 commandes hier."

  Ce qu'on débloque                       Ce qu'on ne peut pas encore
  ─────────────────                       ──────────────────────────
  ✓ Première conversation en français     ✗ Les noms de colonnes sont souvent
  ✓ Zéro modification sur les données       cryptiques (amt_ht, dt_cmd, cust_id)
  ✓ Déployé en quelques jours             ✗ Le LLM devine le sens → parfois faux
                                          ✗ "revenue" peut être calculé n'importe
                                            comment selon la question

  ※ Pour des données bien nommées et une logique simple, ce niveau suffit.
    Pour du métier complexe, il faut monter.


                                    │
                         ┌──────────┘
                         │  on ajoute : descriptions dbt → Glue
                         ▼


╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║   NIVEAU  2                                                                  ║
║   ▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔                                              ║
║   « LE FEU MAÎTRISÉ »                                                        ║
║   Le LLM comprend le vocabulaire métier                                      ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝

  Ce qu'on construit
  ──────────────────
  On enrichit le Glue Catalog avec les descriptions dbt.
  L'agent du Niveau 1 lit maintenant des métadonnées riches — sans rien changer
  au code de l'agent.

  Matériaux nécessaires
  ─────────────────────
  ┌──────────────────────────────────────────────────────────────────────────┐
  │                                                                          │
  │  ① Écrire les descriptions dans les _mart.yml dbt                        │
  │                                                                          │
  │     models:                                                              │
  │       - name: fct_orders                                                 │
  │         description: "1 ligne par commande validée sur la plateforme"    │
  │         columns:                                                         │
  │           - name: amount_ht                                              │
  │             description: "Montant hors taxes en euros"                   │
  │           - name: status                                                 │
  │             description: "paid | pending | cancelled | refunded"         │
  │           - name: ordered_at                                             │
  │             description: "Timestamp UTC de validation de la commande"    │
  │                                                                          │
  │  ② Activer persist_docs dans dbt_project.yml  (une ligne)                │
  │                                                                          │
  │     models:                                                              │
  │       +persist_docs:                                                     │
  │         relations: true    ← description du modèle → commentaire Glue   │
  │         columns:  true     ← description colonne  → commentaire Glue    │
  │                                                                          │
  │  ③ Relancer dbt run  →  les descriptions arrivent dans Glue              │
  │     L'agent du Niveau 1 est automatiquement amélioré. Rien à redéployer. │
  │                                                                          │
  └──────────────────────────────────────────────────────────────────────────┘

  Ce que voit le LLM maintenant
  ──────────────────────────────

   AVANT (Niveau 1)                    APRÈS (Niveau 2)
   ────────────────                    ────────────────
   table: fct_orders                   table: fct_orders
   columns:                            description: "1 ligne par commande"
     - amount_ht  DOUBLE               columns:
     - status     VARCHAR                - amount_ht  DOUBLE
     - ordered_at TIMESTAMP               "Montant hors taxes en euros"
                                        - status     VARCHAR
                                          "paid | pending | cancelled"
                                        - ordered_at TIMESTAMP
                                          "Timestamp UTC de validation"

  Ce qu'on débloque                       Ce qu'on ne peut pas encore
  ─────────────────                       ──────────────────────────
  ✓ Le LLM comprend chaque colonne        ✗ "revenue" = SUM(amount_ht) ?
  ✓ Moins d'hallucinations sur les noms     Ou juste amount_ht ?
  ✓ Zéro nouveau service à déployer         Ou amount_ht WHERE status='paid' ?
  ✓ Les descriptions profitent aussi      ✗ Deux questions similaires peuvent
    à Metabase et à Athena                  donner des chiffres différents
  ✓ Travail fait une fois, profite à tout

  ※ C'est le niveau le plus rentable : peu d'effort, impact maximal sur la qualité.
  ※ L'effort principal est humain : quelqu'un doit écrire les descriptions.
    C'est du travail de data modeling, pas d'infra.


                                    │
                         ┌──────────┘
                         │  on ajoute : définitions de métriques dbt
                         ▼


╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║   NIVEAU  3                                                                  ║
║   ▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔                                              ║
║   « LA FORGE »                                                               ║
║   Les métriques métier sont gravées dans le marbre                           ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝

  Ce qu'on construit
  ──────────────────
  On formalise les métriques clés dans dbt (MetricFlow).
  "Revenue" a maintenant une définition unique, partagée, versionnable dans Git.
  L'agent l'injecte dans son prompt : le LLM n'a plus à deviner.

  Matériaux nécessaires
  ─────────────────────
  ┌──────────────────────────────────────────────────────────────────────────┐
  │                                                                          │
  │  ① Écrire les semantic_models dans les _mart.yml dbt                     │
  │                                                                          │
  │     semantic_models:                                                     │
  │       - name: orders                                                     │
  │         model: ref('fct_orders')                                         │
  │         entities:                                                        │
  │           - name: customer   type: foreign   expr: customer_id           │
  │           - name: product    type: foreign   expr: product_id            │
  │         dimensions:                                                      │
  │           - name: ordered_at    type: time                               │
  │           - name: region        type: categorical                        │
  │           - name: channel       type: categorical                        │
  │         measures:                                                        │
  │           - name: paid_revenue                                           │
  │             agg: SUM                                                     │
  │             expr: "CASE WHEN status='paid' THEN amount_ht END"           │
  │                                                                          │
  │  ② Définir les métriques nommées                                         │
  │                                                                          │
  │     metrics:                                                             │
  │       - name: revenue                                                    │
  │         description: "CA des commandes payées, hors taxes, en euros"     │
  │         type: simple                                                     │
  │         type_params:  { measure: paid_revenue }                          │
  │                                                                          │
  │       - name: conversion_rate                                            │
  │         description: "% de sessions ayant abouti à une commande payée"  │
  │         type: ratio                                                      │
  │         type_params:                                                     │
  │           numerator:   paid_orders                                       │
  │           denominator: total_sessions                                    │
  │                                                                          │
  │  ③ L'agent lit ces définitions et les injecte dans le prompt LLM         │
  │     "revenue = SUM(amount_ht) WHERE status='paid' — défini dans dbt"    │
  │                                                                          │
  └──────────────────────────────────────────────────────────────────────────┘

  Ce qu'on débloque                       Ce qu'on ne peut pas encore
  ─────────────────                       ──────────────────────────
  ✓ "revenue" = même calcul partout       ✗ Les métriques sont dans des fichiers
  ✓ Cohérence entre Metabase et le LLM      YAML — pas encore exposées via une API
  ✓ Définitions versionnées dans Git      ✗ Pas de caching des requêtes
  ✓ Raffinables sans toucher à l'agent    ✗ Chaque outil (Metabase, LLM)
  ✓ Testables avec dbt test                 réinterprète encore les définitions
                                            à sa façon

  ※ Ce niveau est le cœur du travail de "data modeling" — le plus long,
    le plus précieux, et celui qui survit à n'importe quel changement d'outil.


                                    │
                         ┌──────────┘
                         │  on ajoute : Cube.dev comme serveur de métriques
                         ▼


╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║   NIVEAU  4                                                                  ║
║   ▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔                                              ║
║   « L'ACIER »                                                                ║
║   Une API de métriques pour tous les outils                                  ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝

  Ce qu'on construit
  ──────────────────
  On déploie Cube.dev sur EKS. Il lit les modèles dbt (Niveau 3) et expose
  une API REST/SQL unique que tous les outils consomment.
  Plus personne ne recalcule "revenue" de son côté.

  ┌──────────────────────────────────────────────────────────────────────────┐
  │  Matériaux nécessaires                                                   │
  │                                                                          │
  │  ① Déployer Cube.dev sur EKS                                             │
  │     apps/cube/   →   ArgoCD   (Helm chart officiel)                      │
  │     Connexion : Athena via IRSA  ★  (même mécanisme)                     │
  │     Lecture : dbt models + metric definitions du Niveau 3                │
  │                                                                          │
  │  ② Mettre à jour l'agent (Niveau 1) pour appeler Cube API               │
  │     avant : glue.get_tables()                                            │
  │     après  : cube_api.get_meta()  → métriques + dimensions + types       │
  │                                                                          │
  │  ③ (optionnel) Rebrancher Metabase sur Cube au lieu d'Athena direct      │
  │     → Metabase voit les mêmes métriques que le LLM                       │
  └──────────────────────────────────────────────────────────────────────────┘

  Architecture résultante
  ────────────────────────

                    dbt models + metric defs  (Niveau 3)
                              │
                              ▼
                        ┌──────────┐
                        │ Cube.dev │  ← source de vérité unique
                        └────┬─────┘
                ┌────────────┼─────────────┐
                ▼            ▼             ▼
           NL→SQL         Metabase      API future
            Agent           BI         (mobile, etc.)
              │
         AWS Bedrock
              │
          Chat UI

  Ce qu'on débloque                       Ce qu'on ne peut pas encore
  ─────────────────                       ──────────────────────────
  ✓ Source de vérité pour TOUS les outils ✗ Le LLM ne se souvient pas
  ✓ Caching des requêtes Athena             des échanges précédents
  ✓ Contrôle d'accès par outil / équipe   ✗ On ne peut pas lui "apprendre"
  ✓ Metabase + LLM = chiffres identiques    qu'une question précédente
  ✓ Ajouter un outil = le brancher sur      était mal formulée
    Cube, pas sur Athena


                                    │
                         ┌──────────┘
                         │  on ajoute : mémoire et apprentissage
                         ▼


╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║   NIVEAU  5                                                                  ║
║   ▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔                                              ║
║   « L'ARMURE »                                                               ║
║   Mémoire conversationnelle et auto-amélioration                             ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝

  Ce qu'on construit
  ──────────────────
  L'agent se souvient des conversations passées. Il stocke les paires
  question→SQL validées comme exemples (few-shot). Plus on l'utilise,
  meilleur il devient.

  ┌──────────────────────────────────────────────────────────────────────────┐
  │  Matériaux nécessaires                                                   │
  │                                                                          │
  │  ① Activer pgvector sur Aurora PostgreSQL  ★  (déjà en place)            │
  │     CREATE EXTENSION vector;                                             │
  │     → stocke les embeddings des questions passées                        │
  │                                                                          │
  │  ② Enrichir l'agent avec une couche RAG                                  │
  │     Quand une question arrive :                                          │
  │       a. Chercher les 3 questions les plus similaires dans Aurora         │
  │       b. Injecter les paires (question → SQL validé) dans le prompt      │
  │       c. Le LLM s'en inspire pour générer un SQL plus précis             │
  │                                                                          │
  │  ③ Ajouter un mécanisme de feedback dans le Chat UI                      │
  │     👍 / 👎 sur chaque réponse                                           │
  │     → les réponses validées alimentent la base d'exemples                │
  │     → les mauvaises réponses sont exclues                                │
  └──────────────────────────────────────────────────────────────────────────┘

  Ce qu'on débloque
  ─────────────────
  ✓ Le système s'améliore avec l'usage
  ✓ Les questions fréquentes sont traitées avec une précision quasi-parfaite
  ✓ L'historique de conversation est persisté entre sessions
  ✓ On peut auditer les paires question→SQL pour détecter les dérives
  ✓ Base pour un fine-tuning futur du modèle


  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


  RÉCAPITULATIF — LA PROGRESSION COMPLÈTE
  ────────────────────────────────────────

   DÉPART             NIV.1             NIV.2             NIV.3
  ┌────────┐         ┌──────┐          ┌──────┐          ┌──────┐
  │ S3     │         │      │          │      │          │      │
  │ Glue   │──────── │  La  │ ──────── │  Le  │ ──────── │  La  │
  │ Athena │         │Torche│          │ Feu  │          │Forge │
  │ dbt    │         │      │          │Maît. │          │      │
  │ EKS    │         └──────┘          └──────┘          └──────┘
  └────────┘         1ère conv.        LLM comprend      Métriques
                     en français       les colonnes      cohérentes


   NIV.3             NIV.4             NIV.5
  ┌──────┐          ┌──────┐          ┌──────┐
  │      │          │      │          │      │
  │  La  │ ──────── │  L'  │ ──────── │  L'  │
  │Forge │          │Acier │          │Armure│
  │      │          │      │          │      │
  └──────┘          └──────┘          └──────┘
  Métriques         API unique        Mémoire +
  cohérentes        tous outils       apprentissage


  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


  CE QUI S'AJOUTE À CHAQUE NIVEAU
  ────────────────────────────────

  Niveau  Ajout                            Effort   Nouveau service ?
  ──────  ──────────────────────────────── ──────   ─────────────────
    1     Bedrock activé + Agent + Chat UI  Moyen   Oui (Agent + UI)
    2     Descriptions dbt + persist_docs   Faible  Non  ← le plus rentable
    3     semantic_models + metrics dbt     Élevé   Non
    4     Cube.dev sur EKS                  Moyen   Oui (Cube)
    5     pgvector + RAG + feedback         Moyen   Non (Aurora existe)

  ※ On peut s'arrêter à n'importe quel niveau — chacun est en production.
  ※ Le Niveau 2 est le meilleur rapport effort/qualité.
  ※ Le Niveau 3 est le plus structurant — il survit à tout changement d'outil.
  ※ Passer de 1 à 2 ne nécessite aucune modification de l'infra ni du code.
```
