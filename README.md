---


---

<h1 id="snakemake">Snakemake</h1>
<p>Snakemake est un outil inspiré de GNU Make, mais conçu pour être plus flexible et puissant. Il utilise une syntaxe basée sur Python pour définir des règles qui spécifient comment générer des fichiers de sortie à partir de fichiers d’entrée. Pour consulter la documentation officielle, vous pouvez cliquer sur ce <a href="https://snakemake.readthedocs.io/en/stable/snakefiles/rules.html">lien</a>.<br>
Les workflows sont définis en termes de règles. Chaque règle spécifie comment créer un ou des fichiers de sortie à partir d’un ou plusieurs fichiers d’entrée. Voici un exemple de règle :</p>
<pre><code>region=[south, north]

rule reference_DEFAULT:
	input:
		"chemin/vers/fichierInput.zarr"
	output:
		"chemin/vers/ref_{region}.zarr"
	script:
		"load_ref.py"
</code></pre>
<p>Ici l’objectif est de générer les fichiers:</p>
<pre><code>chemin/vers/ref_north.zarr
chemin/vers/ref_south.zarr
</code></pre>
<p>en exécutant le script <strong>load_ref.py</strong> qui utilise le fichier <strong>“chemin/vers/fichierInput.zarr”</strong> comme point de départ. Le script peut ressembler à:</p>
<pre><code>import xarray as xr  
import xscen as xs  
import xclim as xc

if __name__ == '__main__':  
	  # load input_file 
	  input = xr.open_zarr(snakemake.input.rechunk)  
	  # 
	  # do your stuff 
	  #
	  xs.save_to_zarr(input, str(snakemake.output[0]))
</code></pre>
<h1 id="narval">Narval</h1>
<p>Le cluster narval permet d’optimiser la parallélisation d’un workflow en le divisant en plusieurs jobs qui peuvent s’exécuter en même temps.</p>
<p>Les jobs sont soumis à l’ordonnanceur <strong>slurm</strong> qui planifie l’exécution de chaque job en fonction des ressources disponibles.<br>
Les jobs non interactifs sont soumis via <code>sbatch</code>.<br>
Pour soumettre une tâche (exemple <code>echo 'Hello, world!'</code>) à slurm, il faudra donc écrire un script de soumission <code>soumission.sh</code> de la forme:</p>
<pre><code>#!/bin/bash

#SBATCH --time=00:15:00  
#SBATCH --account=def-frigon

echo 'Hello, world!'  
sleep 30  
</code></pre>
<p>et exécuter la commande:</p>
<pre><code>$ sbatch soumission.sh  
Submitted batch job 123456  
</code></pre>
<p>Ce job réservera par défaut 1 core et 256MB de mémoire pour 15 minutes. <code>--time</code> et <code>--account</code> sont des arguments sbatch obligatoires pour soumettre un job sur Narval. Il est possible de choisir la quantité de mémoire et de cores en ajoutant les options sbatch <code>--mem</code> ou <code>--mem-per-cpu</code> et <code>--cpus-per-task</code>.</p>
<p>Il est conseillé de créer un environment pour chaque job. Exemple:</p>
<pre><code>#!/bin/bash

#SBATCH --account=def-frigon  
#SBATCH --mem-per-cpu=1.5G # increase as needed  
#SBATCH --time=1:00:00

module load python/3.10  
virtualenv --no-download $SLURM_TMPDIR/env  
source $SLURM_TMPDIR/env/bin/activate  
pip install --no-index --upgrade pip

pip install --no-index -r requirements.txt  
echo 'Hello, world!'  
</code></pre>
<p>Narval contient trois principaux répertoires: <strong>HOME</strong>, <strong>SCRATCH</strong> et <strong>PROJECT</strong>.<br>
Le HOME a un quota fixe par utilisateur et est sauvegardé tous les jours, le SCRATCH a un grand quota par utilisateur qui sert à stocker les fichiers temporaires et PROJECT a un large quota qui est sauvegardé tous les jours.<br>
Il ne faut pas créer un environment dans le SCRATCH.</p>
<h1 id="snakemake-sur-narval">Snakemake sur narval</h1>
<p>Pour utiliser snakemake sur <strong>narval</strong>, il faut créer un environment snakemake:</p>
<pre><code>module load StdEnv/2023 gcc openmpi python/3.11 arrow/16.1.0 openmpi netcdf proj esmf geos mpi4py 
virtualenv --no-download &lt;NOM-ENV&gt; 
source &lt;NOM-ENV&gt;/bin/activate 
pip install --no-index --upgrade pip 
pip install --no-index -r "/project/ctb-frigon/scenario/environnements/xscen0.9.0-requirements.txt" 
pip install --no-index snakemake==8.12.0
pip install --no-index snakemake-executor-plugin-cluster-generic
</code></pre>
<p>Les règles doivent avoir d’autres directives en plus de <strong>input</strong>, <strong>output</strong> et <strong>script</strong>. La directive <code>resources</code> est utilisée pour passer des valeurs à <code>sbatch</code>. Ainsi chaque script de soumission demandera des ressources spécifiques à chaque règle. Exemple:</p>
<pre><code>region=[south, north]

