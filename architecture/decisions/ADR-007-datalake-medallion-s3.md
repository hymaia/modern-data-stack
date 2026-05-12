# ADR-007: Architecture Médaillon (raw / staging / mart) sur S3

## Statut
Accepté

## Contexte
La plateforme a besoin d'un modèle de stockage pour les données. Il faut organiser les
données selon leur niveau de maturité (brut → nettoyé → agrégé) pour permettre à chaque
outil de travailler sur la couche qui lui correspond, et garantir la traçabilité depuis
la source jusqu'à la restitution.

## Décision
Le Data Lake est structuré en 3 couches S3 selon le pattern **Médaillon**, chacune
chiffrée (AES-256), versionnée et bloquée en accès public :

- **raw** (`hymaia-datalake-raw`) : données brutes telles que reçues des sources.
  Tous les outils peuvent y écrire tant que ça correspond à une récupération brute
  (Airbyte, Spark, Glue jobs…).
- **staging** (`hymaia-datalake-staging`) : données nettoyées, typées et conformées
  selon la définition standard du médaillon.
- **mart** (`hymaia-datalake-mart`) : agrégats et modèles métier prêts pour la
  consommation BI.

S3 est choisi pour son coût bas et parce qu'il répond aux besoins de cette plateforme.
Un Data Warehouse (ex. ClickHouse) peut être ajouté en complément si un projet nécessite
des performances de requête plus élevées — les deux approches ne sont pas exclusives.

## Options considérées

| Option | Pour | Contre |
|--------|------|--------|
| **Médaillon 3 couches sur S3** ✅ | Coût bas, découplé du moteur de requête, flexible sur les formats et outils | Performances moindres qu'un DWH, pas d'ACID natif |
| Data Warehouse (Redshift, Snowflake, ClickHouse) | Très performant, SQL natif, ACID | Coût fixe élevé, vendor lock-in, répond à d'autres besoins |
| 2 couches (raw / mart) | Plus simple | Perd la séparation entre conforming et agrégation métier |
| Lakehouse ACID (Delta Lake / Iceberg) | ACID, time travel, upserts | Complexité opérationnelle supplémentaire |

## Conséquences

**Positives :** Coût maîtrisé (pay-as-you-go sur S3). Séparation claire des responsabilités
entre couches. Chaque outil intervient sur la couche qui lui correspond. Extensible :
un DWH ou un format table ACID (Iceberg) peut être ajouté par-dessus sans remettre en
cause le modèle.

**Compromis / Risques :** Pas de garanties ACID sur les fichiers bruts. Les performances
de requête dépendent d'Athena et du partitionnement — insuffisant pour des cas d'usage
temps-réel ou à très haute fréquence.
