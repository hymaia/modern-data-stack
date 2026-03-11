# Modern Data Stack

How to deploy your stack ?

## Prerequisite

Install :
* terraform >=1.14
* helm 4
* kubectl >=1.35
* uv >= 0.5.7
* docker
* awscli

## Deploy infra

### Prerequisites

1. You have to be authenticated to your AWS account.
2. You must update the hostnames in template files in `infra/templates/` folder corresponding to your own domain name.

### Deploy

```bash
cd infra
terraform init
terraform apply
```

This apply will create files in `apps/` folder, used to deploy argo apps.

### Kubernetes

In your Kubernetes cluster, you will have a lot of useful additional apps. An example is `external-dns` !
This app will detect all ingress apply and automatically creates a record DNS in the corresponding zone DNS in Route 53.

For the other apps, you should read the code and the jetbrain's [terraform kubernetes module documentation](https://registry.terraform.io/modules/JetBrains/kubernetes/aws/latest).

## Build and push container image for dbt

### Prerequisites

Get access to ECR :

```bash
aws ecr get-login-password --region <region> | docker login --username AWS --password-stdin <accountid>.dkr.ecr.<region>.amazonaws.com
```

### Deploy discover-dagster

This package is a simple example to understand how dagster works.

```bash
cd discover-dagster
docker build -t 662195598891.dkr.ecr.eu-west-1.amazonaws.com/hymaia/discover-dagster:latest .
docker push 662195598891.dkr.ecr.eu-west-1.amazonaws.com/hymaia/discover-dagster:latest
```

### Deploy dbt

This package is a real usecase for dagster to transform data using dbt from github and create a dashboard in metabase.

```bash
cd discover-dagster
docker build -t 662195598891.dkr.ecr.eu-west-1.amazonaws.com/hymaia/github-dbt-project:latest .
docker push 662195598891.dkr.ecr.eu-west-1.amazonaws.com/hymaia/github-dbt-project:latest
```

## Deploy argo apps

### Prerequisites

1. Deploy the infra with terraform
2. You have to be authenticated to your eks cluster.

```bash
aws eks update-kubeconfig --name <cluster-name>
```

### Commit the changes

If you have changed helm charts in `apps/` folder, commit it.

### Deploy applications

If you have forked this repository, update the github url value in the manifest in `argocd/` folder.

```bash
kubectl apply -f argocd/
```

Go to your argocd webapp, you will see all your apps deploying. To find the url :

```bash
kubectl get ingress -n argocd
```

And copy the `HOSTS` value.

It deploys :

* Airbyte : use a graphic interface to create raw data ingestion from an app to an output, existing in their marketplace.
* Dagster : orchestrate and create data transformation pipelines
* Metabase : create dashboard
* External secret store : create a secret in Kubernetes from a secret in AWS Secret Manager

## Get the access of the webapps

### Get URLs

To know the url of each of your apps :

```bash
kubectl get ingress --all-namespaces
```

### Get ArgoCD credentials

The default username is `admin`.

To get the password, run :

```bash
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d
```

### Get Dagster credentials

The default username is `admin`.

To get the password, run :

```bash
kubectl -n dagster get secret dagster-postgresql-secret -o jsonpath="{.data.postgresql-password}" | base64 -d
```

### Get airbyte credentials

The default username is `admin`.

To get the password, run :

```bash
kubectl -n airbyte get secret airbyte-auth-secrets -o jsonpath="{.data.instance-admin-password}" | base64 -d
```

If you want to use the dbt package, create a connection between github and AWS datalake.

### Get metabase credentials

Go to metabase webapp and create your first account.
