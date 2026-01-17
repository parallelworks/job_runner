# Job Runner

A reusable marketplace workflow for executing scripts on HPC and cloud compute resources via SSH, PBS, or SLURM. Job Runner abstracts away the complexity of job submission, monitoring, and cleanup, allowing you to focus on your actual workload.

> **Note:** The marketplace name is `job_runner` (with underscore) for compatibility with ACTIVATE market naming requirements.

## Overview

This workflow provides a flexible way to run user-defined scripts on cloud compute and on-prem resources using SSH, PBS, or SLURM. The user supplies a script and (when applicable) configures scheduler directives directly through the workflow UI. Based on these selections, the workflow automatically generates a fully populated job script—including the shebang, run directory, scheduler options, and user script—and executes or submits it on the target system.

## Versions

| Version | File | Description |
|---------|------|-------------|
| **v3.5** | `v3.5.yaml` | Original stable version with basic SSH/PBS/SLURM support |
| **v4.0** | `v4.0.yaml` | Enhanced version with structured inputs, cleanup handlers, and job markers |

### v4.0 Improvements over v3.5

- **Bug Fixes**: Fixed scheduler_directives expansion, typo in error messages
- **Structured Inputs**: SLURM (account, qos, nodes, gres, mem, constraint, array) and PBS (account, queue, walltime, select)
- **Cleanup Handlers**: Proper job cancellation on all execution paths
- **Job Markers**: Optional `inject_markers` for session management coordination
- **Failure Detection**: Reports final job state (COMPLETED, FAILED, TIMEOUT, etc.)
- **Configurable Polling**: `poll_interval` parameter for status checks

## How It Works

### SSH Execution
The workflow creates a simple script and executes it directly on the remote host via SSH. Best for quick tasks that don't require scheduler resource allocation.

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ Create      │ --> │ Execute     │ --> │ Stream      │
│ Script      │     │ via SSH     │     │ Output      │
└─────────────┘     └─────────────┘     └─────────────┘
```

### SLURM Execution
The workflow builds a SLURM job script using user-selected options and any additional scheduler directives. The script is submitted with `sbatch`, and its status is monitored using `squeue` and `sacct`.

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ Create      │ --> │ Submit      │ --> │ Monitor     │ --> │ Cleanup     │
│ SLURM Script│     │ via sbatch  │     │ via squeue  │     │             │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
```

### PBS Execution
The workflow constructs a PBS-compatible job script using the user-provided account and scheduler directives, submits it with `qsub`, monitors the queue, and waits for completion.

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ Create      │ --> │ Submit      │ --> │ Monitor     │ --> │ Cleanup     │
│ PBS Script  │     │ via qsub    │     │ via qstat   │     │             │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
```

## Monitoring & Cleanup

For PBS and SLURM, the workflow continuously monitors job status until completion or until the job is no longer found in the queue.

If the workflow run itself is canceled, the cleanup logic automatically attempts to terminate the remote job (`qdel` or `scancel`) to prevent orphaned workloads on the compute resource.

**v4.0 Additional Cleanup Features:**
- Runs user's `cancel.sh` script if present in the run directory
- Cleans up temporary files (jobid, CANCEL_STREAMING, job.started, HOSTNAME)
- SSH jobs attempt to kill background processes

---

## Usage

### As a Standalone Workflow

Deploy job_runner directly to run ad-hoc scripts on your resources:

```yaml
# Your workflow.yaml
uses: marketplace/job_runner/v4.0
```

### As a Reusable Component in Other Workflows

Reference job_runner from within your workflow's job steps:

```yaml
jobs:
  my_job:
    ssh:
      remoteHost: ${{ inputs.resource.ip }}
    steps:
      - name: Run My Script
        uses: marketplace/job_runner/v4.0
        with:
          resource: ${{ inputs.resource }}
          rundir: /path/to/workdir
          use_existing_script: true
          script_path: /path/to/my_script.sh
          scheduler: ${{ inputs.scheduler.enabled }}
          slurm:
            partition: ${{ inputs.slurm.partition }}
            time: ${{ inputs.slurm.time }}
            gres: "gpu:1"
```

---

## Input Reference

### Core Inputs

| Input | Type | Default | Description |
|-------|------|---------|-------------|
| `resource` | compute-clusters | (required) | The compute resource to execute the script on |
| `shebang` | string | `#!/bin/bash` | The shell interpreter line for the script |
| `rundir` | string | `${PWD}` | The directory where the script will be executed |

### Script Configuration

| Input | Type | Default | Description |
|-------|------|---------|-------------|
| `use_existing_script` | boolean | `false` | `true` = use script at `script_path`; `false` = use inline `script` |
| `script` | editor | (demo script) | Inline script content (when `use_existing_script=false`) |
| `script_path` | string | - | Path to existing script on target (when `use_existing_script=true`) |

### Job Control

| Input | Type | Default | Description |
|-------|------|---------|-------------|
| `scheduler` | boolean | `false` | `true` = submit to scheduler; `false` = execute via SSH |
| `inject_markers` | boolean | `true` | Auto-inject `job.started` and `HOSTNAME` markers (v4.0) |
| `poll_interval` | number | `15` | How often to check job status in seconds (v4.0) |

