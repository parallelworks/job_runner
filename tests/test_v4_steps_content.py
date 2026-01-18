from tests.helpers import get_job, get_step_run, get_step_cleanup


def test_stream_output_script_contains_markers(workflow_data):
    job = get_job(workflow_data, "stream_output")
    run = get_step_run(job, "Stream Output")
    assert 'OUTPUT_FILE="run.${PW_JOB_ID}.out"' in run
    assert "timeout=60" in run
    assert "tail -f" in run
    assert "CANCEL_STREAMING" in run
    assert "job.ended" in run
    assert "ERROR: Job ended unexpectedly" in run


def test_create_script_template_validation(workflow_data):
    job = get_job(workflow_data, "create_script_template")
    run = get_step_run(job, "Validate Scheduler Selection")
    assert "inputs.scheduler" in run
    assert "inputs.slurm.is_disabled" in run
    assert "inputs.pbs.is_disabled" in run
    assert "Scheduler enabled but no scheduler type is active" in run


def test_create_script_template_injection(workflow_data):
    job = get_job(workflow_data, "create_script_template")
    run = get_step_run(job, "Create Script Template")
    assert "use_existing_script" in run
    assert "inputs.script_path" in run
    assert "run-template.sh" in run
    assert "inject_markers" in run
    assert "job.started" in run
    assert "HOSTNAME" in run


def test_ssh_job_execution_contract(workflow_data):
    job = get_job(workflow_data, "ssh_job")
    run = get_step_run(job, "Execute Script")
    assert "./run.sh > run.${PW_JOB_ID}.out 2>&1" in run
    assert "exit_code=$?" in run
    assert "touch job.ended" in run
    assert "exit_code=${exit_code}" in run

    cleanup = get_step_cleanup(job, "Execute Script")
    assert "SSH job cleanup triggered" in cleanup
    assert "job.ended" in cleanup


def test_pbs_submission_and_cleanup(workflow_data):
    job = get_job(workflow_data, "pbs_job")
    run = get_step_run(job, "Submit PBS Job")
    assert "qsub run.sh" in run
    assert "grep -oE '^[0-9]+'" in run
    assert "jobid" in run

    cleanup = get_step_cleanup(job, "Submit PBS Job")
    assert "qdel" in cleanup
    assert "job.ended" in cleanup


def test_slurm_submission_and_cleanup(workflow_data):
    job = get_job(workflow_data, "slurm_job")
    run = get_step_run(job, "Submit SLURM Job")
    assert "sbatch run.sh" in run
    assert "grep -oE '[0-9]+$'" in run
    assert "jobid" in run

    cleanup = get_step_cleanup(job, "Submit SLURM Job")
    assert "scancel" in cleanup
    assert "job.ended" in cleanup


def test_monitors_use_poll_interval(workflow_data):
    for job_name, step_name in (
        ("pbs_job", "Monitor PBS Job"),
        ("slurm_job", "Monitor SLURM Job"),
    ):
        job = get_job(workflow_data, job_name)
        run = get_step_run(job, step_name)
        assert "sleep ${{ inputs.poll_interval }}" in run


def test_cleanup_job_contract(workflow_data):
    job = get_job(workflow_data, "cleanup")
    assert job.get("if") == "${{ always }}"

    run = get_step_run(job, "Cleanup")
    assert "Workflow completed" in run
    assert "touch COMPLETED" in run

    cleanup = get_step_cleanup(job, "Cleanup")
    assert "CANCEL_STREAMING" in cleanup
    assert "Job was cancelled" in cleanup
    assert "cancel.sh" in cleanup
