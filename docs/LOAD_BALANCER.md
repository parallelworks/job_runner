# Load Balancer Implementation

## Overview

This document describes the multi-site load balancing implementation for the job runner system. The feature enables job submission across multiple compute resources (SSH, PBS, SLURM sites) with two execution modes: **race mode** (first-to-start wins) and **parallel mode** (run on all sites simultaneously).

**Implementation Status:** Complete - see `v5.0.yaml`

---

## Architecture

### Self-Contained Workflow: `v5.0.yaml`

The implementation is fully self-contained within a single YAML file (~1500 lines), with all scheduler logic embedded directly. This approach:
- Avoids complexity of sub-workflow invocation
- Keeps all coordination logic in one place
- Supports 5 sites (site_0 through site_4) with SSH, SLURM, and PBS schedulers
- Maintains backward compatibility with v4.0.yaml (no modifications required)

### High-Level Architecture

```
v5.0-loadbalancer.yaml
    │
    ├── initialize
    │   └── Validate sites, create coordination directory lb_${PW_JOB_ID}/
    │
    ├── site_0 ──► SSH/SLURM/PBS (parallel)
    ├── site_1 ──► SSH/SLURM/PBS (parallel)
    ├── site_2 ──► SSH/SLURM/PBS (parallel)
    ├── site_3 ──► SSH/SLURM/PBS (parallel)
    ├── site_4 ──► SSH/SLURM/PBS (parallel)
    │
    ├── log (aggregated output streaming)
    │
    └── cleanup (generate summary, signal stop)
```

---

## Execution Modes

### Race Mode

Submit to all enabled sites in parallel. When the first job starts running (`job.started` file appears), cancel all other pending/queued jobs.

```
Submit to ALL Sites (parallel)
         │
    ┌────┴────┬────────┐
    ▼         ▼        ▼
 [Site 1]  [Site 2]  [Site 3]
    │         │        │
    ▼         ▼        ▼
 Monitor   Monitor   Monitor
    │         │        │
    └────┬────┴────────┘
         │
         ▼
  First job.started detected?
         │
    Yes ─┴─ No (all failed)
    │           │
    ▼           ▼
 Cancel      Report
 Others      Failure
    │
    ▼
 Wait for winner completion
    │
    ▼
 Cleanup all sites
```

**Use Case:** Resource availability varies; want fastest time-to-start regardless of site.

### Parallel Mode

Submit to all enabled sites in parallel. Wait for all jobs to complete, aggregating results.

```
Submit to ALL Sites (parallel)
         │
    ┌────┴────┬────────┐
    ▼         ▼        ▼
 [Site 1]  [Site 2]  [Site 3]
    │         │        │
    ▼         ▼        ▼
 Run to    Run to    Run to
 completion completion completion
    │         │        │
    └────┬────┴────────┘
         │
         ▼
 Aggregate Results
 (success/failure per site)
         │
         ▼
 Generate Summary Report
```

**Use Case:** Run same computation across multiple sites for redundancy, comparison, or distributed processing.

---

## Input Schema (Implemented)

The workflow uses individual site groups (`sites_0` through `sites_4`) rather than arrays, since the workflow YAML doesn't support dynamic loops.

### Core Inputs

| Input | Type | Default | Description |
|-------|------|---------|-------------|
| `execution_mode` | select | `race` | Race (first wins) or Parallel (all run) |
| `rundir` | string | `${PWD}` | Base directory for execution |
| `poll_interval` | number | `10` | Status check interval (seconds) |
| `use_existing_script` | boolean | `false` | Use script file vs inline content |
| `script` | editor | sample | Script content to execute |
| `script_path` | string | - | Path to existing script |

### Per-Site Configuration (sites_0 through sites_4)

Each site has its own configuration group with:

| Input | Type | Default | Description |
|-------|------|---------|-------------|
| `enabled` | boolean | site_0: true, others: false | Include site in execution |
| `name` | string | `Site-N` | Human-readable identifier |
| `resource` | compute-clusters | - | Target compute resource |
| `priority` | number | 1-5 | Lower = higher priority (race mode) |
| `scheduler` | boolean | false | Use scheduler vs direct SSH |
| `slurm.*` | group | - | SLURM settings (account, partition, time, nodes) |
| `pbs.*` | group | - | PBS settings (account, queue, walltime) |