rule maRegle: 
	input:
		"chemin/vers/fichierInput.zarr" 
    output:  
        "chemin/vers/ref_{region}.zarr" 
    resources:
	    mem="1.5G",
	    cpus=10
    script:  
        "load_ref.py"
</code></pre>
<p>Toutefois, pour écrire le script de soumission associé à une règle snakemake, il faudra soit directement l’écrire à la console:</p>
<pre><code>snakemake \
    --jobs 10 \ #nombre totale de jobs dans la liste de soumission
    --cluster '   # pour dire a snakemake de rouler la règle dans un cluster
      sbatch \    # choisir le gestionnaire de cluster slurm
        --mem 10G \
        --account ctb-frigon \
        --cpus-per-task 6\
        --time 02:00:00 \
</code></pre>
<p>soit créer un profile snakemake qui se chargera de soumettre les jobs en utilisant les options sbatch souhaitées pour chaque règle.<br>
Il suffit de taper la commande:</p>
<pre><code>$ snakemake --profile simple/  
</code></pre>
<p>avec <em><strong>simple/</strong></em> étant le nom du répertoire où se situe le fichier <em><strong>config.v8+.yaml</strong></em>. Ce nom du fichier est recommandé pour les versions de snakemake supérieures à 8.0.0.<br>
Le contenu de <em><strong>config.v8+.yaml</strong></em> sera donc:</p>
<pre><code>executor: cluster-generic  
cluster-generic-submit-cmd: 
  sbatch  
    --account=ctb-frigon    
    --cpus-per-task={resources.cpus}  
    --mem={resources.mem}   
    --time={resources.time}
    --parsable  
default-resources:  
  - mem=80GB  
  - time=120
cluster-generic-cancel-cmd: "scancel"  
cluster-generic-status-cmd: status-sacct.py  
restart-times: 3  
</code></pre>
<p>Le paramètre <code>executor</code> permet de choisir un plugin pour soumettre des tâches à des systèmes de clusters. Pour les versions de snakemake supérieure à 8.0.0, c’est <code>cluster-generic</code> qu’il faut utiliser.</p>
<p><code>Cluster-generic</code>est un plugin générique qui donne accès à plusieurs types de plugin. Slurm est sélectionné via <code>sbatch</code>. <code>resources.cpus</code> et <code>resources.mem</code> seront remplacés respectivement par “1.5G” et 10. Puisque <code>maRegle</code> n’a pas resources.time, c’est la valeur par défaut du fichier <em><strong>config.v8+.yaml</strong></em> qui sera prise, 120. <code>--parsable</code> stocke le <strong>job ID</strong>.</p>
<p>Le paramètre <code>cluster-generic-cancel-cmd: scancel</code> permet d’annuler les jobs slurm lorsque le processus de snakemake est interrompu.</p>
<p><strong>Remarque :</strong> si vous appuyez trop rapidement <strong>Ctrl-C</strong> une deuxième fois, Snakemake sera tué avant qu’il ne puisse terminer d’annuler tous les travaux avec <code>scancel</code>.</p>
<p>Le paramètre <code>cluster-generic-status-cmd: status-sacct.sh</code> vérifie l’état des jobs soumis à slurm. Il est nécessaire surtout pour détecter les jobs qui échouent à cause du temps limite <code>--time</code> car par défaut Snakemake ne vérifie pas l’état <strong>TIMEOUT</strong>. <code>status-sacct.sh</code> est un script parmi quatre autres proposés par  <a href="https://github.com/jdblischak/smk-simple-slurm/tree/main/extras">snakemake</a>.<br>
Ces fichiers utilisent <code>sacct</code> ou <code>scontrol</code>.<br>
<code>scontrol</code> ne montre que les informations sur les jobs en cours d’exécution ou qui sont récemment terminés (5 min) alors que <code>sacct</code> renvoie des informations de la base de données, et fonctionne donc pour tous les jobs.<br>
Le script de statut doit être dans le répertoire <strong>simple/</strong> et dois être exécutable.</p>
<p><code>restart-times</code> exécute jusqu’à 3 fois la règle en cas d’échec.</p>
<p><strong>Attention:</strong> les jobs sont bien soumis au cluster si les informations de snakemake écrites à la console sont suivies de <code>Submitted job 28 with external jobid '32636155'.</code> Et on peut voir l’état des jobs avec la commande slurm:</p>
<pre><code>$ sq  
</code></pre>
<h1 id="espo-on-snakemake-on-narval">ESPO on snakemake on narval</h1>
<p>Le workflow est stocké dans le référentiel git de la structure suivante :</p>
<pre><code>├── Snakefile
├── config
│   ├── config.yaml
|   ├── off-properties_ESPO-G.yaml
|   ├── portraits.yaml
|   └── properties_ESPO-G.yaml
├── simple
|   ├── config.v8+.yaml
|   └── status-sacct.sh
├── workflow
│   ├── rules
|   │   ├── common.smk
|   │   | 
|   │   |        .
|   │   |        .
|   │   |        .  
|   │   |  
|   │   └── markeref.smk
│   ├── scripts
|   │   ├── adjust.py
|   │   | 
|   │   |        .
|   │   |        .
|   │   |        .  
|   │   |  
|   │   └── train.py
├── dag.png
├── report.html
</code></pre>
<h2 id="snakefile">Snakefile</h2>
<p>Il faut obligatoirement avoir un fichier dans le répertoire courant, appelé <em><strong>Snakefile</strong></em> ou <em><strong>snakefile</strong></em> afin de pouvoir utiliser la commande <code>snakemake</code>. Pour des workflows ayant peu de règles, il n’est pas nécessaire d’avoir des fichiers <em>.smk</em>, toutes les règles peuvent être écrites dans le <em>Snakefile</em>. Cependant, la première règle qui doit être définie est la règle <strong>all</strong>.</p>
<p>Elle définit les fichiers cibles finaux que l’on souhaite obtenir à la fin du workflow. En d’autres termes, elle indique à Snakemake quels fichiers doivent être générés pour que le workflow soit considéré comme terminé.<br>
La règle all de ESPO-G est:</p>
<pre><code>rule all:  
   input:  
       expand(Path(config['paths']['exec_workdir']) / "ESPO-G_workdir/diag-improved_{sim_id}_{dom_name}.zarr", sim_id=sim_id_name,dom_name=dom),  
       expand(Path(config['paths']['exec_workdir']) / "ESPO-G_workdir/DIAGNOCTICS_diag-heatmap_{sim_id}_{region}.zarr", sim_id=sim_id_name,region=region_name),  
       expand(Path(config['paths']['exec_workdir']) / "ESPO-G_workdir/DIAGNOCTICS_diag-improved_{sim_id}_{region}.zarr", sim_id=sim_id_name, region=region_name),  
       expand(Path(config['paths']['final'])/"diagnostics/NAM/{sim_id}/{level}_{sim_id}_NAM.zar", sim_id=sim_id_name,level=level_name),  
       expand(Path(config['paths']['final']) / "checks/NAM/{sim_id}_NAM_checks.zarr", sim_id=sim_id_name),  
       Path(config['paths']['final']) / "diagnostics/NAM/ECMWF-ERA5-Land_NAM/diag-ref-prop_ECMWF-ERA5-Land_NAM.zar"
