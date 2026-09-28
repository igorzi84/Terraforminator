from pathlib import Path

import pytest

from terraforminator.config import load_policy_config
from terraforminator.domain.models import PolicyConfig
from terraforminator.domain.policies import evaluate_policies

TEST_CONFIG_DIR = Path(__file__).parent / "fixtures" / "config"
REPO_CONFIG_DIR = Path(__file__).parent.parent / "config"


def test_load_public_inbound_policy_only():
    config_path = TEST_CONFIG_DIR / "public-inbound-only.toml"
    policy_config = load_policy_config(config_path)
    assert isinstance(policy_config, PolicyConfig)
    assert policy_config.enabled_policy_ids == frozenset({"public-inbound-access"})


def test_load_multiple_policies():
    config_path = TEST_CONFIG_DIR / "multiple-policies.toml"
    policy_config = load_policy_config(config_path)
    assert isinstance(policy_config, PolicyConfig)
    assert policy_config.enabled_policy_ids == frozenset(
        {"public-inbound-access", "iam-wildcard-permission"}
    )
    assert policy_config.required_tags == frozenset({"Project", "Environment", "Owner"})


def test_empty_config_error():
    config_path = TEST_CONFIG_DIR / "empty-config.toml"
    with pytest.raises(ValueError, match="enabled_policy_ids is required"):
        load_policy_config(config_path)


def test_reject_str_in_policy_config():
    config_path = TEST_CONFIG_DIR / "string-in-config.toml"
    with pytest.raises(TypeError, match="enabled_policy_ids must be a list of strings"):
        load_policy_config(config_path)


def test_reject_non_string_policy_id():
    config_path = TEST_CONFIG_DIR / "int-in-config.toml"
    with pytest.raises(TypeError, match="enabled_policy_ids must be a list of strings"):
        load_policy_config(config_path)


def test_real_config_load():
    config_path = REPO_CONFIG_DIR / "policies.toml"
    policy_config = load_policy_config(config_path)
    assert isinstance(policy_config, PolicyConfig)
    assert evaluate_policies([], policy_config) == []


def test_required_tags():
    config_path = TEST_CONFIG_DIR / "public-inbound-only.toml"
    policy_config = load_policy_config(config_path)
    assert isinstance(policy_config, PolicyConfig)
    assert policy_config.required_tags == frozenset(
        {"Project", "Environment", "Owner", "Test-Tag"}
    )


def test_reject_str_in_tag_config():
    config_path = TEST_CONFIG_DIR / "string-required-tags.toml"
    with pytest.raises(TypeError, match="required_tags must be a list of strings"):
        load_policy_config(config_path)