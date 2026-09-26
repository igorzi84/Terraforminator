import json

from terraforminator.domain.models import Finding, PolicyConfig, ResourceChange


def evaluate_policies(
    changes: list[ResourceChange], policy_config: PolicyConfig | None = None
) -> list[Finding]:
    if policy_config is None:
        policy_config = PolicyConfig()

    unknown_policy_ids = policy_config.enabled_policy_ids - POLICY_REGISTRY.keys()

    if unknown_policy_ids:
        unknown_ids = ", ".join(sorted(unknown_policy_ids))
        raise ValueError(f"Unknown policy IDs: {unknown_ids}")

    findings = []
    for change in changes:
        for policy_id, policy_check in POLICY_REGISTRY.items():
            if policy_id in policy_config.enabled_policy_ids:
                findings.extend(policy_check(change))
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
        if "0.0.0.0/0" in rule.get("cidr_blocks", []):
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
        if statement["Effect"] == "Allow" and (
            statement["Action"] == "*" or statement["Resource"] == "*"
        ):
            finding = Finding(
                id="iam-wildcard-permission",
                severity="high",
                resource_address=change.address,
                evidence="policy.statement contains wildcard permissions",
                remediation="Replace wildcard actions and resources with the minimum required permissions.",
            )
            findings.append(finding)
    return findings


def check_destructive_stateful_changes(change: ResourceChange) -> list[Finding]:
    if change.resource_type != "docker_volume":
        return []

    if "delete" not in change.actions:
        return []

    return [
        Finding(
            id="destructive-stateful-change",
            severity="high",
            resource_address=change.address,
            evidence=f"actions contains delete for {change.resource_type}",
            remediation="Backup data and explicitly approve.",
        )
    ]


def check_missing_storage_encryption(change: ResourceChange) -> list[Finding]:
    if change.resource_type != "aws_ebs_volume":
        return []

    if not {"create", "update"}.intersection(change.actions):
        return []

    if change.after is None:
        return []

    encrypted = change.after.get("encrypted")

    if encrypted is False:
        return [
            Finding(
                id="missing-storage-encryption",
                severity="high",
                resource_address=change.address,
                evidence="after.encrypted is false",
                remediation="Enable encryption for the storage resource.",
            )
        ]

    if (change.after_unknown or {}).get("encrypted") is True:
        return [
            Finding(
                id="storage-encryption-unknown",
                severity="medium",
                resource_address=change.address,
                evidence="after.encrypted is unknown",
                remediation="Resolve the encryption value before approving the change.",
            )
        ]

    return []


POLICY_REGISTRY = {
    "public-inbound-access": check_public_inbound_access,
    "iam-wildcard-permission": check_iam_wildcard_permissions,
    "destructive-stateful-change": check_destructive_stateful_changes,
    "storage-encryption": check_missing_storage_encryption,
}
