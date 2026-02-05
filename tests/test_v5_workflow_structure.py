from tests.helpers import get_job


def test_top_level_sections(v5_workflow_data):
    assert "jobs" in v5_workflow_data
    assert "on" in v5_workflow_data
    assert "execute" in v5_workflow_data["on"]
    assert "inputs" in v5_workflow_data["on"]["execute"]


def test_required_jobs_exist(v5_workflow_data):
    expected_jobs = {
        "initialize",
        "site_0",
        "site_1",
        "site_2",
        "site_3",
        "site_4",
        "log",
        "cleanup",
    }
    assert expected_jobs == set(v5_workflow_data["jobs"].keys())


def test_site_jobs_depend_on_initialize(v5_workflow_data):
    for i in range(5):
        job_name = f"site_{i}"
        job = get_job(v5_workflow_data, job_name)
        assert "initialize" in job.get("needs", [])


def test_site_jobs_have_conditional_execution(v5_workflow_data):
    for i in range(5):
        job_name = f"site_{i}"
        job = get_job(v5_workflow_data, job_name)
        assert f"inputs.sites_{i}.enabled" in job.get("if", "")


def test_site_jobs_use_site_specific_resources(v5_workflow_data):
    for i in range(5):
        job_name = f"site_{i}"
        job = get_job(v5_workflow_data, job_name)
        assert f"inputs.sites_{i}.resource.ip" in job.get("ssh", {}).get(
            "remoteHost", ""
        )
        assert f"lb_${{PW_JOB_ID}}/site_{i}" in job.get("working-directory", "")


def test_log_job_depends_on_initialize(v5_workflow_data):
    job = get_job(v5_workflow_data, "log")
    assert "initialize" in job.get("needs", [])


def test_cleanup_job_always_runs(v5_workflow_data):
    job = get_job(v5_workflow_data, "cleanup")
    assert job.get("if") == "${{ always }}"


def test_cleanup_job_depends_on_all_sites_and_log(v5_workflow_data):
    job = get_job(v5_workflow_data, "cleanup")
    needs = set(job.get("needs", []))
    expected = {"site_0", "site_1", "site_2", "site_3", "site_4", "log"}
    assert expected == needs


def test_initialize_has_no_dependencies(v5_workflow_data):
    job = get_job(v5_workflow_data, "initialize")
    assert "needs" not in job or job.get("needs") is None
