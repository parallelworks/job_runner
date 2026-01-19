from tests.helpers import get_job


def test_core_input_defaults(workflow_data):
    inputs = workflow_data["on"]["execute"]["inputs"]
    assert inputs["resource"]["type"] == "compute-clusters"
    assert inputs["shebang"]["default"] == "#!/bin/bash"
    assert inputs["rundir"]["default"] == "${PWD}"
    assert inputs["scheduler"]["default"] is False
    assert inputs["inject_markers"]["default"] is True
    assert inputs["poll_interval"]["default"] == 15


def test_script_inputs_visibility(workflow_data):
    inputs = workflow_data["on"]["execute"]["inputs"]
    script = inputs["script"]
    script_path = inputs["script_path"]
    assert "use_existing_script == true" in script["hidden"]
    assert "use_existing_script == false" in script_path["hidden"]


def test_slurm_group_defaults(workflow_data):
    slurm = workflow_data["on"]["execute"]["inputs"]["slurm"]
    assert "schedulerType != 'slurm'" in slurm["hidden"]
    assert "inputs.scheduler == false" in slurm["hidden"]

    slurm_items = slurm["items"]
    assert "schedulerType != 'slurm'" in slurm_items["is_disabled"]["default"]
    assert "inputs.scheduler == false" in slurm_items["is_disabled"]["default"]
    assert slurm_items["time"]["default"] == "04:00:00"
    assert slurm_items["nodes"]["default"] == 1
    assert slurm_items["cpus_per_task"]["default"] == 4


def test_pbs_group_defaults(workflow_data):
    pbs = workflow_data["on"]["execute"]["inputs"]["pbs"]
    assert "schedulerType != 'pbs'" in pbs["hidden"]
    assert "inputs.scheduler == false" in pbs["hidden"]

    pbs_items = pbs["items"]
    assert "schedulerType != 'pbs'" in pbs_items["is_disabled"]["default"]
    assert "inputs.scheduler == false" in pbs_items["is_disabled"]["default"]
    assert pbs_items["walltime"]["default"] == "04:00:00"


def test_job_output_wiring(workflow_data):
    pbs_job = get_job(workflow_data, "pbs_job")
    slurm_job = get_job(workflow_data, "slurm_job")
    assert (
        pbs_job["outputs"]["jobid"]
        == "${{ needs.pbs_job.steps.submit.outputs.jobid }}"
    )
    assert (
        slurm_job["outputs"]["jobid"]
        == "${{ needs.slurm_job.steps.submit.outputs.jobid }}"
    )
