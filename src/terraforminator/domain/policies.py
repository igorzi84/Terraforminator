import json

from terraforminator.domain.models import Finding, ResourceChange


def evaluate_policies(changes: list[ResourceChange]) -> list[Finding]:
    findings = []
    for change in changes:
        findings.extend(check_public_inbound_access(change))
        findings.extend(check_iam_wildcard_permissions(change))
    return findings


def check_public_inbound_access(change: ResourceChange) -> list[Finding]:
    findings = []
    if change.resource_type != "aws_security_group":
        return []

    if not {"create", "update"}.intersection(change.actions):
        return []

    if change.after is None:
        return []
 
    for rule in change.after.get("ingress", []):
        if "0.0.0.0/0" in rule.get("cidr_blocks",[]):
            finding = Finding(
                id="public-inbound-access",
                severity="high",
                resource_address=change.address,
                evidence="ingress.cidr_blocks contains 0.0.0.0/0",
                remediation="Restrict ingress to approved networks.",
            )
            findings.append(finding)
    return findings

def check_iam_wildcard_permissions(change: ResourceChange) -> list[Finding]:
    findings = []
    if change.resource_type != "aws_iam_policy":
        return []

    if not {"create", "update"}.intersection(change.actions):
        return []

    if change.after is None:
        return []
 
    policy = json.loads(change.after["policy"])
    for statement in policy["Statement"]:
        if statement["Effect"] == "Allow" and (statement["Action"] == "*" or statement["Resource"] == "*"):
            finding = Finding(
                id="iam-wildcard-permission",
                severity="high",
                resource_address=change.address,
                evidence="policy.statement contains wildcard permissions",
                remediation="Replace wildcard actions and resources with the minimum required permissions.",
            )
            findings.append(finding)
    return findings
