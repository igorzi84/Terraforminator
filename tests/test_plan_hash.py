from terraforminator.domain.plan_hash import hash_plan


def test_identical_content():
    first_plan = {"key1": "value1", "key2": "value2"}
    second_plan = {"key2": "value2", "key1": "value1"}

    first_hash = hash_plan(first_plan)
    second_hash = hash_plan(second_plan)

    assert first_hash == second_hash


def test_different_content():
    first_plan = {"key1": "value1", "key2": "value2"}
    second_plan = {"key1": "value1", "key2": "value3"}

    first_hash = hash_plan(first_plan)
    second_hash = hash_plan(second_plan)

    assert first_hash != second_hash
