module "kubernetes" {
  source  = "jetbrains/kubernetes/aws"
  version = "v3.6.0"

  prefix = local.prefix

  tags = {
    Environment = "dev"
    ManagedBy   = "terraform"
  }

  cluster_version = "1.35"

  cluster_network_type = "internal"

  cluster_autoscaler_subnet_selector = "1"

  cluster_compute_pool_aws_managed = {
    defaults = {}
    groups = {
      main = {
        capacity_type = "SPOT"
        desired_size  = 3
        min_size      = 0
        max_size      = 5
        disk_size     = 100
        instance_types = ["t3a.xlarge", "t3.xlarge", "m5a.xlarge", "m6a.xlarge", "m6i.xlarge"]
        labels = {
          "node-type" = "spot"
        }
        update_config = {
          max_unavailable_percentage = 30
        }
        use_custom_launch_template = false
      }
    }
  }

  cluster_private_ingress_create = false
  cluster_public_ingress_create  = false

  cluster_additional_apps_create = true
  cluster_additional_apps = [
    {
      namespace  = "external-secrets"
      repository = "oci://ghcr.io/external-secrets/charts"
      app = {
        name             = "external-secrets"
        chart            = "external-secrets"
        version          = "2.0.1"
        create_namespace = true
        wait             = true
        atomic           = true
      }
      params = [
        { name = "installCRDs", value = "true" },
        { name = "serviceAccount.create", value = "true" },
        { name = "serviceAccount.name", value = "external-secrets" },
        {
          name  = "serviceAccount.annotations.eks\\.amazonaws\\.com/role-arn"
          value = aws_iam_role.external_secrets.arn
        },
      ]
    },
  ]
}


resource "helm_release" "secrets_store_csi_driver" {
  depends_on = [module.kubernetes]

  name       = "secrets-store-csi-driver"
  repository = "https://kubernetes-sigs.github.io/secrets-store-csi-driver/charts"
  chart      = "secrets-store-csi-driver"
  version    = "1.5.6"
  namespace  = "kube-system"
  wait       = true
  atomic     = true

  set {
    name = "syncSecret.enabled"
    value = "true"
  }
  set {
    name = "enableSecretRotation"
    value = "true"
  }
}


locals {
  oidc_issuer        = trimprefix(module.kubernetes.cluster[0].cluster_oidc_issuer_url, "https://")
  irsa_assume_policy = { for sa in [
    {
      name      = "aws-lb-controller"
      namespace = "kube-system"
      sa_name   = "aws-load-balancer-controller"
    },
    {
      name      = "external-dns"
      namespace = "kube-system"
      sa_name   = "external-dns"
    },
    {
      name      = "external-secrets"
      namespace = "external-secrets"
      sa_name   = "external-secrets"
    },
  ] : sa.name => jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Federated = "arn:aws:iam::${local.account_id}:oidc-provider/${local.oidc_issuer}" }
      Action    = "sts:AssumeRoleWithWebIdentity"
      Condition = {
        StringEquals = {
          "${local.oidc_issuer}:sub" = "system:serviceaccount:${sa.namespace}:${sa.sa_name}"
          "${local.oidc_issuer}:aud" = "sts.amazonaws.com"
        }
      }
    }]
  }) }
}

resource "aws_iam_role" "aws_lb_controller" {
  name               = "${local.prefix}-aws-lb-controller"
  assume_role_policy = local.irsa_assume_policy["aws-lb-controller"]
}

resource "aws_iam_policy" "aws_lb_controller" {
  name   = "${local.prefix}-aws-lb-controller"
  policy = file("${path.module}/policies/aws-lb-controller.json")
}

resource "aws_iam_role_policy_attachment" "aws_lb_controller" {
  role       = aws_iam_role.aws_lb_controller.name
  policy_arn = aws_iam_policy.aws_lb_controller.arn
}

resource "aws_iam_role" "external_dns" {
  name               = "${local.prefix}-external-dns"
  assume_role_policy = local.irsa_assume_policy["external-dns"]
}

resource "aws_iam_role_policy" "external_dns" {
  name = "${local.prefix}-external-dns"
  role = aws_iam_role.external_dns.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["route53:ChangeResourceRecordSets"]
        Resource = ["arn:aws:route53:::hostedzone/*"]
      },
      {
        Effect   = "Allow"
        Action   = ["route53:ListHostedZones", "route53:ListResourceRecordSets", "route53:ListTagsForResource"]
        Resource = ["*"]
      },
    ]
  })
}

resource "aws_iam_role" "external_secrets" {
  name               = "${local.prefix}-external-secrets"
  assume_role_policy = local.irsa_assume_policy["external-secrets"]
}

resource "aws_iam_role_policy" "external_secrets" {
  name = "${local.prefix}-external-secrets"
  role = aws_iam_role.external_secrets.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "secretsmanager:GetResourcePolicy",
        "secretsmanager:GetSecretValue",
        "secretsmanager:DescribeSecret",
        "secretsmanager:ListSecretVersionIds",
        "secretsmanager:ListSecrets",
        "ssm:GetParameter",
        "ssm:GetParameters",
        "ssm:GetParametersByPath",
        "ssm:DescribeParameters",
        "kms:Decrypt",
      ]
      Resource = ["*"]
    }]
  })
}
