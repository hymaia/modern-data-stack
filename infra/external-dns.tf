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
