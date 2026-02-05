from tests.helpers import get_job, get_step_run, get_step_cleanup


def test_log_job_script_contains_markers(workflow_data):
    job = get_job(workflow_data, "log")
    run = get_step_run(job, "Job Output")
    assert 'OUTPUT_FILE="run.${PW_JOB_ID}.out"' in run
    assert "timeout=60" in run
    assert "tail -f" in run
    assert "CANCEL_STREAMING" in run
    assert "job.ended" in run


def test_create_script_template_validation(workflow_data):
    """Validation is now consolidated into Create Script Template step"""
    job = get_job(workflow_data, "create_script_template")
    run = get_step_run(job, "Create Script Template")
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
    """SSH job is now consolidated into single Execute SSH Job step"""
    job = get_job(workflow_data, "ssh_job")
    run = get_step_run(job, "Execute SSH Job")
    assert "./run.sh > run.${PW_JOB_ID}.out 2>&1" in run
    assert "exit_code=$?" in run
    assert "touch job.ended" in run
    assert "exit_code=${exit_code}" in run

    cleanup = get_step_cleanup(job, "Execute SSH Job")
    assert "SSH job cleanup triggered" in cleanup
    assert "job.ended" in cleanup


def test_pbs_submission_and_cleanup(workflow_data):
    """PBS submit and monitor are now consolidated into single step"""
    job = get_job(workflow_data, "pbs_job")
    run = get_step_run(job, "Submit and Monitor PBS Job")
    assert "qsub run.sh" in run
    assert "grep -oE '^[0-9]+'" in run
    assert "jobid" in run
    # Monitor functionality is now in the same step
    assert "sleep ${{ inputs.poll_interval }}" in run
    assert "job_status" in run

    cleanup = get_step_cleanup(job, "Submit and Monitor PBS Job")
    assert "qdel" in cleanup
    assert "job.ended" in cleanup


def test_slurm_submission_and_cleanup(workflow_data):
    """SLURM submit and monitor are now consolidated into single step"""
    job = get_job(workflow_data, "slurm_job")
    run = get_step_run(job, "Submit and Monitor SLURM Job")
    assert "sbatch run.sh" in run
    assert "grep -oE '[0-9]+$'" in run
    assert "jobid" in run
    # Monitor functionality is now in the same step
    assert "sleep ${{ inputs.poll_interval }}" in run
    assert "job_status" in run

    cleanup = get_step_cleanup(job, "Submit and Monitor SLURM Job")
    assert "scancel" in cleanup
    assert "job.ended" in cleanup


def test_monitors_use_poll_interval(workflow_data):
    """Monitors are now consolidated into submit steps"""
    for job_name, step_name in (
        ("pbs_job", "Submit and Monitor PBS Job"),
        ("slurm_job", "Submit and Monitor SLURM Job"),
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
