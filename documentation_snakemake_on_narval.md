
# Le profile de snakemake
Pour éxecuter un workflow snakemake dans un cluster, on utilise la commande 

> $ snakemake --profile simple/

 avec *simple/* étant le nom du répertoire où se situe le fichier *config.v8+.yaml*. Ce nom du fichier est recommandé pour les versions de snakemake supérieures à 8.0.0. Pour générer un fichier en particulier, on écrit le nom du fichier après simple/. Exemple:
 

> $ snakemake --profile simple/ /project/ctb-frigon/oumou/ESPO-G6-SNAKEMAKE/reference/ref_south_nodup_noleap.zarr/

Dans le fichier *config.v8+.yaml* se trouvent les paramètres que l'on veut passer à la commande `snakemake`. Parmis les paramètres à passer il y a `executor` qui permet de choisir un plugin pour soumettre des tâches à des systèmes de clusters. Pour les versions de snakemake supérieure à 8.0.0, c'est `cluster-generic` qu'il faut utiliser. Il faut d'abord l'installer:

   

> $ pip install snakemake-executor-plugin-cluster-generic

    
`Cluster-generic`est un plugin générique qui donne accés à plusieurs types de plugin.  Ainsi `sbatch` est utilisé pour soumettre une tâche au système de gestion de tâches Slurm avec les options de notre choix:

    executor: cluster-generic  
    cluster-generic-submit-cmd:  
      mkdir -p slurm_logs/{rule} &&  
      sbatch  
        --partition=c-frigon  
        --account=ctb-frigon  
        --constraint=genoa  
        --cpus-per-task={threads}  
        --qos={resources.qos}  
        --mem={resources.mem_mb}  
        --job-name={rule}-{wildcards}  
        --output=slurm_logs/{rule}/{rule}-{wildcards}-%j.out  
        --time={resources.time}  
        --parsable  
    default-resources:  
      - qos=high_priority  
      - mem_mb=60000  
      - time=5  
    cluster-generic-status-cmd: status-sacct.sh  
    #restart-times: 3  
    max-jobs-per-second: 10  
    max-status-checks-per-second: 10  
    local-cores: 1  
    latency-wait: 60  
    jobs: 500  
    keep-going: True  
    rerun-incomplete: True  
    printshellcmds: True  
    scheduler: greedy

On peut utiliser les paramètres de snakemake comme {wildcards} et {rule} dans les options `sbatch` de slurm. Pour la règle `adjust` suivante:

    rule adjust:  
       input:  
            train = Path(config['paths']['exec_workdir'])/"ESPO-G_workdir/{sim_id}_{region}_{var}_training.zarr",  
            rechunk = Path(config['paths']['exec_workdir'])/"ESPO-G_workdir/{sim_id}_{region}_regchunked.zarr",  
       output:  
           directory(Path(config['paths']['exec_workdir'])/"ESPO-G_workdir/{sim_id}_{region}_{var}_adjusted.zarr")  
       wildcard_constraints:  
           region = r"[a-zA-Z]+_[a-zA-Z]+",  
           sim_id="([^_]*_){6}[^_]*"  
      log:  
            "logs/adjust_{sim_id}_{region}_{var}"  
      params:  
           n_workers=5,  
           threads=3  
      threads: 15  
      script:  
            f"{home}workflow/scripts/adjust.py"

 on aura les outputs de slurm avec comme noms:
 1. adjust-region=south_nodup,sim_id=CMIP6_ScenarioMIP_AS-RCEC_TaiESM1_ssp585_r1i1p1f1_global,var=tasmax-32072380.out
 2. adjust-region=north_nodup,sim_id=CMIP6_ScenarioMIP_AS-RCEC_TaiESM1_ssp585_r1i1p1f1_global,var=dtr-32072382.out
 3. adjust-region=middle_nodup,sim_id=CMIP6_ScenarioMIP_AS-RCEC_TaiESM1_ssp585_r1i1p1f1_global,var=dtr-32072381.out
 
`--cpus-per-task` prendra comme valeur 15, `--mem` sera égal à 60000 par defaut puis que `mem` n'est pas defini dans la section `resources` de de la règle. Pareil pour `--qos`, il prendra la valeur par défaut définie dans le profile soit `high_priority`. Après la définition des options `sbatch`  et des valeurs par défaut de `sbatch`, il y a le paramètre `cluster-generic-status-cmd: status-sacct.sh` qui sera passé à la commande snakemake et servira  à vérifier le statut des job soumis à slurm. Ce parametre est nécessaire surtout pour détecter les jobs qui échouent à cause du temps limite `--time`. Snakemake dépend par défaut de `cluster-status.py`, fournie par le profile slurm officiel de snakemake, pour connaître l'état des jobs de slurm. Cependant, certains jobs peuvent échouer silencieusement sans que snakemake ne s'en rende compte se qui fait que son exécution peut rester bloquée indéfinement. C'est pourquoi il y a d'autres alternatives fournies par snakemake pour gérer ce problème. Les fichiers dans [ extras/](https://github.com/jdblischak/smk-simple-slurm/tree/main/extras) permettent de gérer le statut des jobs de différente manière, il faut télécharger celui qui vous convient dans le même répertoire que *config.v8+.yaml*, le rendre exécutable avec la commande `

> $ chmod +x status-sacct.sh

 et ajouter `cluster-generic-status-cmd: status-sacct.sh` dans *config.v8+.yaml* et l'option `--parsable` sous `sbatch`. Il faut aussi bien choisir la valeur de `max-status-checks-per-second` qui correspond au nombre de fois maximum qu'on peut surveiller l'état de tous les jobs et non par job. C'est à dire que si `--max-status-checks-per-second` est défini à 10, alors il n’y aura pas plus de 10 requêtes envoyées par seconde, donc pour 500 jobs, cela signifie qu’il faudra environ 50 secondes pour vérifier toutes les tâches.
 Les job s sont bien soumis au cluster si les informations de snakemake ecrites à la console sont suivies de `Submitted job 28 with external jobid '32636155'.`
 Exemple:
 

    > Using profile simple/ for setting default command line arguments.
    Building DAG of jobs...
    Using shell: /cvmfs/soft.computecanada.ca/gentoo/2023/x86-64-v3/usr/bin/bash
    Provided remote nodes: 10
    Job stats:
    job                          count
    -------------------------  -------
    DIAGNOSTICS                      3
    adjust                           9
    all                              1
    clean_up                         3
    concatenation_diag               4
    concatenation_final              1
    diag_improved_et_heatmap         3
    diag_measures_improvement        4
    final_zarr                       3
    health_checks                    1
    off_diag_scen_prop_meas          4
    train                            9
    total                           45
    
    Select jobs to execute...
    Execute 9 jobs...
    
    [Wed Aug  7 11:10:41 2024]
    rule train:
        input: /project/ctb-frigon/oumou/ESPO-G6-SNAKEMAKE/reference/ref_middle_nodup_noleap.zarr, /project/ctb-frigon/oumou/ESPO-G6-SNAKEMAKE/reference/ref_middle_nodup_360_day.zarr, /scratch/oumou/ESPO-G6-SNAKEMAKE/ESPO-G_workdir/CMIP6_ScenarioMIP_AS-RCEC_TaiESM1_ssp585_r1i1p1f1_global_middle_nodup_regchunked.zarr
        output: /scratch/oumou/ESPO-G6-SNAKEMAKE/ESPO-G_workdir/CMIP6_ScenarioMIP_AS-RCEC_TaiESM1_ssp585_r1i1p1f1_global_middle_nodup_dtr_training.zarr
        jobid: 31
        reason: Missing output files: /scratch/oumou/ESPO-G6-SNAKEMAKE/ESPO-G_workdir/CMIP6_ScenarioMIP_AS-RCEC_TaiESM1_ssp585_r1i1p1f1_global_middle_nodup_dtr_training.zarr
        wildcards: sim_id=CMIP6_ScenarioMIP_AS-RCEC_TaiESM1_ssp585_r1i1p1f1_global, region=middle_nodup, var=dtr
        threads: 15
        resources: mem_mb=61989, mem_mib=954, disk_mb=1000, disk_mib=954, tmpdir=<TBD>, qos=high_priority, mem=65GB, time=60
    
    Submitted job 31 with external jobid '32636148'.
Et on peut voir l'etat des jobs avec la commande d slurm:

    $ sq
Lorsqu'on annule une job slurm associée à une règle snakemake, la règle échoue aussi. Par contre, si c'est le workflow de snakemake qui est annuler avec `ctrl + c` les jobs slurm associés doivent être annulées séparement avec la commande:

    $ scancel <JOBID>
     
ou
    

    $ scancel -u <USERNAME>

pour annuler tous les jobs soumis par l'utilisateur USERNAME.

# Erreurs fréquentes 
Lorsque `dask` utilise plus de `threads` que `slurm` , l'erreur ci dessous peut interrompre  l'exécution d'un ou plusieurs jobs sans pour autant faire appel à  `scancel`. Ce qui fait que le job reste dans l'état `R` jusqu'à la fin de `--time`.

    [nc31222:1355168:a:1360164]    ib_iface.c:746  Assertion `gid->global.interface_id != 0' failed
    ==== backtrace (tid:1360164) ====
     0 0x000000000001e2d0 uct_ib_iface_fill_ah_attr_from_gid_lid()  /tmp/ebuser/avx2/UCX/1.14.1/GCCcore-12.3.0/ucx-1.14.1/src/uct/ib/base/ib_iface.c:746
     1 0x000000000001e341 uct_ib_iface_fill_ah_attr_from_addr()  /tmp/ebuser/avx2/UCX/1.14.1/GCCcore-12.3.0/ucx-1.14.1/src/uct/ib/base/ib_iface.c:785
     2 0x0000000000063426 uct_ud_mlx5_iface_get_av()  /tmp/ebuser/avx2/UCX/1.14.1/GCCcore-12.3.0/ucx-1.14.1/src/uct/ib/ud/accel/ud_mlx5_common.c:48
     3 0x00000000000638f8 uct_ud_mlx5_iface_unpack_peer_address()  /tmp/ebuser/avx2/UCX/1.14.1/GCCcore-12.3.0/ucx-1.14.1/src/uct/ib/ud/accel/ud_mlx5.c:650
     4 0x0000000000059f23 uct_ud_iface_unpack_peer_address()  /tmp/ebuser/avx2/UCX/1.14.1/GCCcore-12.3.0/ucx-1.14.1/src/uct/ib/ud/base/ud_iface.h:524
     5 0x0000000000059f23 uct_ud_iface_cep_get_peer_address()  /tmp/ebuser/avx2/UCX/1.14.1/GCCcore-12.3.0/ucx-1.14.1/src/uct/ib/ud/base/ud_iface.c:50
     6 0x000000000005a14a uct_ud_iface_cep_get_ep()  /tmp/ebuser/avx2/UCX/1.14.1/GCCcore-12.3.0/ucx-1.14.1/src/uct/ib/ud/base/ud_iface.c:134
     7 0x000000000005ddc8 uct_ud_ep_rx_creq()  /tmp/ebuser/avx2/UCX/1.14.1/GCCcore-12.3.0/ucx-1.14.1/src/uct/ib/ud/base/ud_ep.c:802
     8 0x000000000005ddc8 uct_ud_ep_process_rx()  /tmp/ebuser/avx2/UCX/1.14.1/GCCcore-12.3.0/ucx-1.14.1/src/uct/ib/ud/base/ud_ep.c:993
     9 0x0000000000067b12 uct_ud_mlx5_iface_poll_rx()  /tmp/ebuser/avx2/UCX/1.14.1/GCCcore-12.3.0/ucx-1.14.1/src/uct/ib/ud/accel/ud_mlx5.c:527
    10 0x0000000000067b12 uct_ud_mlx5_iface_async_progress()  /tmp/ebuser/avx2/UCX/1.14.1/GCCcore-12.3.0/ucx-1.14.1/src/uct/ib/ud/accel/ud_mlx5.c:604
    11 0x00000000000635db uct_ud_iface_async_progress()  /tmp/ebuser/avx2/UCX/1.14.1/GCCcore-12.3.0/ucx-1.14.1/src/uct/ib/ud/base/ud_inl.h:274
    12 0x00000000000635db uct_ud_mlx5_iface_async_handler()  /tmp/ebuser/avx2/UCX/1.14.1/GCCcore-12.3.0/ucx-1.14.1/src/uct/ib/ud/accel/ud_mlx5.c:707
    13 0x00000000000170ec ucs_async_handler_invoke()  /tmp/ebuser/avx2/UCX/1.14.1/GCCcore-12.3.0/ucx-1.14.1/src/ucs/async/async.c:252
    14 0x00000000000170ec ucs_async_handler_dispatch()  /tmp/ebuser/avx2/UCX/1.14.1/GCCcore-12.3.0/ucx-1.14.1/src/ucs/async/async.c:274
    15 0x00000000000171fc ucs_async_dispatch_handlers()  /tmp/ebuser/avx2/UCX/1.14.1/GCCcore-12.3.0/ucx-1.14.1/src/ucs/async/async.c:306
    16 0x0000000000019b36 ucs_async_thread_ev_handler()  /tmp/ebuser/avx2/UCX/1.14.1/GCCcore-12.3.0/ucx-1.14.1/src/ucs/async/thread.c:88
    17 0x0000000000032301 ucs_event_set_wait()  /tmp/ebuser/avx2/UCX/1.14.1/GCCcore-12.3.0/ucx-1.14.1/src/ucs/sys/event_set.c:215
    18 0x000000000001a220 ucs_async_thread_func()  /tmp/ebuser/avx2/UCX/1.14.1/GCCcore-12.3.0/ucx-1.14.1/src/ucs/async/thread.c:131
    19 0x0000000000084a9d pthread_condattr_setpshared()  ???:0
    20 0x0000000000104fc0 __clone()  ???:0
    =================================
    [nc31222:1355168] *** Process received signal ***
    [nc31222:1355168] Signal: Aborted (6)
    [nc31222:1355168] Signal code:  (-6)
    [nc31222:1355168] [ 0] /cvmfs/soft.computecanada.ca/gentoo/2023/x86-64-v3/usr/lib64/libc.so.6(+0x38790)[0x1507d3baf790]
    [nc31222:1355168] [ 1] /cvmfs/soft.computecanada.ca/gentoo/2023/x86-64-v3/usr/lib64/libc.so.6(+0x867ac)[0x1507d3bfd7ac]
    [nc31222:1355168] [ 2] /cvmfs/soft.computecanada.ca/gentoo/2023/x86-64-v3/usr/lib64/libc.so.6(gsignal+0x12)[0x1507d3baf6f2]
    [nc31222:1355168] [ 3] /cvmfs/soft.computecanada.ca/gentoo/2023/x86-64-v3/usr/lib64/libc.so.6(abort+0xd3)[0x1507d3b994b2]
    [nc31222:1355168] [ 4] /cvmfs/soft.computecanada.ca/easybuild/software/2023/x86-64-v3/Compiler/gcccore/ucx/1.14.1/lib/libucs.so.0(+0x26e2b)[0x1507b18d2e2b]
    [nc31222:1355168] [ 5] /cvmfs/soft.computecanada.ca/easybuild/software/2023/x86-64-v3/Compiler/gcccore/ucx/1.14.1/lib/libucs.so.0(+0x26f11)[0x1507b18d2f11]
    [nc31222:1355168] [ 6] /cvmfs/soft.computecanada.ca/easybuild/software/2023/x86-64-v3/Compiler/gcccore/ucx/1.14.1/lib/ucx/libuct_ib.so.0(uct_ib_iface_fill_ah_attr_from_gid_lid+0x1b0)[0x1507b0c022d0]
    [nc31222:1355168] [ 7] /cvmfs/soft.computecanada.ca/easybuild/software/2023/x86-64-v3/Compiler/gcccore/ucx/1.14.1/lib/ucx/libuct_ib.so.0(uct_ib_iface_fill_ah_attr_from_addr+0x61)[0x1507b0c02341]
    [nc31222:1355168] [ 8] /cvmfs/soft.computecanada.ca/easybuild/software/2023/x86-64-v3/Compiler/gcccore/ucx/1.14.1/lib/ucx/libuct_ib.so.0(uct_ud_mlx5_iface_get_av+0x56)[0x1507b0c47426]
    [nc31222:1355168] [ 9] /cvmfs/soft.computecanada.ca/easybuild/software/2023/x86-64-v3/Compiler/gcccore/ucx/1.14.1/lib/ucx/libuct_ib.so.0(+0x638f8)[0x1507b0c478f8]
    [nc31222:1355168] [10] /cvmfs/soft.computecanada.ca/easybuild/software/2023/x86-64-v3/Compiler/gcccore/ucx/1.14.1/lib/ucx/libuct_ib.so.0(uct_ud_iface_cep_get_peer_address+0x13)[0x1507b0c3df23]
    [nc31222:1355168] [11] /cvmfs/soft.computecanada.ca/easybuild/software/2023/x86-64-v3/Compiler/gcccore/ucx/1.14.1/lib/ucx/libuct_ib.so.0(uct_ud_iface_cep_get_ep+0x5a)[0x1507b0c3e14a]
    [nc31222:1355168] [12] /cvmfs/soft.computecanada.ca/easybuild/software/2023/x86-64-v3/Compiler/gcccore/ucx/1.14.1/lib/ucx/libuct_ib.so.0(uct_ud_ep_process_rx+0x368)[0x1507b0c41dc8]
    [nc31222:1355168] [13] /cvmfs/soft.computecanada.ca/easybuild/software/2023/x86-64-v3/Compiler/gcccore/ucx/1.14.1/lib/ucx/libuct_ib.so.0(+0x67b12)[0x1507b0c4bb12]
    [nc31222:1355168] [14] /cvmfs/soft.computecanada.ca/easybuild/software/2023/x86-64-v3/Compiler/gcccore/ucx/1.14.1/lib/ucx/libuct_ib.so.0(+0x635db)[0x1507b0c475db]
    [nc31222:1355168] [15] /cvmfs/soft.computecanada.ca/easybuild/software/2023/x86-64-v3/Compiler/gcccore/ucx/1.14.1/lib/libucs.so.0(+0x170ec)[0x1507b18c30ec]
    [nc31222:1355168] [16] /cvmfs/soft.computecanada.ca/easybuild/software/2023/x86-64-v3/Compiler/gcccore/ucx/1.14.1/lib/libucs.so.0(ucs_async_dispatch_handlers+0x3c)[0x1507b18c31fc]
    [nc31222:1355168] [17] /cvmfs/soft.computecanada.ca/easybuild/software/2023/x86-64-v3/Compiler/gcccore/ucx/1.14.1/lib/libucs.so.0(+0x19b36)[0x1507b18c5b36]
    [nc31222:1355168] [18] /cvmfs/soft.computecanada.ca/easybuild/software/2023/x86-64-v3/Compiler/gcccore/ucx/1.14.1/lib/libucs.so.0(ucs_event_set_wait+0xb1)[0x1507b18de301]
    [nc31222:1355168] [19] /cvmfs/soft.computecanada.ca/easybuild/software/2023/x86-64-v3/Compiler/gcccore/ucx/1.14.1/lib/libucs.so.0(+0x1a220)[0x1507b18c6220]
    [nc31222:1355168] [20] /cvmfs/soft.computecanada.ca/gentoo/2023/x86-64-v3/usr/lib64/libc.so.6(+0x84a9d)[0x1507d3bfba9d]
    [nc31222:1355168] [21] /cvmfs/soft.computecanada.ca/gentoo/2023/x86-64-v3/usr/lib64/libc.so.6(__clone+0x40)[0x1507d3c7bfc0]
    [nc31222:1355168] *** End of error message ***
Pour s'assurer que le nombre de `threads` utilisés par `dask` soit toujours au minimum égal  à `--cpus-per-task`, j'utilse `params` où je déclare les paramètres:

    params:  
        n_workers=2,  
        threads_per_worker=3
        memory_limit=60000
       
qui seront utilisés dans la fonction

     LocalCluster(n_workers=snakemake.params.n_workers, threads_per_worker=snakemake.params.threads_per_worker,  
               memory_limit=f"{snakemake.params. memory_limit}MB", **daskkws)) 
            
la multiplication des deux doit être égale à:

    threads: 6
et sera affecté à cpus-per-task dans le profile:

    --cpus-per-task={threads}


Il faut demander aussi au mois autant de mémoire à slurm via `sbatch --mem` que `memory_limit*n_workers` de dasks pour éviter les `slurmstepd: error: Detected 1 oom-kill event(s) `.
> Written with [StackEdit](https://stackedit.io/).
<!--stackedit_data:
eyJoaXN0b3J5IjpbNjE4MDAwMDMsLTk4OTQ0MDQ3OSw0OTM2OT
U0MSwtMjE0MDEwMzU4LDg3NzY3MTg0NiwtMTkwODY5MjYwMiwx
OTc3NTEyNTEyXX0=
-->