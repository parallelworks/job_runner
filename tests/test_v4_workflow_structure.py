from tests.helpers import get_job


def test_top_level_sections(workflow_data):
    assert "jobs" in workflow_data
    assert "on" in workflow_data
    assert "execute" in workflow_data["on"]
    assert "inputs" in workflow_data["on"]["execute"]


def test_required_jobs_exist(workflow_data):
    expected_jobs = {
        "log",
        "create_script_template",
        "ssh_job",
        "pbs_job",
        "slurm_job",
        "cleanup",
    }
    assert expected_jobs.issubset(set(workflow_data["jobs"].keys()))


def test_jobs_share_remote_host_and_rundir(workflow_data):
    for job_name in (
        "log",
        "create_script_template",
        "ssh_job",
        "pbs_job",
        "slurm_job",
        "cleanup",
    ):
        job = get_job(workflow_data, job_name)
        assert job.get("working-directory") == "${{ inputs.rundir }}"
        assert job.get("ssh", {}).get("remoteHost") == "${{ inputs.resource.ip }}"


def test_job_dependencies(workflow_data):
    create_job = get_job(workflow_data, "create_script_template")
    assert "needs" not in create_job

    for job_name in ("ssh_job", "pbs_job", "slurm_job"):
        job = get_job(workflow_data, job_name)
        assert "create_script_template" in job.get("needs", [])

    cleanup = get_job(workflow_data, "cleanup")
    assert set(cleanup.get("needs", [])) == {"ssh_job", "pbs_job", "slurm_job"}
