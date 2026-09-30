# Terraforminator

Terraforminator reviews Terraform or OpenTofu plan JSON before deployment. It
normalizes resource changes, runs deterministic policy checks, and returns a
review decision with concrete findings.

It is a local-first portfolio project. The current implementation provides the
plan-review domain layer and a small FastAPI endpoint; AI explanations, human
approval workflows, audit storage, and observability are planned next.

## Safety boundary

- Terraforminator never runs `terraform apply` or `tofu apply`.
- Deterministic Python policies produce findings and decide `approve`,
  `needs_review`, or `block`.
- `approve` means no enabled deterministic policy found a violation. It is not
  permission to deploy automatically: a human approval remains required before
  a normal CI/CD deployment.
- Future AI functionality will explain structured findings only. It will not
  make enforcement or deployment decisions.

## Current flow

```text
Terraform/OpenTofu plan JSON
            |
            v
       parse_plan()
            |
            v
   ResourceChange objects
            |
            v
   evaluate_review()
      |             |
      v             v
 policy findings   decision
            |
            v
      FastAPI response
```

## Policies

The enabled policies are configured in
[`config/policies.toml`](config/policies.toml).

| Policy ID | What it checks | Severity |
| --- | --- | --- |
| `public-inbound-access` | `0.0.0.0/0` ingress on `aws_security_group` create or update | high |
| `iam-wildcard-permission` | Wildcard action or resource in an allow statement on `aws_iam_policy` | high |
| `destructive-stateful-change` | Deletion of a `docker_volume` | high |
| `storage-encryption` | Missing or unknown encryption on `aws_ebs_volume` create or update | high or medium |
| `missing-required-tags` | Missing configured tags on `aws_ebs_volume` create or update | medium |

`enabled_policy_ids` selects trusted policy implementations. `required_tags`
controls the tag policy without changing Python code. Unknown policy IDs are
rejected during evaluation.

## Run locally

Requirements: Python 3.14+, [uv](https://docs.astral.sh/uv/), Docker, and
Terraform or OpenTofu for the optional local demo.

Install dependencies and run tests:

```bash
uv sync --dev
uv run pytest
```

Start the API:

```bash
uv run fastapi dev src/terraforminator/main.py
```

The API is available at `http://127.0.0.1:8000`. FastAPI also exposes
interactive documentation at `/docs`.

## API

`POST /reviews` accepts a plan document and returns the deterministic review
result.

Request shape:

```json
{
  "plan": {
    "resource_changes": []
  }
}
```

Example response:

```json
{
  "decision": "block",
  "findings": [
    {
      "id": "public-inbound-access",
      "severity": "high",
      "resource_address": "aws_security_group.web",
      "evidence": "ingress.cidr_blocks contains 0.0.0.0/0",
      "remediation": "Restrict ingress to approved networks."
    }
  ]
}
```

## Local Terraform demo

[`terraform/local-demo`](terraform/local-demo) defines a Docker Nginx
container. It is intended only for local experimentation with a Docker daemon.

```bash
cd terraform/local-demo
terraform init
terraform plan -out=tfplan
terraform show -json tfplan > ../../tests/fixtures/plans/nginx-create.json
```

Do not commit Terraform/OpenTofu state, `.tfvars` files, binary plan files, or
credentials. If you apply the demo locally, destroy it when finished:

```bash
terraform destroy
```

## Tests and fixtures

Checked-in fixtures under `tests/fixtures/plans/` are fictional and safe to
commit. They cover both a local Docker plan and a risky public AWS security
group update. The tests cover parsing, individual policy checks, configuration
loading, decision rules, the domain pipeline, and the FastAPI endpoint.

Before committing changes:

```bash
uv run pytest
git diff --check
```

## Planned work

- Validation and clearer API errors for malformed plan documents.
- Advisory AI explanations grounded in policy findings.
- Human approval workflow, audit records, structured logs, and Prometheus
  metrics.
- A bounded AWS demonstration with MFA, budget alerts, required tags, and a
  verified destroy path.
