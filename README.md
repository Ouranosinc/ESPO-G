---


---

<h1 id="snakemake">Snakemake</h1>
<p>Snakemake est un outil inspiré de GNU Make, mais conçu pour être plus flexible et puissant. Il utilise une syntaxe basée sur Python pour définir des règles qui spécifient comment générer des fichiers de sortie à partir de fichiers d’entrée. Pour consulter la documentation officielle vous pouvez cliquer sur ce <a href="https://snakemake.readthedocs.io/en/stable/snakefiles/rules.html">lien</a>.<br>
Les workflows sont définis en termes de règles. Chaque règle spécifie comment créer un fichier de sortie à partir d’un ou plusieurs fichiers d’entrée. Voici un exemple de règle :</p>
<pre><code>    rule reference_DEFAULT:  
    output:  
        directory(Path(config['paths']['final'])/"reference/ref_{region}_default.zarr")  
    wildcard_constraints:  
        region=r"[a-zA-Z]+_[a-zA-Z]+"  
  params:  
        threads_per_worker= lambda wildcards,threads, resources: threads / resources.n_workers,  
        memory_limit=lambda wildcards, resources: int(resources.mem.rstrip("GB")) / resources.n_workers  
    threads: 10  
  resources:  
        mem='50GB',  
        n_workers=2  
  script:  
        f"{home}workflow/scripts/load_default_ref.py"
</code></pre>
<p>Une règle snakemake doit avoir un output c’est-à-dire le fichier qu’on veut créer. La manière dont le fichier et son contenu sont générés est spécifié dans le script, run ou shell. S’il s’agit d’un script, le chemin vers le fichier du script est donné comme dans l’exemple précédent. Dans le script on peut utiliser les paramèetres de snakemake par exemple on utilise <code>snakemake.input</code>si la règle ne possède qu’un seul fichier input ou bien  <code>snakemake.input[0]</code>  si elle possède une liste de fichiers input. On peut aussi appeler chaque fichier input par un nom, par exemple  <code>snakemake.input.south</code>si on a:</p>
<pre><code>input:  
    middle=Path(config['paths']['final'])/"reference/ref_middle_nodup_default.zarr"  
    north=Path(config['paths']['final'])/"reference/ref_ north_nodup_default.zarr"  
    south=Path(config['paths']['final'])/"reference/ref_south_nodup_default.zarr"
</code></pre>
<p>La section input n’est pas obligatoire c’est le cas dans la règle <code>reference_DEFAULT</code> dans <code>Makeref.smk</code>. Dans la règle ci-haut j’utilise la section <code>params</code> pour passer des valeurs aux paramètres de dask.distributed.LocalCluster et qu’elles soient en adéquation avec les ressources demandées à slurm. Donc le client sera appelé de la façon suivante dans le script <em>load_default_ref.py</em>:</p>
<pre><code>cluster = LocalCluster(n_workers=snakemake.resources.n_workers, threads_per_worker=snakemake.params.threads_per_worker,  
                       memory_limit=snakemake.params.memory_limit, **daskkws)  
client = Client(cluster)
</code></pre>
<p>Dans le script de soumission slurm (expliqué dans la partie Profile de Snakemake) on aura exactement <code>--cpus-per-task= n_workers*threads_per_worker</code> et <code>--mem=n_workers*memory_limit</code></p>
<p>Snakemake construit automatiquement un graphe acyclique dirigé (DAG) des tâches à partir des dépendances entre les règles. Cela permet de paralléliser les tâches et d’optimiser l’exécution. Le DAG associé à ESPO-G est la suivante:</p>
<h1 id="création-denvironment">Création d’environment</h1>
<h1 id="le-profile-de-snakemake">Le profile de snakemake</h1>
<p>Pour éxecuter un workflow snakemake dans un cluster, on utilise la commande</p>
<blockquote>
<p>$ snakemake --profile simple/</p>
</blockquote>
<p>avec <em>simple/</em> étant le nom du répertoire où se situe le fichier <em>config.v8+.yaml</em>. Ce nom du fichier est recommandé pour les versions de snakemake supérieures à 8.0.0. Pour générer un fichier en particulier, on écrit le nom du fichier après simple/. Exemple:</p>
<blockquote>
<p>$ snakemake --profile simple/ /project/ctb-frigon/oumou/ESPO-G6-SNAKEMAKE/reference/ref_south_nodup_noleap.zarr/</p>
</blockquote>
<p>Dans le fichier <em>config.v8+.yaml</em> se trouvent les paramètres que l’on veut passer à la commande <code>snakemake</code>. Parmis les paramètres à passer il y a <code>executor</code> qui permet de choisir un plugin pour soumettre des tâches à des systèmes de clusters. Pour les versions de snakemake supérieure à 8.0.0, c’est <code>cluster-generic</code> qu’il faut utiliser. Il faut d’abord l’installer:</p>
<blockquote>
<p>$ pip install snakemake-executor-plugin-cluster-generic</p>
</blockquote>
<p><code>Cluster-generic</code>est un plugin générique qui donne accés à plusieurs types de plugin.  Ainsi <code>sbatch</code> est utilisé pour soumettre une tâche au système de gestion de tâches Slurm avec les options de notre choix:</p>
<pre><code>executor: cluster-generic  
cluster-generic-submit-cmd:  
  mkdir -p slurm_logs/{rule} &amp;&amp;  
  sbatch  
    --partition=c-frigon  
    --account=ctb-frigon  
    --constraint=genoa  
    --cpus-per-task={threads}  
    --qos={resources.qos}  
    --mem={resources.mem}  
    --job-name={rule}-{wildcards}  
    --output=slurm_logs/{rule}/{rule}-{wildcards}-%j.out  
    --time={resources.time}  
    --parsable  
