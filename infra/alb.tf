resource "helm_release" "aws_load_balancer_controller" {
  name       = "aws-load-balancer-controller"
  namespace  = "kube-system"
  repository = "https://aws.github.io/eks-charts"
  chart      = "aws-load-balancer-controller"
  version    = "3.1.0"
  wait       = true
  atomic     = true

  set {
    name  = "clusterName"
    value = local.prefix
  }

  set {
    name  = "region"
    value = local.region
  }

  set {
    name  = "vpcId"
    value = local.vpc_id
  }

  set {
    name  = "serviceAccount.create"
    value = "true"
  }

  set {
    name  = "serviceAccount.name"
    value = "aws-load-balancer-controller"
  }

  set {
    name  = "serviceAccount.annotations.eks\\.amazonaws\\.com/role-arn"
    value = aws_iam_role.aws_lb_controller.arn
  }
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
