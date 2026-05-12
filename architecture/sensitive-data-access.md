# 🔬 DONNÉE SENSIBLE — Les niveaux de protection

> Paie des employés. TJ des consultants. Données RH et financières.
> Ce document décrit **la méthode** pour intégrer de la donnée sensible dans la
> plateforme — indépendamment des outils AWS. Il couvre trois problèmes distincts :
> comment isoler la donnée, comment permettre aux devs de travailler dessus sans
> y accéder, et comment faire en sorte que les jobs soient les seuls intermédiaires.

---

```
╔══════════════════════════════════════════════════════════════════════════════╗
║  CE QUI EXISTE DÉJÀ SUR LA PLATEFORME                                       ║
║                                                                              ║
║  ★  IAM Identity Center (SSO)                                               ║
║  ★  tracking-data-access — log des read_actions Athena dans audit/          ║
║  ★  S3 chiffré · versionné · accès public bloqué                            ║
║  ★  IRSA — chaque job a son rôle IAM dédié (≠ identité humaine)            ║
║                                                                              ║
║  ⚠  athena_user_role donne s3:GetObject sur tous les buckets.               ║
║     Quiconque assume ce rôle peut lire les fichiers Parquet                 ║
║     sans passer par Athena et sans laisser de trace dans l'audit.           ║
╚══════════════════════════════════════════════════════════════════════════════╝


  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  QUESTION PRÉLIMINAIRE — Un bucket ou deux ?
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  IAM permet de restreindre l'accès à un préfixe S3 :

    s3://hymaia-datalake-mart/public/*    → tout le monde
    s3://hymaia-datalake-mart/sensitive/* → rôles autorisés uniquement

  C'est techniquement suffisant pour le contrôle d'accès.
  Un seul bucket fonctionne, à condition d'accepter deux contraintes :

  ┌──────────────────────────────────────────────────────────────────────────┐
  │  Contrainte 1 — Le chiffrement                                           │
  │  KMS s'applique par bucket, pas par préfixe. Pour utiliser une clé       │
  │  différente sur la donnée sensible (recommandé), il faut soit un bucket  │
  │  séparé, soit du chiffrement par objet (gérable mais plus complexe).     │
  │                                                                          │
  │  Contrainte 2 — La surface d'erreur                                      │
  │  Une policy IAM avec un wildcard mal écrit peut accidentellement         │
  │  exposer le préfixe sensible. Avec deux buckets, une erreur sur le       │
  │  bucket public n'affecte pas le bucket sensible.                         │
  └──────────────────────────────────────────────────────────────────────────┘

  Recommandation : préfixe séparé si on accepte une clé KMS partagée et
  une vigilance accrue sur les policies. Bucket séparé si on veut une clé
  KMS dédiée et une isolation sans risque de contamination par erreur.

  ※ Ce document fonctionne dans les deux cas. La suite parle de "préfixe
    sensible" — remplacer par "bucket sensible" si vous choisissez la
    séparation physique.


                                    │
                                    ▼


╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║   NIVEAU  1                                                                  ║
║   ▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔                                              ║
║   « LA FRONTIÈRE »                                                           ║
║   Séparer la donnée sensible et bloquer l'accès direct                      ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝

  ┌──────────────────────────────────────────────────────────────────────────┐
  │  Ce qu'il faut faire                                                     │
  │                                                                          │
  │  ① Créer le préfixe sensitive/ dans le bucket mart                       │
  │     mart/public/*     → accès actuel, inchangé                           │
  │     mart/sensitive/*  → nouveau, fermé par défaut                        │
  │                                                                          │
  │  ② Base Glue séparée : sensitive_mart                                    │
  │     → les tables sensibles ne sont pas dans hymaia_datalake_mart         │
  │                                                                          │
  │  ③ Modifier athena_user_role : retirer s3:GetObject sur sensitive/*       │
  │     C'est le correctif immédiat sur l'infra existante.                   │
  │     Les humains avec ce rôle ne peuvent plus lire la donnée sensible.    │
  │                                                                          │
  │  ④ Athena workgroup dédié : sensitive-data                               │
  │     enforce_workgroup_configuration = true                               │
  │     → les requêtes sur sensitive_mart passent uniquement par ce          │
  │       workgroup, traçables séparément dans l'audit existant ★            │
  └──────────────────────────────────────────────────────────────────────────┘

  Ce qu'on débloque                       Problème suivant
  ─────────────────                       ────────────────
  ✓ Donnée sensible inaccessible          → Les jobs (Spark, Polars, dbt)
    aux rôles humains existants             ont besoin d'y accéder
  ✓ L'audit ★ couvre déjà les requêtes    → Les devs ont besoin de connaître
    Athena — le workgroup dédié les         le schéma et de tester
    isole dans un compartiment distinct


                                    │
                         ┌──────────┘
                         │
                         ▼


╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║   NIVEAU  2                                                                  ║
║   ▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔                                              ║
║   « LES DEUX CLÉS »                                                          ║
║   Jobs et humains : deux identités distinctes, deux niveaux d'accès         ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝

  Problème à résoudre
  ───────────────────
  Un dev écrit le code du job Spark qui lit la paie.
  Le job doit pouvoir lire la donnée réelle.
  Le dev ne doit pas pouvoir lire la donnée réelle.
  Ce n'est pas une contradiction — ce sont deux identités différentes.

  ┌──────────────────────────────────────────────────────────────────────────┐
  │  Le principe                                                             │
  │                                                                          │
  │  Identité humaine  ≠  Identité du job                                   │
  │  (rôle SSO)           (rôle IRSA du pod K8s)                            │
  │                                                                          │
  │  Le dev écrit le code → soumet via PR → merge → Dagster lance le job    │
  │  Le job tourne sous son rôle IRSA → accède à sensitive/*                │
  │  Le dev, lui, n'a jamais assumed ce rôle → ne voit rien                 │
  │                                                                          │
  │  C'est exactement le même modèle que CI/CD :                            │
  │  un dev qui écrit un script de déploiement ne peut pas déployer         │
  │  lui-même en prod — la pipeline CI/CD le fait à sa place.               │
  └──────────────────────────────────────────────────────────────────────────┘

  Architecture des rôles
  ──────────────────────

  Rôle humain (SSO → IAM)          Rôle job (IRSA → pod K8s)
  ──────────────────────────────   ──────────────────────────────────────
  s3:GetObject  mart/public/*  ✓   s3:GetObject  mart/sensitive/*  ✓
  s3:GetObject  mart/sensitive/* ✗ s3:GetObject  mart/public/*     ✓
  glue:GetTable sensitive_mart  ✗  glue:GetTable sensitive_mart    ✓
                                   glue:GetTable hymaia_datalake_* ✓
                                   s3:PutObject  mart/sensitive/*  ✓ (dbt)

  ┌─────────────────────────────────────────────────────────────────────────┐
  │  Dev                                                                    │
  │   └─ écrit  dbt/models/sensitive/payroll_mart.sql                       │
  │   └─ PR → review → merge                                                │
  │   └─ Dagster lance le job sous rôle IRSA "dbt-sensitive-writer"         │
  │         └─ lit  mart/sensitive/raw/payroll.parquet   ✓                  │
  │         └─ écrit mart/sensitive/mart/payroll_mart/   ✓                  │
  │   └─ Le dev ne voit que le code et les logs Dagster                     │
  │         └─ les logs ne doivent PAS afficher les valeurs                 │
  │            → utiliser des counts/stats, pas de print(row)               │
  └─────────────────────────────────────────────────────────────────────────┘

  ⚠  Risque résiduel : le dev peut écrire un job qui logue ou copie
     la donnée sensible vers un endroit accessible.
     Mitigation : revue de code obligatoire (PR) sur les pipelines
     sensibles + IRSA du job limité en écriture (mart/sensitive/* uniquement,
     pas d'écriture vers mart/public/*).

  Ce qu'on débloque                       Problème suivant
  ─────────────────                       ────────────────
  ✓ Les jobs accèdent à la vraie donnée   → Le dev ne peut pas tester son
  ✓ Les devs n'y accèdent pas              code sans données : comment
  ✓ Séparation nette dans les rôles IAM    écrire et valider un pipeline
                                           sur de la donnée sensible ?


                                    │
                         ┌──────────┘
                         │
                         ▼


╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║   NIVEAU  3                                                                  ║
║   ▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔                                              ║
║   « LA MAQUETTE »                                                            ║
║   Permettre aux devs de travailler sans voir la vraie donnée                ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝

  Problème à résoudre
  ───────────────────
  Un dev doit écrire un job dbt/Spark/Polars sur la paie.
  Il a besoin de :
    ① connaître le schéma (noms de colonnes, types, relations)
    ② tester que son code fonctionne
    ③ voir des données réalistes pour valider la logique métier
  Sans avoir accès aux vraies données.

  Trois outils répondent à ces trois besoins
  ────────────────────────────────────────────

  ┌──────────────────────────────────────────────────────────────────────────┐
  │  ① Le schéma → dbt _schema.yml  (contrat de données)                    │
  │                                                                          │
  │  models:                                                                 │
  │    - name: payroll                                                       │
  │      description: "1 ligne par employé par mois"                        │
  │      columns:                                                            │
  │        - name: employee_id      type: VARCHAR                            │
  │        - name: department       type: VARCHAR                            │
  │        - name: gross_salary     type: DECIMAL   description: "Brut €"   │
  │        - name: net_salary       type: DECIMAL   description: "Net €"    │
  │        - name: month            type: DATE                               │
  │                                                                          │
  │  Le dev connaît le schéma complet sans voir une seule valeur.           │
  │  Le schéma est dans Git, versionné, consultable par tous.               │
  └──────────────────────────────────────────────────────────────────────────┘

  ┌──────────────────────────────────────────────────────────────────────────┐
  │  ② Le test → données synthétiques générées par un job Dagster            │
  │                                                                          │
  │  Un asset Dagster "sensitive_synthetic_data" :                           │
  │    - lit le schéma depuis le _schema.yml dbt                             │
  │    - génère N lignes de données fake cohérentes (Faker / Mimesis)        │
  │    - écrit dans mart/sensitive_dev/*  (préfixe dev séparé)              │
  │    - accessible aux devs via leur rôle SSO                               │
  │                                                                          │
  │  Les données synthétiques ressemblent aux vraies :                       │
  │    employee_id: "EMP-4821"  department: "Engineering"                    │
  │    gross_salary: 4750.00    net_salary: 3612.00    month: 2024-03-01     │
  │                                                                          │
  │  Elles sont dans Git / Dagster — pas de donnée réelle exposée.          │
  └──────────────────────────────────────────────────────────────────────────┘

  ┌──────────────────────────────────────────────────────────────────────────┐
  │  ③ La validation → dbt tests sur les données synthétiques               │
  │                                                                          │
  │  Le dev lance dbt test contre mart/sensitive_dev/*                       │
  │  Les mêmes tests tournent en prod contre mart/sensitive/*                │
  │  Le comportement est identique — seul le préfixe change.                │
  └──────────────────────────────────────────────────────────────────────────┘

  Résultat
  ────────

   Dev                        CI/CD (Dagster)             Prod
   ──────────────────────     ──────────────────────────  ────────────────
   Lit _schema.yml ✓          Lance le job sous IRSA      Job tourne avec
   Travaille sur              accès mart/sensitive/*       les vraies données
   mart/sensitive_dev/* ✓     Lance dbt test              Devs ne voient
   Ne voit pas                contre mart/sensitive/*      jamais les valeurs
   mart/sensitive/* ✗

  Ce qu'on débloque
  ─────────────────
  ✓ Dev peut travailler normalement sans voir une seule valeur réelle
  ✓ Les données synthétiques sont cohérentes → tests métier valides
  ✓ La frontière dev/prod est dans IAM, pas dans la confiance humaine
  ✓ Le schéma est la source de vérité partagée entre RH et data


                                    │
                         ┌──────────┘
                         │
                         ▼


╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║   NIVEAU  4                                                                  ║
║   ▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔                                              ║
║   « LES CLÉS »                                                               ║
║   Définir qui, parmi les humains autorisés, voit quoi                       ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝

  Problème à résoudre
  ───────────────────
  Certains humains DOIVENT voir la vraie donnée : RH pour la paie,
  direction pour les TJ. Il faut des règles d'accès granulaires.

  Le modèle d'autorisation à définir en premier  (indépendant de l'outil)
  ────────────────────────────────────────────────────────────────────────

  ┌─────────────────────────────────────────────────────────────────────────┐
  │  Qui                    Voit quoi                   Via                 │
  │  ─────────────────────  ─────────────────────────── ───────────────────│
  │  hymaia-hr-team         sensitive_mart.payroll       vue complète       │
  │  hymaia-finance-team    sensitive_mart.tj_rates      sans colonnes PII  │
  │  hymaia-exec-team       agrégats par département     vue aggrégée       │
  │  hymaia-data-admins     tout                         lecture + écriture │
  └─────────────────────────────────────────────────────────────────────────┘

  Outil selon la granularité requise
  ────────────────────────────────────

  ┌──────────────────────────────────────────────────────────────────────────┐
  │  TABLE entière (oui/non) → IAM policies + rôles SSO                     │
  │  Effort faible · zéro nouveau service · cloud-agnostique                 │
  │                                                                          │
  │  COLONNE masquée → Vues dbt par profil d'accès  ← recommandé départ     │
  │  sensitive_mart.payroll_hr_view     → toutes colonnes                   │
  │  sensitive_mart.payroll_exec_view   → department, salary_total           │
  │  Versionné dans Git · 100% cloud-agnostique · lisible par tous          │
  │                                                                          │
  │  LIGNE filtrée (manager voit son équipe) → vue dbt + variable           │
  │  WHERE department = '{{ var("department") }}'                            │
  │  ou → Open Policy Agent (OPA) sur EKS : policy-as-code dans Git         │
  │                                                                          │
  │  GOUVERNANCE CENTRALISÉE (> 5 tables, > 3 profils)                      │
  │  → OPA sur EKS : même pattern que les autres outils, ArgoCD, Git        │
  │  → AWS Lake Formation si lock-in AWS assumé et équipe ops mature         │
  │  → Apache Ranger si stack Spark lourde déjà en place                    │
  └──────────────────────────────────────────────────────────────────────────┘


  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


  VUE COMPLÈTE — LES TROIS PROBLÈMES ET LEURS SOLUTIONS
  ──────────────────────────────────────────────────────

  ┌───────────────────────┬──────────────────────────────────────────────────┐
  │  Problème             │  Solution                                        │
  ├───────────────────────┼──────────────────────────────────────────────────┤
  │  Isoler la donnée     │  Préfixe sensitive/* + Glue database séparée    │
  │                       │  + retirer s3:GetObject sensitive du rôle humain │
  ├───────────────────────┼──────────────────────────────────────────────────┤
  │  Jobs accèdent,       │  IRSA dédié par job (≠ rôle humain SSO)         │
  │  devs n'accèdent pas  │  Le job tourne sous son rôle, pas sous celui     │
  │                       │  du dev qui a écrit le code                      │
  ├───────────────────────┼──────────────────────────────────────────────────┤
  │  Devs travaillent     │  Contrat de schéma (dbt _schema.yml)             │
  │  sans voir la donnée  │  + données synthétiques dans préfixe _dev/*      │
  │  réelle               │  générées par un job Dagster (Faker/Mimesis)     │
  ├───────────────────────┼──────────────────────────────────────────────────┤
  │  Humains autorisés    │  Vues dbt par profil + IAM groups SSO            │
  │  voient leur périmètre│  (OPA si gouvernance à l'échelle)                │
  ├───────────────────────┼──────────────────────────────────────────────────┤
  │  Audit complet        │  Module tracking-data-access ★ étendu au        │
  │                       │  workgroup sensitive-data                        │
  └───────────────────────┴──────────────────────────────────────────────────┘


  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


  LA PROGRESSION COMPLÈTE
  ────────────────────────

   DÉPART             NIV.1              NIV.2              NIV.3
  ┌──────────────┐   ┌──────┐           ┌──────┐           ┌──────┐
  │ Tout le monde│   │  La  │           │  Les │           │  La  │
  │ voit tout    │── │Front.│ ────────  │2 clés│ ────────  │Maqu. │
  │ par défaut   │   │      │           │      │           │      │
  └──────────────┘   └──────┘           └──────┘           └──────┘
                     Isolation          IRSA job ≠          Schéma +
                     préfixe +          rôle humain         données
                     workgroup dédié    audit complet       synthétiques

   NIV.3              NIV.4
  ┌──────┐           ┌──────┐
  │  La  │           │  Les │
  │Maqu. │ ────────  │ Clés │
  │      │           │      │
  └──────┘           └──────┘
  Schéma +           Vues dbt
  données synth.     + IAM groups
                     (OPA si scale)


  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


  CE QUI S'AJOUTE À CHAQUE NIVEAU
  ────────────────────────────────

  Niv  Ce qu'on résout                   Déjà là ?     Effort  Service ?
  ───  ──────────────────────────────── ─────────────  ──────  ─────────
   1   Isolation préfixe + workgroup     Partiel ⚠     Faible  Non
       audit complet via module ★        audit ★ OK
   2   IRSA job ≠ rôle humain            Partiel ⚠     Faible  Non
       (IRSA existe, à spécialiser)      IRSA ★ exist.
   3   Schéma public + données synth.    Non           Moyen   Non
       pour les devs                                   (1 job Dagster)
   4   Vues dbt + IAM groups             Non           Moyen   Non
       accès granulaire pour humains                   (vues SQL)

  ※ Niveau 1 + 2 sont des modifications Terraform sur l'infra existante.
    Pas de nouveau service. Quelques heures de travail.

  ※ Niveau 3 est le plus structurant pour l'expérience dev.
    Un schéma bien écrit + un générateur de données fake = les devs
    travaillent normalement sans jamais toucher la vraie donnée.

  ※ Le risque résiduel à Niveau 2 : un dev peut écrire un job qui logue
    ou copie la vraie donnée vers un endroit accessible.
    La mitigation est organisationnelle : PR obligatoire sur les pipelines
    sensibles + IRSA du job en écriture sur sensitive/* uniquement.
```
