#!/usr/bin/env python

# Example --cluster-status script from docs:
# https://snakemake.readthedocs.io/en/stable/tutorial/additional_features.html#using-cluster-status

import subprocess
import sys

jobid = sys.argv[1]

if jobid == "Submitted":
    sys.stderr.write("smk-simple-slurm: Invalid job ID: %s\n" % (jobid))
    sys.stderr.write("smk-simple-slurm: Did you remember to add the flag --parsable to your sbatch call?\n")
    sys.exit(1)

output = str(subprocess.check_output("sacct -j %s --format State --noheader | head -1 | awk '{print $1}'" % jobid,
                                     shell=True).strip())

# running_status = ["PENDING", "CONFIGURING", "COMPLETING", "RUNNING", "SUSPENDED"]
failed_status = ["FAILED", "CANCELLED", "TIMEOUT", "PREEMPTED", "NODE_FAIL", "REVOKED", "SPECIAL_EXIT"]
if "COMPLETED" in output:
    print("success")
elif any(r in output for r in failed_status):
    print("failed")
else:
    print("running")