</code></pre>
<p>C’est dans le fichier Snakfile qu’il faut associer les fichiers <strong>.smk</strong> au processus snakemake:</p>
<pre><code>include: "workflow/rules/Makeref.smk  
</code></pre>
<p>On peut contraindre snakemake à utiliser une version minimale en ajoutant dans le Snakefile:</p>
<pre><code>from snakemake.utils import min_version  
  
##### set minimum snakemake version #####  
min_version("8.0.0")  
</code></pre>
<p>C’est aussi dans le <em><strong>Snakefile</strong></em> qu’on associe le workflow à un fichier de <strong>configuration</strong>. Snakefile n’accepte qu’un seul fichier de configuration qu’on importe de la sorte:</p>
<pre><code>configfile: "config/config.yaml"  
</code></pre>
<h3 id="config">Config</h3>
<p>Les fichiers de configuration sont utilisés à la fois par snakemake et par l’interpréteur python. Snakemake utilise <code>config</code> exemple <code>config["custom"]["regions"]</code> et python utilise <code>xscen.CONFIG</code>.<br>
Le répertoire <strong>config/</strong> contient:</p>
<ul>
<li><strong>config.yaml:</strong> fournis la plupart des arguments des fonctions utilisées dans les scripts</li>
<li><strong>off-properties_ESPO-G.yaml:</strong> fournie à <code>xs.properties_and_measures</code> présent dans les scripts des règles <em>off_diag_scen_prop_meas, off_diag_sim_prop_meas</em> et <em>off_diag_ref_prop</em>, un chemin d’accès à un fichier YAML qui indique comment calculer les</li>
<li><strong>properties_ESPO-G.yaml:</strong> fournie à <code>xs.properties_and_measures</code> utilisé dans le script de la règle <em>DIAGNOSTICS</em> un chemin d’accès à un fichier YAML qui indique comment calculer les propriétés</li>
</ul>
<h2 id="simple">simple</h2>
<p>Le répertoire simple a deux fichiers, le fichier <em><strong>config.v8+.yaml</strong></em> et <strong><code>status-sacct.sh</code></strong>.</p>
<h3 id="config.v8.yaml">config.v8+.yaml</h3>
<p>Comme discuté dans le chapitre Snakemake sur narval, <em><strong>config.v8+.yaml</strong></em> est utilisé pour passer des paramètres à la commande <code>snakemake</code>. En plus des paramètres donnés en exemple dans le chapitre Snakemake sur narval, le profile de ESPO en introduit d’autres puisqu’il roule plusieurs jobs en même temps.</p>
<pre><code>executor: cluster-generic  
cluster-generic-submit-cmd:  
  mkdir -p logs/{rule} &amp;&amp;   # crée un repertoire pour sauvegarder les fichiers output de slurm
  sbatch   
    --partition=c-frigon  
    --account=ctb-frigon  
    --constraint=genoa  
    --cpus-per-task={resources.cpus_per_task}
    --qos={resources.qos}  
    --mem={resources.mem}  
    --job-name={rule}-{wildcards}
    --output=logs/{rule}/{rule}-{wildcards}-%j.out 
    --time={resources.time}  
    --parsable
