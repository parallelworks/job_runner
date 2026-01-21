def test_execution_mode_input(v5_workflow_data):
    inputs = v5_workflow_data["on"]["execute"]["inputs"]
    execution_mode = inputs["execution_mode"]
    assert execution_mode["type"] == "select"
    assert execution_mode["default"] == "race"
    options = [opt["value"] for opt in execution_mode["options"]]
    assert "race" in options
    assert "parallel" in options


def test_core_input_defaults(v5_workflow_data):
    inputs = v5_workflow_data["on"]["execute"]["inputs"]
    assert inputs["rundir"]["default"] == "${PWD}"
    assert inputs["poll_interval"]["default"] == 10
    assert inputs["use_existing_script"]["default"] is False


def test_script_inputs_visibility(v5_workflow_data):
    inputs = v5_workflow_data["on"]["execute"]["inputs"]
    script = inputs["script"]
    script_path = inputs["script_path"]
    assert "use_existing_script == true" in script["hidden"]
    assert "use_existing_script == false" in script_path["hidden"]


def test_all_site_groups_exist(v5_workflow_data):
    inputs = v5_workflow_data["on"]["execute"]["inputs"]
    for i in range(5):
        site_key = f"sites_{i}"
        assert site_key in inputs, f"Missing {site_key}"
        assert inputs[site_key]["type"] == "group"


def test_site_0_enabled_by_default(v5_workflow_data):
    inputs = v5_workflow_data["on"]["execute"]["inputs"]
    site_0 = inputs["sites_0"]["items"]
    assert site_0["enabled"]["default"] is True


def test_sites_1_through_4_disabled_by_default(v5_workflow_data):
    inputs = v5_workflow_data["on"]["execute"]["inputs"]
    for i in range(1, 5):
        site = inputs[f"sites_{i}"]["items"]
        assert site["enabled"]["default"] is False, f"sites_{i} should be disabled"


def test_site_configuration_fields(v5_workflow_data):
    inputs = v5_workflow_data["on"]["execute"]["inputs"]
    for i in range(5):
        site = inputs[f"sites_{i}"]["items"]
        assert "enabled" in site
        assert "name" in site
        assert "resource" in site
        assert "priority" in site
        assert "scheduler" in site
        assert "slurm" in site
        assert "pbs" in site


def test_site_priorities_increase(v5_workflow_data):
    inputs = v5_workflow_data["on"]["execute"]["inputs"]
    for i in range(5):
        site = inputs[f"sites_{i}"]["items"]
        assert site["priority"]["default"] == i + 1


def test_site_names_default(v5_workflow_data):
    inputs = v5_workflow_data["on"]["execute"]["inputs"]
    for i in range(5):
        site = inputs[f"sites_{i}"]["items"]
        assert site["name"]["default"] == f"Site-{i}"


def test_site_scheduler_defaults_to_false(v5_workflow_data):
    inputs = v5_workflow_data["on"]["execute"]["inputs"]
    for i in range(5):
        site = inputs[f"sites_{i}"]["items"]
        assert site["scheduler"]["default"] is False


def test_site_slurm_config_hidden_conditions(v5_workflow_data):
    inputs = v5_workflow_data["on"]["execute"]["inputs"]
    for i in range(5):
        site = inputs[f"sites_{i}"]["items"]
        slurm = site["slurm"]
        assert f"sites_{i}.resource.schedulerType != 'slurm'" in slurm["hidden"]
        assert f"sites_{i}.scheduler == false" in slurm["hidden"]


def test_site_pbs_config_hidden_conditions(v5_workflow_data):
    inputs = v5_workflow_data["on"]["execute"]["inputs"]
    for i in range(5):
        site = inputs[f"sites_{i}"]["items"]
        pbs = site["pbs"]
        assert f"sites_{i}.resource.schedulerType != 'pbs'" in pbs["hidden"]
        assert f"sites_{i}.scheduler == false" in pbs["hidden"]


def test_slurm_has_required_fields(v5_workflow_data):
    inputs = v5_workflow_data["on"]["execute"]["inputs"]
    for i in range(5):
        slurm = inputs[f"sites_{i}"]["items"]["slurm"]["items"]
        assert "account" in slurm
        assert "partition" in slurm
        assert "time" in slurm
        assert "nodes" in slurm
        assert slurm["time"]["default"] == "04:00:00"
        assert slurm["nodes"]["default"] == 1


def test_pbs_has_required_fields(v5_workflow_data):
    inputs = v5_workflow_data["on"]["execute"]["inputs"]
    for i in range(5):
        pbs = inputs[f"sites_{i}"]["items"]["pbs"]["items"]
        assert "account" in pbs
        assert "queue" in pbs
        assert "walltime" in pbs
        assert pbs["walltime"]["default"] == "04:00:00"