---

## Job Structure (Implemented)

### Jobs Overview

| Job | Purpose | Runs On |
|-----|---------|---------|
| `initialize` | Create coordination directory, validate sites | Local |
| `site_0` - `site_4` | Submit and monitor jobs per site | Remote (SSH) |
| `log` | Aggregate output streaming from all sites | Local |
| `cleanup` | Generate summary, signal completion | Local |

### Site Job Logic

Each site job (site_0 through site_4) contains self-contained logic for:

1. **Script Creation**: Copy existing or create from inline content
2. **Marker Injection**: Add `job.started` and `HOSTNAME` markers
3. **Scheduler Detection**: Determine SLURM, PBS, or SSH based on resource
4. **Job Submission**: Build and submit scheduler script (sbatch/qsub) or execute directly
5. **Race Mode Coordination**: Check for `../WINNER` file before/during execution
6. **Monitoring Loop**: Poll job status until `job.ended`
7. **Cleanup Handler**: Cancel scheduler jobs on workflow cancellation

### Coordination Files

```
${rundir}/lb_${PW_JOB_ID}/
├── enabled_count          # Number of enabled sites
├── events.jsonl           # Structured event log
├── summary.json           # Final execution summary
├── WINNER                 # (race mode) ID of winning site
├── STOP_STREAMING         # Signal to stop log aggregation
│
├── site_0/
│   ├── status             # PENDING|SUBMITTING|SUBMITTED|RUNNING|COMPLETED|FAILED|CANCELLED
│   ├── name               # Human-readable site name
│   ├── priority           # Site priority
│   ├── run.sh             # Generated execution script
│   ├── run.out            # Job output
│   ├── job.started        # Created when job starts running
│   ├── job.ended          # Created when job completes
│   ├── jobid              # Scheduler job ID (if applicable)
│   ├── exit_code          # Script exit code (SSH mode)
│   └── CANCEL_REQUESTED   # Signal to cancel this site
│
├── site_1/
│   └── ...
└── ...
```

---

## Fault Tolerance (Implemented)

### Race Mode Behavior

- Sites check for `../WINNER` file before and during execution
- First site to create `job.started` writes its ID to `../WINNER`
- Other sites detect `WINNER` file and cancel gracefully
- Scheduler jobs are cancelled via `scancel`/`qdel`

### Cleanup Handlers

Each site job has a cleanup handler that:
1. Cancels any running scheduler job
2. Creates `job.ended` marker
3. Sets status to `CANCELLED` if not already set

### Status Tracking

Sites track their state in the `status` file:
- `PENDING` - Initial state
- `SUBMITTING` - Creating and submitting job
- `SUBMITTED` - Job submitted to scheduler
- `RUNNING` - Job actively executing
- `COMPLETED` - Job finished successfully
- `FAILED` - Job failed
- `CANCELLED` - Job cancelled (race mode loser or workflow cancel)

---

## Files

| File | Description |
|------|-------------|
| `v5.0.yaml` | Main load balancer workflow (~1500 lines) |
| `LOAD_BALANCER.md` | This documentation |

No modifications to `v4.0.yaml` are required - the load balancer is fully self-contained.

---

## Usage

### Basic Race Mode (2 Sites)

1. Enable `sites_0` and `sites_1`
2. Configure resources for each site
3. Set `execution_mode` to "race"
4. First site to start running wins; other is cancelled

### Parallel Mode (Multiple Sites)

1. Enable desired sites
2. Configure resources and scheduler settings for each
3. Set `execution_mode` to "parallel"
4. All sites run to completion; summary shows results

### Example Summary Output

```json
{
  "execution_id": "abc123",
  "mode": "race",
  "timestamp": "2025-01-21T10:30:00-05:00",
  "winner": "site_0",
  "total_sites": 3,
  "completed": 1,
  "failed": 0,
  "cancelled": 2
}
```

---

## Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Architecture | Self-contained YAML | Simpler than sub-workflow invocation |
| Site count | 5 sites (0-4) | Practical limit, easily extensible |
| Coordination | File-based (`WINNER`, `status`) | Consistent with v4.0 patterns |
| Output streaming | Polling with prefix | Real-time visibility per site |
| Scheduler support | SLURM + PBS + SSH | Matches v4.0 capabilities |
