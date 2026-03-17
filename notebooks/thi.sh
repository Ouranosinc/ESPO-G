#!/bin/bash
#SBATCH --time=3:00:00       # modifier pour vos besoins
#SBATCH --account=ctb-frigon
#SBATCH --constraint=genoa    # pour accéder à bébé narval
#SBATCH --partition=c-frigon  # pour avoir la priorité Ouranos
#SBATCH --mem=200G #modifier selon vos besoins
#SBATCH --export=none         # optionnel


#source /project/ctb-frigon/julavoie/envs/espojan2026/bin/modules
#source /project/ctb-frigon/julavoie/envs/espojan2026/bin/activate

source /project/ctb-frigon/scenario/environnements/envs/xscen-0.14/bin/modules
source /project/ctb-frigon/scenario/environnements/envs/xscen-0.14/bin/activate

python /home/julavoie/code/lait-e/ESPO-G/notebooks/thi.py