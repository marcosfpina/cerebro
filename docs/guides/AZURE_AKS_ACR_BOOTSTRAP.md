# Azure AKS + ACR Bootstrap

## Objetivo

Provisionar o mínimo para publicar a imagem do Cerebro em um `Azure Container Registry` e fazer deploy em `AKS` usando GitHub Actions.

## Arquivos envolvidos

- Bootstrap de infraestrutura: `scripts/bootstrap-azure-aks-acr.sh`
- Workflow de push para ACR: `.github/workflows/deploy-acr.yml`
- Workflow de deploy para AKS: `.github/workflows/deploy-aks.yml`
- Manifest AKS: `kubernetes/aks-deployment.yaml` e `kubernetes/aks-service.yaml`

## Uso

Rode o bootstrap:

```bash
chmod +x scripts/bootstrap-azure-aks-acr.sh
./scripts/bootstrap-azure-aks-acr.sh
```

Ele cria:

- `Resource Group`
- `ACR`
- `AKS`
- `Service Principal` para `AZURE_CREDENTIALS`
- `GitHub Actions vars` se `gh` estiver autenticado

## Variáveis esperadas no GitHub

- `AZURE_ACR_NAME`
- `AZURE_ACR_LOGIN_SERVER`
- `AZURE_ACR_REPOSITORY`
- `AZURE_RESOURCE_GROUP`
- `AZURE_AKS_NAME`
- `AZURE_AKS_NAMESPACE` opcional, default `default`
- `AZURE_AKS_SECRET_NAME` opcional, default `cerebro-env`
- secret `AZURE_CREDENTIALS`
- secret `SOPS_AGE_KEY`

## Fluxo recomendado de produção

1. Rode o bootstrap Azure para criar `ACR`, `AKS` e popular as vars do GitHub.
2. Gere sua chave `age`, atualize `.sops.yaml` se necessário e versione `secrets/cerebro.enc.env`.
3. Dispare `.github/workflows/deploy-acr.yml` para publicar a imagem no `ACR`.
4. Dispare `.github/workflows/deploy-aks.yml` com:
   - `build_image=true` para pipeline completa
   - `build_image=false` e `image_tag=<tag>` para promover imagem já publicada
5. Use o resumo do workflow para confirmar `image ref`, namespace e rollout.

## Segredos de runtime com SOPS

O deploy para AKS agora espera um arquivo criptografado no repositório:

- `secrets/cerebro.enc.env`

Fluxo:

```bash
mkdir -p secrets
cp config/examples/cerebro.secrets.env.example secrets/cerebro.enc.env
nix develop --command sops encrypt --in-place secrets/cerebro.enc.env
```

No GitHub:

- adicione a chave privada `age` em `SOPS_AGE_KEY`
- mantenha o arquivo criptografado versionado no repo

No workflow:

- o runner decripta o arquivo com `nix develop --command sops decrypt`
- cria/atualiza o `Secret` Kubernetes
- faz rollout do `Deployment` consumindo `envFrom.secretRef`

## Bootstrap com variáveis customizadas

Você pode rodar tudo já com nomes finais:

```bash
SUBSCRIPTION_ID="xxxx-xxxx-xxxx" \
RESOURCE_GROUP="rg-cerebro-prod" \
LOCATION="eastus" \
ACR_NAME="cerebroprodacr" \
ACR_REPOSITORY="cerebro" \
AKS_NAME="aks-cerebro-prod" \
AKS_NAMESPACE="cerebro" \
AKS_SECRET_NAME="cerebro-env" \
GITHUB_OWNER="minhaorg" \
GITHUB_REPO="cerebro" \
./scripts/bootstrap-azure-aks-acr.sh
```

## Build publicado

O workflow usa o output Nix:

```bash
nix build .#dockerImage
docker load < result
```

Por padrão, `.#dockerImage` aponta para a imagem Azure validada no `flake`.
