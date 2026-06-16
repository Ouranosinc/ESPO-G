#!/bin/bash
#SBATCH --time=2:00:00       # modifier pour vos besoins
#SBATCH --account=ctb-frigon
#SBATCH --constraint=genoa    # pour accéder à bébé narval
#SBATCH --partition=c-frigon  # pour avoir la priorité Ouranos
#SBATCH --mem=100G #modifier selon vos besoins
#SBATCH --export=none         # optionnel

# Script utilitaire qui crée l'environnement fourni par Ouranos
source /project/ctb-frigon/scenario/environnements/config_env_slurm.sh xscen-0.12

python /home/julavoie/code/DQM/ESPO-G/pre-workflow/create_mask.py