# Linknest GCP Terraform 实验

中文 | [English](README.en.md)

本目录保存 Google Cloud 的 Terraform 配置，独立于 `../aws/sandbox`，两边分别初始化、使用各自的 Provider 和 state。

## 当前状态

2026-10-26 已完成首次「创建 → 验证 → 清理」：Cloud Run sandbox 创建成功，健康检查、分类及认证／输入校验通过，部署后 plan 无差异，随后删除 sandbox。原服务 `linknest-classifier-service` 保留。

**目前配置保留，但实验服务已删除。再次执行 apply 会重新创建服务。** 后续练习先解释并审阅每一步，再执行。

## 目录与文件

实际 Terraform 根目录是 [`sandbox/`](sandbox/)，命令应在该目录执行：

| 文件 | 作用 |
| --- | --- |
| [sandbox/versions.tf](sandbox/versions.tf) | Terraform 版本约束、Google Provider 版本约束 |
| [sandbox/providers.tf](sandbox/providers.tf) | 项目 `linknest-gcp-lab`、区域 `australia-southeast1` |
| [sandbox/main.tf](sandbox/main.tf) | 声明新的 Cloud Run 服务及运行配置 |
| [sandbox/.terraform.lock.hcl](sandbox/.terraform.lock.hcl) | 锁定选中的 Google Provider 版本；本次为 7.46.2 |
| `sandbox/terraform.tfstate` | 本地资源登记，Git 忽略，不手动编辑 |
| `sandbox/.terraform/` | 初始化缓存及 Provider 安装，Git 忽略 |

当前 GCP 配置直接填写资源引用，没有 AWS 目录中的 `variables.tf`、`terraform.tfvars` 或 `smoke_test.py`。

## 创建与复用范围

只管理一个资源：`google_cloud_run_v2_service.classifier_sandbox`，云端名称为 `linknest-classifier-tf-sandbox`。

- 复用现有 Artifact Registry 镜像，固定到 digest；不构建或上传镜像。
- 复用运行账号 `linknest-run`、Secret `linknest-service-api-key` 的版本 1，以及模型桶 `linknest-gcp-lab-model-360990832014`。
- 模型桶以只读方式挂载到 `/app/model`；Secret 以引用方式注入 `SERVICE_API_KEY`，不把密钥值写入配置。
- 容器端口 8000，1 vCPU、2 GiB 内存，请求超时 300 秒。
- 保留 Cloud Run IAM 调用检查；URL 可接收互联网流量不等于允许匿名调用。
- 不创建或管理原服务、共享桶、镜像仓库、Secret、运行账号及其 IAM 授权。

## 本机认证与静态检查

Terraform 已安装到 `~/.local/bin/terraform`。先进入实际根目录：

```bash
cd /Users/sha/Code/AI-code-26/练习JS-TS/AI现在项目/6.3-linknest-python-classifier-service/infra/gcp/sandbox
terraform version
terraform fmt -check
terraform init -backend=false
terraform validate
```

`init` 安装 Provider，`validate` 检查配置；这些操作不部署 Cloud Run。部署使用本地 state，没有配置远程 backend。

本机 Terraform 使用 ADC；需要配置或更新身份时使用：

```bash
gcloud auth application-default login
gcloud auth application-default set-quota-project linknest-gcp-lab
```

这是 Terraform 使用的凭据。`gcloud` 命令的 CLI 登录由 `gcloud auth login` 单独管理；CLI 也不读取 providers.tf 中的项目设置。

## 重新部署的步骤

以下是未来重建时的操作说明，当前不需要执行：

```bash
terraform init
terraform plan -out=tfplan
```

审阅计划，预期只新增一个 sandbox 服务，原服务及共享资源没有修改或删除。确认身份拥有部署和复用依赖所需权限后，才执行：

```bash
terraform apply tfplan
```

应用保存的计划不会再询问确认。旧计划可能已失效，每次重建应生成新计划。

## 验证与查看

在已登录且有调用权限的 Cloud Shell 或本机 gcloud 环境中，查询新服务当前 URL：

```bash
gcloud run services describe linknest-classifier-tf-sandbox \
  --project=linknest-gcp-lab \
  --region=australia-southeast1 \
  --format='value(status.url)'
```

本次通过 Cloud Shell 中逐条执行 curl 验证，没有使用 AWS 的 smoke_test.py：

| 测试 | 本次结果 |
| --- | --- |
| 带有效 Google 身份请求 `/health` | 200，`model_loaded: true` |
| 有效 Google 身份及 API Key 请求 `/classify` | 正常分类，Technology／0.4478 |
| 有效 Google 身份、错误 API Key | 401 |
| 不带 Google 身份请求 `/health` | 403 |
| 有效身份与 API Key、空标题 | 422 |

不要打印或提交 token、API Key、凭据文件。部署后运行 `terraform plan` 核对无差异。查看 Terraform 保存的资源记录：

```bash
terraform state list
terraform state show google_cloud_run_v2_service.classifier_sandbox
```

state 是保存的记录；实时状态到 Google Cloud Console → Cloud Run → Services 查询。当前 sandbox 已删除，state list 应为空，state show 不再有该资源。

## 清理

仅在 sandbox 重新创建后需要删除时使用：

```bash
terraform plan -destroy -out=destroy.tfplan
```

审阅完整删除范围，确认只删除 sandbox，再执行：

```bash
terraform apply destroy.tfplan
terraform state list
```

保留共享模型桶、Secret、镜像、运行账号及原服务。不要将 `.terraform/`、state、计划文件或凭据提交到 Git；保留 `.tf` 配置和 `.terraform.lock.hcl`。

## 完整实操记录

本机学习资料仓库包含更完整的操作、截图和问答：

- [GCP 实践 TODO](../../../../学习-相关/云与认证/Terraform/GCP-terraform/2026-10-26-Linknest-GCP-Terraform实践TODO.md)
- [GCP 实操笔记](../../../../学习-相关/云与认证/Terraform/GCP-terraform/2026-10-26-Linknest-GCP-Terraform实操笔记.md)

以上两个链接依赖当前多仓库工作区布局，单独克隆分类器仓库时不会包含学习资料。