default-resources:  
  - qos=high_priority  
  - mem=60GB  
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
</code></pre>
<p>On peut utiliser les paramètres de snakemake comme {wildcards} et {rule} dans les options <code>sbatch</code> de slurm. Les wildcards ne peuvent pas contenir  “/” si vous voulez les utiliser dans le nom des fichiers lod de slurm. Cependant vous pouvez les utiliser dans --job-name.<br>
Pour la règle <code>adjust</code> suivante:</p>
<pre><code>rule adjust:  
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
</code></pre>
<p>on aura les outputs de slurm avec comme noms:</p>
<ol>
<li>adjust-region=south_nodup,sim_id=CMIP6_ScenarioMIP_AS-RCEC_TaiESM1_ssp585_r1i1p1f1_global,var=tasmax-32072380.out</li>
<li>adjust-region=north_nodup,sim_id=CMIP6_ScenarioMIP_AS-RCEC_TaiESM1_ssp585_r1i1p1f1_global,var=dtr-32072382.out</li>
<li>adjust-region=middle_nodup,sim_id=CMIP6_ScenarioMIP_AS-RCEC_TaiESM1_ssp585_r1i1p1f1_global,var=dtr-32072381.out</li>
</ol>
<p><code>--cpus-per-task</code> prendra comme valeur 15, <code>--mem</code> sera égal à 60GB par defaut puis que <code>mem</code> n’est pas defini dans la section <code>resources</code> de de la règle. Pareil pour <code>--qos</code>, il prendra la valeur par défaut définie dans le profile soit <code>high_priority</code>. Pour <code>time</code> sbatch accepte les heures définies à l’aide de différents formats par exemple hours :minutes :seconds ("00:00:00’) ou simplement minute (60).</p>
<p>Après la définition des options <code>sbatch</code>  et des valeurs par défaut de <code>sbatch</code>, il y a le paramètre <code>cluster-generic-status-cmd: status-sacct.sh</code> qui sera passé à la commande snakemake et servira  à vérifier le statut des job soumis à slurm. Ce parametre est nécessaire surtout pour détecter les jobs qui échouent à cause du temps limite <code>--time</code>. Snakemake dépend par défaut de <code>cluster-status.py</code>, fournie par le profile slurm officiel de snakemake, pour connaître l’état des jobs de slurm. Cependant, certains jobs peuvent échouer silencieusement sans que snakemake ne s’en rende compte se qui fait que son exécution peut rester bloquée indéfinement. C’est pourquoi il y a d’autres alternatives fournies par snakemake pour gérer ce problème. Les fichiers dans <a href="https://github.com/jdblischak/smk-simple-slurm/tree/main/extras"> extras/</a> permettent de gérer le statut des jobs de différente manière, il faut télécharger celui qui vous convient dans le même répertoire que <em>config.v8+.yaml</em>, le rendre exécutable avec la commande `</p>
<blockquote>
<p>$ chmod +x <a href="http://status-sacct.sh">status-sacct.sh</a></p>
</blockquote>
<p>et ajouter <code>cluster-generic-status-cmd: status-sacct.sh</code> dans <em>config.v8+.yaml</em> et l’option <code>--parsable</code> sous <code>sbatch</code>.<br>
On a notamment  le fichier <code>status-sacct.sh</code>, ce script est souvent recommandé. Il y a le fichier <code>status-sacct.py</code>qui utilise également la commande <code>sacct</code> mais est écrit en Python. 	Il y a un fichier <code>status-scontrol.sh</code> qui utilise <code>scontrol</code> et est écrit en bash. La diffèrence entre <code>sacct</code> et <code>scontrol</code> est que ce dernier ne montre que les informations sur les jobs en cours d’exécution ou qui sont récemment terminés (5 min) alors que <code>sacct</code>  renvoie des informations de la base de données, et fonctionne donc pour tous les jobs. Le derniers fichier est <code>status-sacct-robust.sh</code>, est une version de <code>status-sacct.sh</code> qui roule plusieurs fois la commande <code>sacct</code> si ce dernier n’arrive pas retourner l’état de la jobs puis retourne une erreur.</p>
<p>Il faut bien choisir la valeur de <code>max-status-checks-per-second</code> qui correspond au nombre de fois maximum qu’on peut voir l’état de tous les jobs et non par job. C’est à dire que si <code>--max-status-checks-per-second</code> est défini à 10, alors il n’y aura pas plus de 10 requêtes envoyées par seconde, donc pour 500 jobs, cela signifie qu’il faudra environ 50 secondes pour toutes les vérifier .<br>
Les jobs sont bien soumis au cluster si les informations de snakemake écrites à la console sont suivies de <code>Submitted job 28 with external jobid '32636155'.</code><br>
Exemple:</p>
<pre><code>Using profile simple/ for setting default command line arguments.
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
    resources: mem_mb=61989, mem_mib=954, disk_mb=1000, disk_mib=954, tmpdir=&lt;TBD&gt;, qos=high_priority, mem=65GB, time=60

Submitted job 31 with external jobid '32636148'.
</code></pre>
<p>Et on peut voir l’etat des jobs avec la commande d slurm:</p>
<pre><code>$ sq
</code></pre>
<p>Lorsqu’on annule une job slurm associée à une règle snakemake, la règle échoue aussi. Par contre, si c’est le processus Snakemake qui est annuler avec <code>ctrl + c</code> les jobs slurm associés doivent être annulées séparement avec la commande:</p>
<pre><code>$ scancel &lt;JOBID&gt;
</code></pre>
<p>ou</p>
<pre><code>$ scancel -u &lt;USERNAME&gt;
</code></pre>
<p>Pour annuler tous les jobs soumis par l’utilisateur USERNAME.<br>
Pour annuler automatiquement tous les travaux en cours d’exécution lorsque vous annulez le processus principal de Snakemake (c’est-à-dire le comportement par défaut de --drmaa), vous pouvez spécifier <code>cluster-generic-cancel-cmd : scancel</code> dans <em>config.v8+.yaml</em> . De la même manière que pour --cluster-generic-status-cmd, vous devez inclure l’indicateur --parsable à la commande sbatch passée à --cluster-generic-cancel-cmd afin de transmettre l’ID de tâche à scancel.<br>
<strong>Remarque :</strong> N’appuyez qu’une seule fois sur Ctrl-C. Si vous appuyez trop rapidement une deuxième fois, Snakemake sera tué avant qu’il ne puisse terminer d’annuler tous les travaux avec scancel.</p>
<h1 id="arborescence-des-fichiers">Arborescence des fichiers</h1>
<h1 id="erreurs-fréquentes">Erreurs fréquentes</h1>
<p>Lorsque <code>dask</code> utilise plus de <code>threads</code> que <code>slurm</code> , l’erreur ci dessous peut interrompre  l’exécution d’un ou plusieurs jobs sans pour autant faire appel à  <code>scancel</code>. Ce qui fait que le job reste dans l’état <code>R</code> jusqu’à la fin de <code>--time</code>.</p>
<pre><code>[nc31222:1355168:a:1360164]    ib_iface.c:746  Assertion `gid-&gt;global.interface_id != 0' failed
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
</code></pre>
<p>Pour s’assurer que le nombre de <code>threads</code> utilisés par <code>dask</code> soit toujours au minimum égal  à <code>--cpus-per-task</code>, j’utilse <code>params</code> où je déclare les paramètres:</p>
<pre><code>params:  
    n_workers=2,  
    threads_per_worker=3
    memory_limit=60000
</code></pre>
<p>qui seront utilisés dans la fonction</p>
<pre><code> LocalCluster(n_workers=snakemake.params.n_workers, threads_per_worker=snakemake.params.threads_per_worker,  
           memory_limit=f"{snakemake.params. memory_limit}MB", **daskkws)) 
</code></pre>
<p>la multiplication des deux doit être égale à:</p>
<pre><code>threads: 6
</code></pre>
<p>et sera affecté à cpus-per-task dans le profile:</p>
<pre><code>--cpus-per-task={threads}
</code></pre>
<p>Il faut demander aussi au mois autant de mémoire à slurm via <code>sbatch --mem</code> que <code>memory_limit*n_workers</code> de dasks pour éviter les <code>slurmstepd: error: Detected 1 oom-kill event(s)</code>.</p>
<blockquote>
<p>Written with <a href="https://stackedit.io/">StackEdit</a>.</p>
</blockquote>

