spark-operator:
  hook:
    upgradeCrd: true

  spark:
    jobNamespaces: ["spark"]
    serviceAccount:
      name: spark-jobs
      annotations:
        eks.amazonaws.com/role-arn: "${role_iam_arn}"

  prometheus:
    podMonitor:
      create: true
