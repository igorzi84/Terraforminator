# Terraforminator

Terraforminator reviews Terraform or OpenTofu plan JSON before deployment. It
normalizes resource changes, runs deterministic policy checks, and returns a
review decision with concrete findings.

It is a local-first portfolio project. The current implementation provides the
plan-review domain layer, deterministic explanations, and a FastAPI API for
storing reviews in SQLite, recording human decisions, and retrieving audit
records. Structured JSON logs capture completed reviews and saved human
decisions. A Prometheus endpoint exposes review and human-decision counters.
Temporal workflows and a local Prometheus scraping configuration are planned.

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

### Database configuration

The local API defaults to `terraforminator.db` in the repository root. Set
`TERRAFORMINATOR_DB_PATH` to use a different database file:

```bash
TERRAFORMINATOR_DB_PATH=/tmp/terraforminator.db uv run fastapi dev src/terraforminator/main.py
```

The parent directory must already exist and be writable. SQLite creates the
database file if it does not exist. Relative paths resolve from the directory
where you start the server. Empty or whitespace-only values are rejected.
Database files matching `*.db` are ignored by Git.

### Structured logging

The API writes JSON logs to stderr in the terminal. Each event includes a UTC
timestamp, log level, logger name, and message.

- `Review created` is emitted after the review is stored and its explanation
  succeeds. It includes `review_id`, `plan_hash`, and `policy_result`.
- `Human decision recorded` is emitted after an approval or rejection is saved
  and the updated review is retrieved. It includes the same review fields plus
  `approval_outcome` (`approved` or `rejected`).

Failed approval requests do not emit a successful human-decision event.

### Metrics

`GET /metrics` exposes metrics in Prometheus text format:

```bash
curl --fail-with-body -sS http://127.0.0.1:8000/metrics
```

| Counter | Label | Values |
| --- | --- | --- |
| `terraforminator_reviews_total` | `policy_result` | `approve`, `needs_review`, `block` |
| `terraforminator_approval_decisions_total` | `approval_outcome` | `approved`, `rejected` |

The review counter increments after storage and explanation succeed. The
human-decision counter increments after an approval or rejection is saved.
Invalid requests, failed explanations, and failed approval requests do not
increment these counters. Policy results and human decisions are counted
separately; human approval of a blocked review still does not allow deployment.

Each app instance owns its metrics registry. Counters are held in memory and
reset when the app process restarts; they do not count historical SQLite
records. A label combination appears after its first recorded event. Review
IDs and plan hashes stay in logs rather than metric labels.

## API

The local API stores reviews and approval records in SQLite. They survive
server restarts when the API uses the same database file. Recording a human
decision updates the review and inserts its audit record in one transaction;
if either write fails, both are rolled back.

The `create_app()` factory retains an in-memory default for isolated tests;
the local entrypoint explicitly supplies the configured SQLite store.
The current explanation provider is deterministic; no model API is required.

Run this example from the repository root with the API running. It uses Python
to wrap the checked-in local Docker fixture in the request body.

### Create a review

```bash
python3 -c 'import json; from pathlib import Path; print(json.dumps({"plan": json.loads(Path("tests/fixtures/plans/nginx-create.json").read_text())}))' | \
  curl --fail-with-body -sS http://127.0.0.1:8000/reviews \
    -H 'Content-Type: application/json' --data-binary @-
```

The response contains `review_id`, `decision`, `findings`, and `explanation`.
Copy the returned ID into a shell variable:

```bash
review_id='<returned review_id>'
```

### Retrieve the review

```bash
curl --fail-with-body -sS "http://127.0.0.1:8000/reviews/$review_id"
```

The response contains `review_id`, `plan_hash`, `decision`, `findings`,
`approval_status`, and `can_deploy`. A new review has `approval_status` set to
`"pending"` and `can_deploy` set to `false`. Retrieval does not regenerate or
return the explanation.

`can_deploy` is calculated from the current policy result and human decision:

| Policy decision | Human pending | Human approved | Human rejected |
| --- | --- | --- | --- |
| `approve` | `false` | `true` | `false` |
| `needs_review` | `false` | `true` | `false` |
| `block` | `false` | `false` | `false` |

Human approval is always required. A policy `block` keeps `can_deploy` false,
even after human approval. This field reports deployment eligibility; CI/CD
enforcement is still planned.

### Record a human decision

```bash
curl --fail-with-body -sS "http://127.0.0.1:8000/reviews/$review_id/approval" \
  -H 'Content-Type: application/json' \
  --data '{"status":"approved","reviewer":"Igor","reason":"Reviewed the local Docker changes."}'
```

Use `"rejected"` to reject the review. Reviewer and reason must be nonblank.
The response returns the updated review with a recalculated `can_deploy` value.
A human decision updates `approval_status` and preserves the deterministic
policy decision and findings, even when a human approves a policy `"block"`.
This endpoint records a decision; it does not deploy infrastructure or provide
a CI/CD gate yet.

### Retrieve the audit record

```bash
curl --fail-with-body -sS "http://127.0.0.1:8000/reviews/$review_id/approval"
```

The response contains `review_id`, `status`, `reviewer`, `reason`, and
`decided_at`. The `decided_at` timestamp is the UTC time when the human decision
was recorded, serialized as an ISO 8601 string. Retrieving the record preserves
the original timestamp.

Invalid plans or approval inputs return `422`. Unknown reviews return `404`;
retrieving an approval record before a human decision also returns `404` with
`approval_not_found`. A second human decision returns `409` with
`review_not_pending` and leaves the original decision intact.

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
loading, decision rules, the domain pipeline, store isolation, SQLite
persistence and transaction rollback, the review and human-decision API routes,
JSON log formatting with and without review context, isolated metrics registries,
counter updates, failure exclusions, and the Prometheus endpoint.

Before committing changes:

```bash
uv run pytest
git diff --check
```

## Planned work

- Optional model-backed advisory explanations grounded in policy findings.
- Temporal human approval workflow and a CI/CD approval gate.
- Review duration, explanation latency, and policy-finding metrics, plus a
  local Prometheus scraping configuration.
- A bounded AWS demonstration with MFA, budget alerts, required tags, and a
  verified destroy path.
