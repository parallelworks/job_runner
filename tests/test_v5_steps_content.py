from tests.helpers import get_job, get_step_run, get_step_cleanup


def test_initialize_creates_coordination_directory(v5_workflow_data):
    job = get_job(v5_workflow_data, "initialize")
    run = get_step_run(job, "Setup Coordination Directory")
    assert "COORD_DIR=" in run
    assert "lb_${PW_JOB_ID}" in run
    assert "mkdir -p" in run


def test_initialize_validates_enabled_sites(v5_workflow_data):
    job = get_job(v5_workflow_data, "initialize")
    run = get_step_run(job, "Setup Coordination Directory")
    assert "enabled_count" in run
    assert "No sites enabled" in run


def test_initialize_creates_site_directories(v5_workflow_data):
    job = get_job(v5_workflow_data, "initialize")
    run = get_step_run(job, "Setup Coordination Directory")
    for i in range(5):
        assert f"site_{i}" in run


def test_initialize_writes_event_log(v5_workflow_data):
    job = get_job(v5_workflow_data, "initialize")
    run = get_step_run(job, "Setup Coordination Directory")
    assert "events.jsonl" in run


def test_site_jobs_check_for_winner(v5_workflow_data):
    for i in range(5):
        job = get_job(v5_workflow_data, f"site_{i}")
        run = get_step_run(job, f"Submit Job to Site {i}")
        assert "../WINNER" in run


def test_site_jobs_create_script(v5_workflow_data):
    for i in range(5):
        job = get_job(v5_workflow_data, f"site_{i}")
        run = get_step_run(job, f"Submit Job to Site {i}")
        assert "use_existing_script" in run
        assert "run-script.sh" in run
        assert "run.sh" in run


def test_site_jobs_inject_markers(v5_workflow_data):
    for i in range(5):
        job = get_job(v5_workflow_data, f"site_{i}")
        run = get_step_run(job, f"Submit Job to Site {i}")
        assert "job.started" in run
        assert "HOSTNAME" in run


def test_site_jobs_support_slurm(v5_workflow_data):
    for i in range(5):
        job = get_job(v5_workflow_data, f"site_{i}")
        run = get_step_run(job, f"Submit Job to Site {i}")
        assert "sbatch" in run
        assert "#SBATCH" in run
        assert f"sites_{i}.slurm" in run


def test_site_jobs_support_pbs(v5_workflow_data):
    for i in range(5):
        job = get_job(v5_workflow_data, f"site_{i}")
        run = get_step_run(job, f"Submit Job to Site {i}")
        assert "qsub" in run
        assert "#PBS" in run
        assert f"sites_{i}.pbs" in run


def test_site_jobs_support_ssh_direct(v5_workflow_data):
    for i in range(5):
        job = get_job(v5_workflow_data, f"site_{i}")
        run = get_step_run(job, f"Submit Job to Site {i}")
        assert "./run.sh > run.out 2>&1" in run


def test_site_jobs_handle_race_mode(v5_workflow_data):
    for i in range(5):
        job = get_job(v5_workflow_data, f"site_{i}")
        run = get_step_run(job, f"Submit Job to Site {i}")
        assert "execution_mode" in run
        assert "race" in run
        assert "WINNER" in run


def test_site_jobs_track_status(v5_workflow_data):
    for i in range(5):
        job = get_job(v5_workflow_data, f"site_{i}")
        run = get_step_run(job, f"Submit Job to Site {i}")
        assert "status" in run
        assert "SUBMITTING" in run
        assert "RUNNING" in run
        assert "COMPLETED" in run


def test_site_jobs_have_cleanup(v5_workflow_data):
    for i in range(5):
        job = get_job(v5_workflow_data, f"site_{i}")
        cleanup = get_step_cleanup(job, f"Submit Job to Site {i}")
        assert "Cleanup triggered" in cleanup
        assert "job.ended" in cleanup


def test_site_cleanup_cancels_scheduler_jobs(v5_workflow_data):
    for i in range(5):
        job = get_job(v5_workflow_data, f"site_{i}")
        cleanup = get_step_cleanup(job, f"Submit Job to Site {i}")
        assert "scancel" in cleanup
        assert "qdel" in cleanup


def test_site_jobs_use_poll_interval(v5_workflow_data):
    for i in range(5):
        job = get_job(v5_workflow_data, f"site_{i}")
        run = get_step_run(job, f"Submit Job to Site {i}")
        assert "sleep ${{ inputs.poll_interval }}" in run


def test_log_job_streams_output(v5_workflow_data):
    job = get_job(v5_workflow_data, "log")
    run = get_step_run(job, "Stream Aggregated Output")
    assert "run.out" in run
    assert "site_*" in run


def test_log_job_uses_poll_interval(v5_workflow_data):
    job = get_job(v5_workflow_data, "log")
    run = get_step_run(job, "Stream Aggregated Output")
    assert "STOP_STREAMING" in run


def test_log_job_has_cleanup(v5_workflow_data):
    job = get_job(v5_workflow_data, "log")
    cleanup = get_step_cleanup(job, "Stream Aggregated Output")
    assert "STOP_STREAMING" in cleanup


def test_cleanup_generates_summary(v5_workflow_data):
    job = get_job(v5_workflow_data, "cleanup")
    run = get_step_run(job, "Generate Summary Report")
    assert "summary.json" in run
    assert "execution_id" in run
    assert "mode" in run


def test_cleanup_reports_statistics(v5_workflow_data):
    job = get_job(v5_workflow_data, "cleanup")
    run = get_step_run(job, "Generate Summary Report")
    assert "completed" in run
    assert "failed" in run
    assert "cancelled" in run


def test_cleanup_handles_race_mode_winner(v5_workflow_data):
    job = get_job(v5_workflow_data, "cleanup")
    run = get_step_run(job, "Generate Summary Report")
    assert "WINNER" in run
    assert "winner" in run


def test_cleanup_has_cleanup_handler(v5_workflow_data):
    job = get_job(v5_workflow_data, "cleanup")
    cleanup = get_step_cleanup(job, "Generate Summary Report")
    assert "STOP_STREAMING" in cleanup