default-resources:  
  - qos=high_priority  
  - mem=80GB  
  - time=20  
# non-slurm profile defaults
cluster-generic-cancel-cmd: "scancel"  
cluster-generic-status-cmd: status-sacct.sh  
restart-times: 3  
max-jobs-per-second: 10
max-status-checks-per-second: 30
local-cores: 1
latency-wait: 60
jobs: 10
keep-going: True
rerun-incomplete: True
printshellcmds: True
</code></pre>
<p><strong>mkdir -p logs/{rule}:</strong> crée un repertoire pour sauvegarder les fichiers output de slurm</p>
<p><strong>sbatch --partition:</strong> pour avoir la priorité Ouranos<br>
<strong>sbatch --account:</strong>  choisir un compte. Obligatoire sur narval<br>
<strong>sbatch --constraint:</strong> pour accéder à bébé narval<br>
<strong>sbatch --cpus-per-task:</strong> nombre de workers de dasks<br>
<strong>sbatch --job-name:</strong>  renommer le nom de la job en fonction de du nom de la règle et des ses wildcards<br>
<strong>sbatch --output:</strong> renommer le nom du fichier output en fonction de du nom de la règle et des ses wildcards<br>
<strong>sbatch --parsable:</strong> pour que sbatch renvoie uniquement le job ID sans aucun texte supplémentaire. Est obligatoire si on utilise cluster-generic-status-cmd.<br>
<strong>cluster-generic-cancel-cmd:</strong><br>
<strong>cluster-generic-status-cmd:</strong> permet d’annuler les jobs slurm lorsque le processus de snakemake est interrompu<br>
<strong>restart-times:</strong> exécute jusqu’à 3 fois la règle en cas d’échec.<br>
<strong>max-jobs-per-second:</strong>  Cela peut être utile pour éviter de surcharger le cluster avec trop de soumissions simultanées.<br>
<strong>max-status-checks-per-second:</strong> le nombre total de vérification d’état de tous les jobs<br>
<strong>local-cores:</strong> pour les règle qui s’exécutent localement. Exemple: localrules: nom_de_la_regle<br>
<strong>latency-wait:</strong> attendre un certain temps pour que les fichiers soient visibles en cas de MissingFileExeption error<br>
<strong>jobs:</strong> le maximum de jobs qui peuvent être roulés en parallèle<br>
<strong>keep-going:</strong>  pour continuer à exécuter les règles qui sont independantes d’une règle qui a échoué<br>
<strong>rerun-incomplete:</strong>  permet de relancer les tâches qui n’ont pas été complètement exécutées lors d’une précédente exécution<br>
<strong>printshellcmds:</strong>  pour que snakemake affiche les commandes shell qui sont exécutées pour chaque règle. Cela peut être très utile pour le<br>
débogage.</p>
<p><strong>Remarque:</strong></p>
<ul>
<li>il faut bien choisir la valeur de <code>max-status-checks-per-second</code><br>
qu’il corresponde au nombre de fois maximum qu’on peut voir l’état de<br>
tous les jobs et non par job. C’est à dire que si<br>
<code>--max-status-checks-per-second</code> est défini à 10, alors il n’y aura<br>
pas plus de 10 requêtes envoyées par seconde, donc pour 500 jobs,<br>
cela signifie qu’il faudra environ 50 secondes pour toutes les<br>
vérifier.</li>
<li>Les wildcards ne peuvent pas contenir <strong>“/”</strong> si vous voulez les<br>
utiliser dans <code>--output</code>. Cependant vous pouvez les utiliser dans<br>
<code>--job-name</code>.</li>
<li>Sbatch accepte <code>--time</code> définies à l’aide de différents formats par<br>
exemple hours :minutes :seconds ("00:00:00’) ou simplement minute<br>
(60).</li>
</ul>
<p>La commande shell soumise pour chaque règle ainsi que les statistiques sur l’utilisation des ressources utilisées par le job slurm de la règle peuvent être consultées à la page de <a href="https://portail.narval.calculquebec.ca/">l’alliance</a>.</p>
<h3 id="status-sacct.sh"><a href="http://status-sacct.sh">status-sacct.sh</a></h3>
<p>Comme expliqué dans le chapitre <strong>Snakemake sur narval</strong>, <code>status-sacct.sh</code> sert d’option à l’argument <code>cluster-generic-status-cmd</code>.<br>
Il a subi quelques modifications pour pouvoir être utilisé dans ESPO. Avant snakemake annulait la job si le script n’arrivait pas connaître son statut c’est-à-dire pour tout statut différent de ["“COMPLETED"PENDING”, “CONFIGURING”, “COMPLETING”, “RUNNING”, “SUSPENDED”], la règle est automatiquement annulée alors que le job slurm associé est peut-être toujours valide. Ce qui fait que snakemake va essayer de reexécuter la règle créant un autre job. Il y aura donc deux jobs associés à la même règle qui tenteront d’ouvrir et de modifier les mêmes fichiers.</p>
<p>Maintenant le script est écrit de la sorte:</p>
<pre><code>if [[ "$jobid" == Submitted ]]  
then  
  echo smk-simple-slurm: Invalid job ID: "$jobid" &gt;&amp;2  
  echo smk-simple-slurm: Did you remember to add the flag --parsable to your sbatch call? &gt;&amp;2  
  exit 1  
fi  
  
output=`sacct -j "$jobid" --format State --noheader | head -n 1 | awk '{print $1}'` 
 
if [[ $output =~ ^(COMPLETED).* ]]  
then  
  echo success  
elif [[ $output =~ ^(FAILED|CANCELLED|TIMEOUT|PREEMPTED|NODE_FAIL|REVOKED|SPECIAL_EXIT).* ]]  
then  
  echo failed  
else  
  echo running  
fi
</code></pre>
<p>Par conséquent, tant que la status n’est pas [“FAILED”, “CANCELLED”, “TIMEOUT”, “PREEMPTED”, “NODE_FAIL”, “REVOKED”, “SPECIAL_EXIT”], la règle n’est pas annulée.</p>
<h2 id="workflow">workflow</h2>
<p>Dans <strong>workflow/</strong> se trouve <code>rules/</code> pour les fichiers <strong>.smk</strong> et <strong>/scripts/</strong> pour les scripts des règles.</p>
<p>Les fichiers <code>.smk</code> permettent d’organiser et de structurer le pipeline de manière claire et modulaire. Chaque task dans le config est divisé en plusieurs règles regroupées dans un fichier .smk portant le nom de la task. Il y a 11 fichiers .smk correspondant aux tasks:</p>
<pre><code>tasks:  
	- makeref  
	- extract  
	- regrid  
	- rechunk  
	- train  
	- adjust  
	- clean_up  
	- final_zarr  
	- diagnostics  
	- concat  
	- health_checks  
	- official-diag  
</code></pre>
<p>le task <strong>concat</strong> est inclus dans <strong>diagnostics</strong> et leurs règles est définis dans <strong>DIAGNOSTICS.smk</strong>.</p>
<p>Un douzième fichier est appelé <strong>common.smk</strong>. Il est utilisé pour définir des fonctions qui seront utilisées par les autres fichiers .smk ce qui permet de ne pas trop les surcharger avec du code. Dans cette règle-ci dessous la fonction <code>inputfiles</code> est directement appelée dans la section <code>input</code>:</p>
<pre><code>rule prop:  
    input:  
        ref=inputfiles  
    output:  
        prop="workdir/prop_{sim_id}.zarr" 
  resources:  
        mem='30GB',  
        n_workers=3, 
        cpus_per_task=6, 
        time=60  
  script:  
        prop.py
</code></pre>
<p>et la définition de la fonction dans <em><strong>common.smk</strong></em> pourrait être:</p>
<pre><code>def inputfiles(wildcards):  
	ref=mon/chemin/ref_{wildcards.sim_id}.zarr"  
	return ref  
</code></pre>
<p>Il faut noter l’argument <code>wildcards</code> de <code>inputfiles</code> qui est présent, car la fonction fait appel aux wildcards de la règle <code>prop</code>.</p>
<p>Dans la règle ci-haut, le script <strong><a href="http://prop.py">prop.py</a></strong> serait dans le sous-répertoire <strong>scripts/</strong> de <strong>workflow/</strong>.</p>
<h2 id="graphe-acyclique-dirigé-ou-dag">Graphe acyclique dirigé ou DAG</h2>
<p>Snakemake construit automatiquement un graphe acyclique dirigé (DAG) des tâches à partir des dépendances entre les règles. Cela permet de paralléliser les tâches et d’optimiser l’exécution. Le graphe acyclique dirigé peut être obtenu avec la commande</p>
<pre><code>$ snakemake --dag all | dot -Tpng &gt; nom_du_fichier.png  
</code></pre>
<p>On peut remplacer l’extension .png, par .svg ou .pdf.<br>
Le DAG associé à ESPO-G est la suivante:<br>
<img src="" alt="Graphe acyclique dirigé"></p>
<h2 id="report.html">Report.html</h2>
<p>Une fois votre workflow terminé, vous pouvez générer le rapport en exécutant la commande suivante :</p>
<pre><code>snakemake --report report.html  
</code></pre>
<p>Cette commande créera un rapport HTML détaillé contenant des statistiques d’exécution, la topologie du workflow et les résultats. Il est pratique pour connaître le temps moyen d’exécution des règles.</p>
<h1 id="informations-utiles-pour-comprendre-snakemake">Informations utiles pour comprendre snakemake</h1>
<h2 id="wildcards">Wildcards</h2>
<p>Le workflow ESPO de base a une grosse boucle <code>for</code> pour boucler sur trois régions.<br>
Les wildcards sont utilisés pour alléger le code et automatiser la notation des fichiers. Au lieu de boucler sur les régions, on utilise les wildcards dans les fichiers <code>input</code> et <code>output</code>. Exemple dans la règle <code>reference_NOLEAP</code> de <strong>Makeref.smk</strong>, il y a:</p>
<pre><code>input:  
	Path(config['paths']['final'])/"reference/ref_{region}_default.zarr"  
output:  
	directory(Path(config['paths']['final'])/"reference/ref_{region}_noleap.zarr")  
</code></pre>
<p>donc dans le script associé, <strong>load_noleap_ref.py</strong>, on a :</p>
<pre><code>ds_ref = xr.open_zarr(snakemake.input[0]) 
#convert calendars  
ds_refnl = convert_calendar(ds_ref, "noleap")  
xs.save_to_zarr(ds_refnl, str(snakemake.output[0]))
</code></pre>
<p>au lieu de</p>
<pre><code>for region_name, region_dict in CONFIG['custom']['regions'].items():
  if not pcat.exists_in_cat(domain=region_name, calendar='noleap', source=ref_source):
          ds_ref = pcat.search(source=ref_source,calendar='default',domain=region_name).to_dask()
      
          ds_refnl = convert_calendar(ds_ref, "noleap")
          save_move_update(ds=ds_refnl,
                           pcat=pcat,
                           init_path=f"{exec_wdir}/ref_{region_name}_noleap.zarr",
                           final_path=f"{refdir}/ref_{region_name}_noleap.zarr",
                           info_dict={'calendar': 'noleap'})
</code></pre>
<p>Pour chaque fichier input, le script associé à <code>reference_NOLEAP</code> est exécuté et toutes les variables <code>snakemake.wildcards.region</code> présentes dans le script sont remplacées par la valeur actuelle du wildcard <code>region</code> .<br>
La valeur des wildcards est spécifiée que lors de l’exécution du workflow, dans la règle <code>all</code>, où toutes les valeurs possibles du wildcards sont passées à la fonction <code>expand()</code>.</p>
<pre><code>rule all:  
	input:  
		expand(Path(config['paths']['final'])/"reference/ref_{region}_noleap.zarr", region=list(config["custom"]["regions"].keys())  
</code></pre>
<p>La fonction <code>expand()</code> génère tous les chemins possibles en remplaçant le wildcard <code>region</code> par ses valeurs. Donc pour les régions <strong>middle_nodup, north_nodup</strong> et <strong>south_nodup</strong>, c’est comme si on avait</p>
<pre><code>rule all:  
	input:  
		Path(config['paths']['final'])/"reference/ref_middle_nodup_default.zarr"  
		Path(config['paths']['final'])/"reference/ref_ north_nodup_default.zarr"  
		Path(config['paths']['final'])/"reference/ref_south_nodup_default.zarr"  
</code></pre>
<p>Pour générer un fichier en particulier, exemple:</p>
<pre><code>Path(config['paths'['final'])/"reference/ref_{region}_noleap.zarr"  
</code></pre>
<p>pour <code>middle_nodup</code>, on exécute la commande:</p>
<pre><code>$ snakemake --profile simple/ /project/ctb-frigon/oumou/ESPO-G6-stage/reference/ref_middle_nodup_noleap.zarr/  
</code></pre>
<p><strong>Remarque:</strong> les fichiers input ne doivent pas contenir des wildcards qui ne sont pas présents dans les fichiers output. De plus, plusieurs wildcards dans un même nom de fichier peuvent provoquer une ambiguïté. Considérez le nom fichier suivant:</p>
<pre><code>Path(config['paths']['exec_workdir'])/"ESPO-G_workdir/{sim_id}_{region}_extracted.zarr"
</code></pre>
<p>dans la règle <strong>extract</strong> et supposez qu’un fichier</p>
<pre><code>CMIP6_ScenarioMIP_AS-RCEC_TaiESM1_ssp585_r1i1p1f1_global_middle_nodup_extracted.zarr  
</code></pre>
<p>est disponible. Il n’est pas clair si</p>
<p><code>sim_id=CMIP6_ScenarioMIP_AS-RCEC_TaiESM1</code> et <code>region=ssp585_r1i1p1f1_global_middle_nodup</code><br>
ou<br>
<code>sim_id=CMIP6_ScenarioMIP_AS-RCEC_TaiESM1_ssp585_r1i1p1f1_global</code> et <code>region=middle_nodup</code></p>
<p>C’est pourquoi une contrainte a été ajoutée à la wildcards <code>region</code> pour qu’il soit composé de deux chaînes de caractères séparées par un tiret du bas. Le wildcards sim_id est aussi contraint à avoir minimum 6 underscords:</p>
<pre><code>wildcard_constraints:  
	region = r"[a-zA-Z]+_[a-zA-Z]+",  
	sim_id="([^_]*_){6}[^_]*"  
</code></pre>
<h2 id="section-params-et-resources">Section params et resources</h2>
<pre><code>rule reference_DEFAULT:  
	output:  
		directory(Path(config['paths']['final'])/"reference/ref_{region}_default.zarr")  
	wildcard_constraints:  
		region=r"[a-zA-Z]+_[a-zA-Z]+"  
	params:  
		threads_per_worker= lambda wildcards,threads, resources: int(resources.cpus_per_task / resources.n_workers),  
		memory_limit=lambda wildcards, resources: int(resources.mem.rstrip("GB")) / resources.n_workers  
	resources:  
		mem='5GB',  
		n_workers=2,  
		cpus_per_task=1,  
		time=160  
	script:  
		f"{home}workflow/scripts/load_default_ref.py"  
</code></pre>
<p>Dans cette règle, la section <code>params</code> sert à passer des valeurs aux paramètres de dask.distributed.LocalCluster dans le script <em><strong>load_default_ref.py</strong></em> et qu’elles soient en adéquation avec les ressources demandées à slurm. Seul <code>n_workers</code>est dans ressources car pour que <code>resources.mem</code> et <code>resources.cpus-per-task</code>soient respectivement égales à <code>params.memory_limit</code> et <code>params.cpus-per-task</code>, j’utilise la fonction <code>lambda</code> qui ne peut pas prendre comme paramètre <code>params</code> .</p>
<p>Le client sera appelé de la façon suivante dans le script <em><strong>load_default_ref.py</strong></em>:</p>
<pre><code>cluster = LocalCluster(n_workers=snakemake.resources.n_workers, threads_per_worker=snakemake.params.threads_per_worker,  
					   memory_limit=snakemake.params.memory_limit, **daskkws)  
client = Client(cluster)  
</code></pre>
<h2 id="section-script-shell-ou-run">Section script, shell ou run</h2>
<p>Une règle snakemake doit avoir une section <code>output</code> c’est-à-dire le fichier qu’on veut créer. La manière dont le fichier et son contenu sont générés est spécifiée dans la section <code>script</code>, <code>run</code> ou <code>shell</code>.</p>
<p>S’il s’agit d’un script, le chemin vers le fichier du script est donné comme dans l’exemple précédent. Dans le script on peut utiliser les paramètres de snakemake par exemple on utilise <code>snakemake.input</code>si la règle ne possède qu’un seul fichier input ou bien <code>snakemake.input[0]</code> si elle possède une liste de fichiers input. On peut aussi appeler chaque fichier input par un nom, par exemple <code>snakemake.input.south</code>si on a:</p>
<pre><code>input:  
	middle=Path(config['paths']['final'])/"reference/ref_middle_nodup_default.zarr"  
	north=Path(config['paths']['final'])/"reference/ref_ north_nodup_default.zarr"  
	south=Path(config['paths']['final'])/"reference/ref_south_nodup_default.zarr"  
</code></pre>
<p>Ceci est aussi valable pour les fichiers output.</p>
<p>À la place de <code>script</code> , on peut utiliser <code>shell</code> pour écrire des commandes. Par défaut, c’est des commandes shell invoquées avec <code>bash</code>. À l’intérieur de la commande shell, toutes les variables locales et globales, en particulier les inputs et output, sont accessibles. Exemple:</p>
<pre><code>rule complex_conversion:  
	input:  
		"{dataset}/inputfile"  
	output:  
		"{dataset}/file.{group}.txt"  
	shell:  
		"somecommand --group {wildcards.group} &lt; {input} &gt; {output}"  
</code></pre>
<p>Comme dernière option pour générer les fichiers output il y a <code>run</code> qui permet d’écrire à même la règle, des codes python et des commandes shell.</p>
<pre><code>rule NAME:  
	input: "path/to/inputfile", "path/to/other/inputfile"  
	output: "path/to/outputfile", somename = "path/to/another/outputfile"  
	run:  
		for f in input:  
			...  
			with open(output[0], "w") as out:  
			out.write(...)  
		with open(output.somename, "w") as out:  
		out.write(...)  
</code></pre>
<p>Dans <code>run</code> pour écrire des commandes shell on utilise <code>shell()</code>. Exemple:</p>
<pre><code>shell("somecommand {output.somename}")  
</code></pre>
<h1 id="erreurs-non-résolue">Erreurs non résolue</h1>
<p>Puisque les jobs utilisent bien moins qu’un nœud au complet, Slurm essaie de les rouler d’une manière aussi “compacte” que possible, en y mettant trois, quatre voire davantage sur un seul nœud. Il est possible que quelque part dans Dask, il y ait des instructions qui supposent que les fils d’exécution de Dask ne partagent pas l’espace de mémoire ou d’autres ressources du nœud avec des fils d’exécution Dask venant d’un autre job. Ces conflits entre fils d’exécution Dask n’arrivent pas à tous les coups, mais de temps en temps, selon le hasard de Dask et l’ordre dans lequel Slurm lance les tâches sur ce nœud. Par conséquent, l’erreur ci-dessous peut interrompre l’exécution d’un ou plusieurs jobs.</p>
<pre><code>[nc31222:1355168:a:1360164] ib_iface.c:746 Assertion `gid-&gt;global.interface_id != 0' failed  
==== backtrace (tid:1360164) ====  
0 0x000000000001e2d0 uct_ib_iface_fill_ah_attr_from_gid_lid() /tmp/ebuser/avx2/UCX/1.14.1/GCCcore-12.3.0/ucx-1.14.1/src/uct/ib/base/ib_iface.c:746  
1 0x000000000001e341 uct_ib_iface_fill_ah_attr_from_addr() /tmp/ebuser/avx2/UCX/1.14.1/GCCcore-12.3.0/ucx-1.14.1/src/uct/ib/base/ib_iface.c:785  
2 0x0000000000063426 uct_ud_mlx5_iface_get_av() /tmp/ebuser/avx2/UCX/1.14.1/GCCcore-12.3.0/ucx-1.14.1/src/uct/ib/ud/accel/ud_mlx5_common.c:48  
3 0x00000000000638f8 uct_ud_mlx5_iface_unpack_peer_address() /tmp/ebuser/avx2/UCX/1.14.1/GCCcore-12.3.0/ucx-1.14.1/src/uct/ib/ud/accel/ud_mlx5.c:650  
4 0x0000000000059f23 uct_ud_iface_unpack_peer_address() /tmp/ebuser/avx2/UCX/1.14.1/GCCcore-12.3.0/ucx-1.14.1/src/uct/ib/ud/base/ud_iface.h:524  
5 0x0000000000059f23 uct_ud_iface_cep_get_peer_address() /tmp/ebuser/avx2/UCX/1.14.1/GCCcore-12.3.0/ucx-1.14.1/src/uct/ib/ud/base/ud_iface.c:50  
6 0x000000000005a14a uct_ud_iface_cep_get_ep() /tmp/ebuser/avx2/UCX/1.14.1/GCCcore-12.3.0/ucx-1.14.1/src/uct/ib/ud/base/ud_iface.c:134  
7 0x000000000005ddc8 uct_ud_ep_rx_creq() /tmp/ebuser/avx2/UCX/1.14.1/GCCcore-12.3.0/ucx-1.14.1/src/uct/ib/ud/base/ud_ep.c:802  
8 0x000000000005ddc8 uct_ud_ep_process_rx() /tmp/ebuser/avx2/UCX/1.14.1/GCCcore-12.3.0/ucx-1.14.1/src/uct/ib/ud/base/ud_ep.c:993  
9 0x0000000000067b12 uct_ud_mlx5_iface_poll_rx() /tmp/ebuser/avx2/UCX/1.14.1/GCCcore-12.3.0/ucx-1.14.1/src/uct/ib/ud/accel/ud_mlx5.c:527  
10 0x0000000000067b12 uct_ud_mlx5_iface_async_progress() /tmp/ebuser/avx2/UCX/1.14.1/GCCcore-12.3.0/ucx-1.14.1/src/uct/ib/ud/accel/ud_mlx5.c:604  
11 0x00000000000635db uct_ud_iface_async_progress() /tmp/ebuser/avx2/UCX/1.14.1/GCCcore-12.3.0/ucx-1.14.1/src/uct/ib/ud/base/ud_inl.h:274  
12 0x00000000000635db uct_ud_mlx5_iface_async_handler() /tmp/ebuser/avx2/UCX/1.14.1/GCCcore-12.3.0/ucx-1.14.1/src/uct/ib/ud/accel/ud_mlx5.c:707  
13 0x00000000000170ec ucs_async_handler_invoke() /tmp/ebuser/avx2/UCX/1.14.1/GCCcore-12.3.0/ucx-1.14.1/src/ucs/async/async.c:252  
14 0x00000000000170ec ucs_async_handler_dispatch() /tmp/ebuser/avx2/UCX/1.14.1/GCCcore-12.3.0/ucx-1.14.1/src/ucs/async/async.c:274  
15 0x00000000000171fc ucs_async_dispatch_handlers() /tmp/ebuser/avx2/UCX/1.14.1/GCCcore-12.3.0/ucx-1.14.1/src/ucs/async/async.c:306  
16 0x0000000000019b36 ucs_async_thread_ev_handler() /tmp/ebuser/avx2/UCX/1.14.1/GCCcore-12.3.0/ucx-1.14.1/src/ucs/async/thread.c:88  
17 0x0000000000032301 ucs_event_set_wait() /tmp/ebuser/avx2/UCX/1.14.1/GCCcore-12.3.0/ucx-1.14.1/src/ucs/sys/event_set.c:215  
18 0x000000000001a220 ucs_async_thread_func() /tmp/ebuser/avx2/UCX/1.14.1/GCCcore-12.3.0/ucx-1.14.1/src/ucs/async/thread.c:131  
19 0x0000000000084a9d pthread_condattr_setpshared() ???:0  
20 0x0000000000104fc0 __clone() ???:0  
=================================  
[nc31222:1355168] *** Process received signal ***  
[nc31222:1355168] Signal: Aborted (6)  
[nc31222:1355168] Signal code: (-6)  
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
<p>Les solutions pour contourner ce problème, c’est soit s’assurer que jamais deux jobs ne se trouvent sur un même nœud, bien que cela risque de gaspiller les ressources de la grappe. Soit reéxécuter les jobs qui échouent. La dernière option est la meilleure puisque snakemake propose un mécanisme qui permet de reéxécuter des règles qui échouent autant de fois qu’on souhaite grâce à <code>restart-times</code>.</p>

