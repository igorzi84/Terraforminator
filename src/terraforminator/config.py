import tomllib
from pathlib import Path

from terraforminator.domain.models import PolicyConfig


def load_policy_config(config_path: Path) -> PolicyConfig:
    with open(config_path, "rb") as f:
        config = tomllib.load(f)
        if "enabled_policy_ids" not in config:
            raise ValueError("enabled_policy_ids is required")

        policy_ids = config["enabled_policy_ids"]

        if not isinstance(policy_ids, list):
            raise TypeError("enabled_policy_ids must be a list of strings")

        if not all(isinstance(policy_id, str) for policy_id in policy_ids):
            raise TypeError("enabled_policy_ids must be a list of strings")

        ids = frozenset(policy_ids)

        tags = PolicyConfig().required_tags

        if "required_tags" in config:
            required_tags = config["required_tags"]

            if not isinstance(required_tags, list):
                raise TypeError("required_tags must be a list of strings")

            if not all(isinstance(tag, str) for tag in required_tags):
                raise TypeError("required_tags must be a list of strings")

            tags = frozenset(required_tags)

        return PolicyConfig(enabled_policy_ids=ids, required_tags=tags)
