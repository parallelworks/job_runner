def get_job(workflow_data, job_name):
    jobs = workflow_data.get("jobs", {})
    if job_name not in jobs:
        raise AssertionError(f"Expected job '{job_name}' to exist")
    return jobs[job_name]


def find_step(job, step_name):
    for step in job.get("steps", []):
        if step.get("name") == step_name:
            return step
    raise AssertionError(f"Expected step '{step_name}' to exist")


def get_step_run(job, step_name):
    step = find_step(job, step_name)
    run = step.get("run")
    if run is None:
        raise AssertionError(f"Expected step '{step_name}' to have a run block")
    return run


def get_step_cleanup(job, step_name):
    step = find_step(job, step_name)
    cleanup = step.get("cleanup")
    if cleanup is None:
        raise AssertionError(f"Expected step '{step_name}' to have a cleanup block")
    return cleanup