### SLURM Configuration

| Input | Type | Default | Description |
|-------|------|---------|-------------|
| `slurm.is_disabled` | boolean | (auto) | Auto-computed based on scheduler type |
| `slurm.account` | slurm-accounts | - | SLURM account (`--account`) |
| `slurm.partition` | slurm-partitions | - | SLURM partition (`--partition`) |
| `slurm.qos` | slurm-qos | - | Quality of Service (`--qos`) |
| `slurm.time` | string | `04:00:00` | Walltime limit (`--time`) |
| `slurm.nodes` | number | `1` | Number of nodes (`--nodes`) (v4.0) |
| `slurm.cpus_per_task` | number | `4` | CPUs per task (`--cpus-per-task`) (v4.0) |
| `slurm.gres` | string | - | Generic resources, e.g., `gpu:1` (`--gres`) (v4.0) |
| `slurm.mem` | string | - | Memory per node, e.g., `32G` (`--mem`) (v4.0) |
| `slurm.constraint` | string | - | Node constraint (`--constraint`) (v4.0) |
| `slurm.array` | string | - | Array job spec, e.g., `0-9` (`--array`) (v4.0) |
| `slurm.scheduler_directives` | editor | - | Additional `#SBATCH` directives |

### PBS Configuration

| Input | Type | Default | Description |
|-------|------|---------|-------------|
| `pbs.is_disabled` | boolean | (auto) | Auto-computed based on scheduler type |
| `pbs.account` | string | - | PBS account (`-A`) (v4.0) |
| `pbs.queue` | string | - | PBS queue (`-q`) (v4.0) |
| `pbs.walltime` | string | `04:00:00` | Walltime limit (`-l walltime=`) (v4.0) |
| `pbs.select` | string | - | Resource selection (`-l select=`) (v4.0) |
| `pbs.scheduler_directives` | editor | - | Additional `#PBS` directives |

---

## Examples

### Example 1: Simple SSH Execution

Run a script directly on the login node without scheduler:

```yaml
jobs:
  hello_world:
    steps:
      - name: Say Hello
        uses: marketplace/job_runner/v4.0
        with:
          resource: ${{ inputs.resource }}
          rundir: ~/my_project
          scheduler: false
          script: |
            echo "Hello from $(hostname)"
            echo "Current directory: $(pwd)"
            echo "Date: $(date)"
```

### Example 2: SLURM GPU Job

Submit a GPU job to SLURM:

```yaml
jobs:
  gpu_training:
    steps:
      - name: Train Model
        uses: marketplace/job_runner/v4.0
        with:
          resource: ${{ inputs.resource }}
          rundir: ${{ inputs.workdir }}
          use_existing_script: true
          script_path: ${{ inputs.workdir }}/train.sh
          scheduler: true
          slurm:
            is_disabled: false
            account: ${{ inputs.slurm.account }}
            partition: gpu
            time: "08:00:00"
            nodes: 1
            cpus_per_task: 8
            gres: "gpu:a100:2"
            mem: "64G"
```

### Example 3: PBS HPC Job

Submit a job to a PBS cluster:

```yaml
jobs:
  simulation:
    steps:
      - name: Run Simulation
        uses: marketplace/job_runner/v4.0
        with:
          resource: ${{ inputs.resource }}
          rundir: /scratch/$USER/simulation
          scheduler: true
          pbs:
            is_disabled: false
            account: my_allocation
            queue: normal
            walltime: "24:00:00"
            select: "4:ncpus=32:mpiprocs=32:ngpus=0"
          script: |
            module load openmpi
            mpirun -np 128 ./my_simulation --input config.yaml
```

### Example 4: SLURM Array Job (v4.0)

Submit an array job for parameter sweeps:

```yaml
jobs:
  parameter_sweep:
    steps:
      - name: Run Sweep
        uses: marketplace/job_runner/v4.0
        with:
          resource: ${{ inputs.resource }}
          rundir: ~/experiments
          scheduler: true
          slurm:
            is_disabled: false
            partition: compute
            time: "01:00:00"
            array: "0-99%10"  # 100 tasks, max 10 concurrent
          script: |
            echo "Running task ${SLURM_ARRAY_TASK_ID}"
            python process.py --index ${SLURM_ARRAY_TASK_ID}
```

### Example 5: Integration with activate-rag-vllm

The vLLM/RAG workflow uses job_runner for unified job submission:

```yaml
# From activate-rag-vllm/workflow.yaml
run_service:
  needs: [setup, prepare_containers, prepare_model, prepare_tiktoken]
  working-directory: ${{ needs.setup.outputs.rundir }}
  ssh:
    remoteHost: ${{ inputs.resource.ip }}
  steps:
    - name: Run Service
      uses: marketplace/job_runner/v4.0
      early-cancel: any-job-failed
      with:
        resource: ${{ inputs.resource }}
        shebang: '#!/bin/bash'
        rundir: ${{ needs.setup.outputs.rundir }}
        use_existing_script: true
        script_path: ${{ needs.setup.outputs.rundir }}/start_service.sh
        scheduler: ${{ inputs.scheduler.enabled }}
        inject_markers: true
        slurm:
          is_disabled: ${{ inputs.scheduler.slurm.is_disabled }}
          account: ${{ inputs.scheduler.slurm.account }}
          partition: ${{ inputs.scheduler.slurm.partition }}
          qos: ${{ inputs.scheduler.slurm.qos }}
          time: ${{ inputs.scheduler.slurm.time }}
          cpus_per_task: ${{ inputs.scheduler.slurm.cpus_per_task }}
          gres: ${{ inputs.scheduler.slurm.gres }}
          scheduler_directives: |
            ${{ inputs.scheduler.slurm.scheduler_directives }}
        pbs:
          is_disabled: ${{ inputs.scheduler.pbs.is_disabled }}
          account: ${{ inputs.scheduler.pbs.account }}
          queue: ${{ inputs.scheduler.pbs.queue }}
          walltime: ${{ inputs.scheduler.pbs.walltime }}
          select: ${{ inputs.scheduler.pbs.select }}
          scheduler_directives: |
            ${{ inputs.scheduler.pbs.scheduler_directives }}
```

### Example 6: Medical Fine-Tuning Workflow Integration

For workflows like `activate-medical-finetuning`:

```yaml
jobs:
  finetune:
    needs: [setup, download_data]
    steps:
      - name: Fine-tune Model
        uses: marketplace/job_runner/v4.0
        with:
          resource: ${{ inputs.resource }}
          rundir: ${{ needs.setup.outputs.workdir }}
          use_existing_script: true
          script_path: ${{ needs.setup.outputs.workdir }}/finetune.sh
          scheduler: ${{ inputs.use_scheduler }}
          inject_markers: true
          slurm:
            is_disabled: ${{ inputs.resource.schedulerType != 'slurm' || !inputs.use_scheduler }}
            partition: ${{ inputs.slurm.partition }}
            time: ${{ inputs.slurm.time }}
            gres: "gpu:${{ inputs.num_gpus }}"
            mem: "${{ inputs.memory }}G"
            scheduler_directives: |
              #SBATCH --exclusive
```

---

## Session Management Integration

When `inject_markers: true` (default in v4.0), job_runner automatically creates:

- **`job.started`** - Touched when the job begins execution
- **`HOSTNAME`** - Contains the compute node hostname

These markers enable session management workflows to:
1. Wait for the job to start
2. Determine the target hostname for port forwarding
3. Coordinate cleanup on job completion

Example session management pattern:

```yaml
create_session:
  needs: [setup]
  steps:
    - name: Wait for Job to Start
      run: |
        timeout=600; elapsed=0
        while [ ! -f ${{ needs.setup.outputs.rundir }}/job.started ]; do
          sleep 5; ((elapsed+=5))
          [[ $elapsed -ge $timeout ]] && exit 1
        done
    
    - name: Get Hostname
      run: |
        target_hostname=$(cat ${{ needs.setup.outputs.rundir }}/HOSTNAME | head -1)
        echo "target_hostname=${target_hostname}" >> $OUTPUTS
```

---

## Customization Tips

### Adding a Cancel Script

Create a `cancel.sh` in your run directory to handle cleanup when the workflow is cancelled:

```bash
#!/bin/bash
# cancel.sh - called by job_runner cleanup

# Stop your services
docker-compose down 2>/dev/null || true
singularity-compose down 2>/dev/null || true

# Kill background processes
pkill -f "my_app" 2>/dev/null || true

# Clean up temp files
rm -rf /tmp/my_cache_*
```

### Using as a Template

This workflow can serve as a template for more specialized workflows:

1. **Hide the script input**: Set `hidden: true` on the `script` input
2. **Pre-define the script**: Set `use_existing_script: true` and provide `script_path`
3. **Add custom inputs**: Extend the input section with workflow-specific parameters
4. **Reference inputs in script**: Use `${{ inputs.my_param }}` in your script

---

## Troubleshooting

### Job Submission Fails

1. Check that the resource has the correct `schedulerType` configured
2. Verify account/partition names are valid for the cluster
3. Check scheduler logs: `scontrol show job <jobid>` or `qstat -f <jobid>`

### Output Not Streaming

1. Ensure the script writes to stdout/stderr (not just files)
2. Check that `run.${PW_JOB_ID}.out` is being created in the rundir
3. Verify SSH connectivity to the resource

### Job Appears Stuck

1. Check the poll_interval setting (default 15 seconds)
2. Verify the job is actually running: `squeue -j <jobid>` or `qstat <jobid>`
3. Check for scheduler-specific issues (node failures, resource unavailability)

### Cleanup Not Running

1. Ensure the workflow is being cancelled (not just the browser closed)
2. Check that `scancel`/`qdel` commands are available on the resource
3. Verify the `jobid` file was created in the rundir

---

## License

Apache 2.0 - See LICENSE file for details.
