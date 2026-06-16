#!/bin/bash
#SBATCH --time=24:00:00       # modifier pour vos besoins
#SBATCH --account=ctb-frigon
#SBATCH --constraint=genoa    # pour accéder à bébé narval
#SBATCH --partition=c-frigon  # pour avoir la priorité Ouranos
#SBATCH --mem=500G #modifier selon vos besoins
#SBATCH --export=none         # optionnel


source /project/ctb-frigon/scenario/environnements/envs/xscen-0.14/bin/modules
source /project/ctb-frigon/scenario/environnements/envs/xscen-0.14/bin/activate

python /home/julavoie/code/DQM/ESPO-R/ESPO-G/pre-workflow/input-checks.py