#!/bin/bash
#SBATCH --time=6:00:00       # modifier pour vos besoins
#SBATCH --account=ctb-frigon
#SBATCH --constraint=genoa    # pour accéder à bébé narval
#SBATCH --partition=c-frigon  # pour avoir la priorité Ouranos
#SBATCH --mem=500G #modifier selon vos besoins
#SBATCH --export=none         # optionnel


source /project/ctb-frigon/julavoie/envs/dqm/bin/modules
source /project/ctb-frigon/julavoie/envs/dqm/bin/activate

python /home/julavoie/code/test-vs/ESPO-G/hx/hx.py