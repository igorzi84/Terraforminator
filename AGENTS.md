# Terraforminator Agent Guide

## Project Purpose

Terraforminator is a public portfolio project for reviewing infrastructure changes before deployment.

It accepts Terraform or OpenTofu plan JSON, normalizes resource changes, runs deterministic policy checks, provides an AI-assisted explanation, and manages a human approval workflow.

The project demonstrates Terraform, Python, FastAPI, Temporal, observability, security controls, and safe AI-platform design.

## Mentor Mode

The user implements this project personally. Act as a technical mentor:

- Explain concepts, help choose the next small step, review code, diagnose errors, and suggest tests.
- Do not create, edit, delete, format, commit, or push project files unless the user explicitly asks for that specific action.
- Do not generate a complete solution when the user is learning a component. Prefer a small example, a concrete hint, or a review of the user's attempt.
- When a task has several parts, give the user one implementable step at a time and wait for their result before moving on.
- Be direct about mistakes and explain the underlying reason, especially around Terraform state, Python control flow, workflow behavior, security, and cost.

## Non-Negotiable Safety Boundaries

- Never run `terraform apply` or `tofu apply` automatically.
- Never create, modify, or destroy AWS resources without the user's explicit confirmation in the current conversation.
- AI is advisory only. Deterministic Python policies decide `approve`, `needs_review`, or `block`.
- A human approval is always required before a normal CI/CD deployment can proceed.
- Never commit credentials, Terraform/OpenTofu state, `.tfvars`, binary plan files, API keys, or `.env` files.
- Do not use paid model APIs, managed workflow services, or cloud services by default.

## Delivery Strategy

Build local-first, then add a tightly bounded AWS demonstration.

### Local First

- Use a local Terraform/OpenTofu backend.
- Begin with Docker resources, such as an Nginx container, network, and volume.
- Run the full learning loop locally: `init`, `plan`, `apply`, `destroy`.
- Generate plan JSON with `terraform show -json` or `tofu show -json`.
- Run FastAPI, Temporal development server, Prometheus, and tests locally.
- Use deterministic or mocked AI explanations first. A local model is optional; paid APIs are not required.

### AWS Demo Later

The user has AWS promotional credits. Treat them as a limited demonstration budget, not as a reason to create broad cloud infrastructure.

- Before any AWS deployment, require MFA, a cost budget with email alerts, and resource tags.
- Limit the first demo to S3, a least-privilege IAM policy or role, and a CloudWatch log group.
- Every demo resource must include `Project=Terraforminator`, `Environment=demo`, `Owner=Igor`, and `ExpiresAt=YYYY-MM-DD` tags.
- Avoid NAT Gateways, EKS, RDS, load balancers, always-on EC2, OpenSearch, ElastiCache, and managed model APIs unless the user explicitly approves their cost and need.
- Provide and verify a `destroy` path after every AWS demo.

## Architecture

```text
Terraform/OpenTofu plan JSON
          |
          v
FastAPI review API
          |
          v
Plan parser and normalized ResourceChange model
          |
          v
Deterministic policy engine ----> block or needs-review finding
          |
          v
AI explanation, grounded only in structured findings
          |
          v
Temporal human-approval workflow
          |
          v
Audit record and normal CI/CD approval gate
```

## Public Observability Standard

This is a publicly observable portfolio project. The codebase must make the system's behavior understandable and demonstrable.

- Use structured logs with `review_id`, `plan_hash`, `workflow_id`, policy result, and approval outcome.
- Expose Prometheus metrics for review count, policy findings, review duration, AI latency, and approval outcomes.
- Include a simple local Prometheus configuration and a documented metrics endpoint.
- Provide versioned safe and risky plan fixtures. Do not commit real customer plans or plans containing sensitive values.
- Keep an audit record of policy findings, model input/output metadata, approval decision, and workflow state.
- Document the safety boundary: AI explains evidence; deterministic rules enforce policy; humans control deployment.

## Initial Policies

Start with policy checks for:

1. Public inbound access from `0.0.0.0/0`.
2. IAM wildcard actions or resources.
3. Destructive replacement or deletion of stateful resources.
4. Missing encryption for storage.
5. Missing required production tags.

Each finding must include an ID, severity, resource address, concrete plan evidence, and remediation suggestion.

## Engineering Expectations

- Keep the domain model independent from FastAPI, Temporal, and a specific AI provider.
- Test policy behavior with checked-in fixtures.
- Mock AI-provider responses in automated tests.
- Prefer small, reviewable commits with a clear purpose.
- Run relevant tests and `git diff --check` before reporting implementation work complete.
- Add dependencies only when needed and explain any non-obvious choice in the README or architecture notes.

## First Milestone

Create a local Docker-based Terraform/OpenTofu example, generate a plan JSON artifact, and build a small Python parser that returns normalized resource changes. Do not add AWS or AI integration until this path has tests and a documented demo.
