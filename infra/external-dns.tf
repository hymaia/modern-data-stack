resource "helm_release" "external_dns" {
  depends_on = [module.kubernetes]

  name       = "external-dns"
  repository = "https://kubernetes-sigs.github.io/external-dns"
  chart      = "external-dns"
  version    = "1.20.0"
  namespace  = "kube-system"
  wait       = true
  atomic     = true

  set {
    name = "provider"
    value = "aws"
  }
  set {
    name = "aws.region"
    value = local.region
  }
  set {
    name = "aws.zoneType"
    value = "public"
  }
  set {
    name = "txtOwnerId"
    value = local.prefix
  }
  set {
    name = "serviceAccount.create"
    value = "true"
  }
  set {
    name = "serviceAccount.name"
    value = "external-dns"
  }
  set {
    name  = "serviceAccount.annotations.eks\\.amazonaws\\.com/role-arn"
    value = aws_iam_role.external_dns.arn
  }
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
