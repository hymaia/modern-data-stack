# ADR-014: External Secrets Operator pour la gestion des secrets Kubernetes

## Statut
Accepté

## Contexte
Les outils déployés sur K8s ont besoin de credentials (mots de passe de bases de données,
tokens…). Ces secrets ne doivent jamais apparaître en clair : ni dans Git, ni dans le
tfstate Terraform, ni dans les manifests K8s.

Il faut un mécanisme qui stocke les secrets dans un coffre-fort externe et les injecte
dans les namespaces K8s au moment du déploiement, sans qu'ils transitent par le repo.

## Décision
External Secrets Operator (v2.0.1) est déployé sur EKS. Il se connecte à AWS Secrets
Manager via IRSA et synchronise automatiquement les secrets dans les namespaces applicatifs.
Un `ClusterSecretStore` unique (`aws-secretsmanager`) sert tous les namespaces.

Les credentials sont générés par Terraform, stockés dans AWS Secrets Manager, et jamais
écrits dans Git ni dans les `values.yaml`.

Ce pattern est une bonne pratique de sécurité maîtrisée et déjà rencontrée sur le terrain —
il pourrait être challengé, mais il offre un bon niveau de confort et de sécurité.

## Options considérées

| Option | Pour | Contre |
|--------|------|--------|
| **External Secrets Operator** ✅ | Standard K8s, sync automatique, multi-backend, pas de secret en clair nulle part | Outil supplémentaire à opérer, lié à AWS Secrets Manager ici |
| Sealed Secrets (Bitnami) | GitOps-friendly — le secret chiffré est commitable dans Git | Clé de déchiffrement du cluster à protéger, rotation plus complexe |
| Secrets Store CSI Driver seul | Natif K8s, pas de copie en clair dans etcd | Moins flexible, pas de sync automatique vers K8s Secrets |
| Secrets en dur dans `values.yaml` / Git | Simple | Inacceptable — secrets exposés dans le repo |
| Secrets injectés depuis Terraform | Pas de dépendance supplémentaire | Secrets en clair dans le tfstate |

## Conséquences

**Positives :** Aucun secret en clair dans Git, le tfstate ou les manifests K8s. Rotation
automatique possible (le CSI Driver avec `enableSecretRotation: true` est également déployé
en complément). Pattern sécurisé et transférable chez les clients.

**Compromis / Risques :** Couplage à AWS Secrets Manager (spécifique au provider).
External Secrets Operator est un composant supplémentaire à maintenir sur le cluster.
Sealed Secrets aurait été une alternative plus GitOps-pure, mais moins familière.
