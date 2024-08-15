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
<p>en exécutant le script <strong>load_ref.py</strong> qui utilise le fichier  <strong>“chemin/vers/fichierInput.zarr”</strong> comme point de départ. Le script peut ressembler à:</p>
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
<p>Les jobs sont soumis à l’ordonnanceur <strong>slurm</strong> qui  planifie l’exécution de chaque job en fonction des ressources disponibles.<br>
Les jobs non intéractives sont soumis via <code>sbatch</code> et les jobs intéractives sont soumis via <code>srun</code>.<br>
Pour soumettre une tâche (exemple <code>echo 'Hello, world!'</code>)à slurm, il faudra donc écrire un script de soumission <code>soumission.sh</code> de la forme:</p>
<pre><code>#!/bin/bash
#SBATCH --time=00:15:00
#SBATCH --account=def-frigon
echo 'Hello, world!'
sleep 30
</code></pre>
<p>et éxécuter la commande:</p>
<pre><code>$ sbatch soumission.sh
Submitted batch job 123456
</code></pre>
<p>Ce job réservera par défaut 1 core et 256MB de mémoire pour 15 minutes.  <code>--time</code> et <code>--account</code> sont des argument sbatch obligatoire pour soumettre un job sur Narval. Il possible de choisir la quantité de mémoire et de cores en ajoutant les options sbatch <code>--mem</code> ou <code>--mem-per-cpu</code> et <code>--cpus-per-task</code>.<br>
Il est conseillé de créer un environment pour chaque job et il est possible de le faire dans le script de soumission. Exemple:</p>
<pre><code>#!/bin/bash

#SBATCH --account=def-frigon
#SBATCH --mem-per-cpu=1.5G      # increase as needed
#SBATCH --time=1:00:00

module load python/3.10
virtualenv --no-download $SLURM_TMPDIR/env
source $SLURM_TMPDIR/env/bin/activate
pip install --no-index --upgrade pip

pip install --no-index -r requirements.txt
echo 'Hello, world!'
</code></pre>
<p>Narval contient trois principaux répertoire: <strong>HOME</strong>, <strong>SCRATCH</strong> et <strong>PROJECT</strong>.<br>
Le HOME a un quota fixe par utilisateur et est sauvegardé tous les jours, le SCRATCH  a un grand quota par utilisateur qui sert à stocker les fichiers temporaires et PROJECT a un large quota qui est sauvegardé tous les jour.<br>
Il ne faut pas créer un environment de le SCRATCH.</p>
<h1 id="snakemake-sur-narval">Snakemake sur narval</h1>
<p>Pour utiliser snakemake sur <strong>narval</strong>, il faut créer un environment snakemake.<br>
D’abord on crée le fichier <em><strong>requirement.text</strong></em>:</p>
<pre><code>[name@server ~]$ module load StdEnv/2023 gcc openmpi python/3.11 arrow/16.1.0 openmpi netcdf proj esmf geos mpi4py 
[name@server ~]$ ENVDIR=/tmp/$RANDOM
[name@server ~]$ virtualenv --no-download $ENVDIR
[name@server ~]$ source $ENVDIR/bin/activate
(xxxx)[name@server ~]$ pip install --no-index --upgrade pip
(xxxx)[name@server ~]$ pip install --no-index snakemake==8.12.0
(xxxx)[name@server ~]$ pip install snakemake-executor-plugin-cluster-generic
(xxxx)[name@server ~]$ pip freeze --local &gt; requirements.txt
(xxxx)[name@server ~]$ deactivate
[name@server ~]$ rm -rf $ENVDIR
</code></pre>
<p>Ensuite créer un script :</p>
<pre><code>#!/bin/bash  
 
echo "Modules loading..."  
module load StdEnv/2023 gcc openmpi python/3.11 arrow/16.1.0 openmpi netcdf proj esmf geos mpi4py  
echo "Modules loaded successfully."  

virtualenv --no-download $SLURM_TMPDIR/env  
source $SLURM_TMPDIR/env/bin/activate  

pip install --no-index --upgrade pip  
pip install  --no-index -r requirements.txt  
echo "Environnment installé!"
</code></pre>
<p>Enfin,  dans le répertoire courant du fichier Snakefile,</p>
<pre><code>$ bash nomDeFichier.sh
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
<p>Toutefois, pour écrire le script de soumission associé à une règle snakemake, il faudra  soit directement l’écrire à la console:</p>
<pre><code>snakemake \
    --jobs 10 \ #nombre totale de jobs dans la liste de soumission
    --cluster '   # pour dire a snakemake de rouler la règle dans un cluster
      sbatch \    # choisir le gestionnaire de cluster slurm
        --mem 10G \
        --account ctb-frigon \
        --cpus-per-task 6\
        --time 02:00:00 \
</code></pre>
<p>soit créer un profile snakemake qui se chargera de soumettre les jobs en utilisants les options sbatch  souhaitées pour chaque règle.<br>
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
<p>Le parmètre <code>executor</code> permet de choisir un plugin pour soumettre des tâches à des systèmes de clusters. Pour les versions de snakemake supérieure à 8.0.0, c’est <code>cluster-generic</code> qu’il faut utiliser.</p>
<p><code>Cluster-generic</code>est un plugin générique qui donne accès à plusieurs types de plugin. Slurm est sélectionné via  <code>sbatch</code>. <code>resources.cpus</code> et <code>resources.mem</code> seront remplacé respectivement par “1.5G” et 10. Puisque maRegle n’a pas resources.time, c’est la valeur par défaut du fichier  <em><strong>config.v8+.yaml</strong></em> qui sera prise, 120. <code>--parsable</code> stocke le <strong>job ID</strong>.</p>
<p>Le paramètre  <code>cluster-generic-cancel-cmd</code> permet d’annuler  les jobs slurm lorsque le processus de snakemake est intérrompu.</p>
<p><strong>Remarque :</strong> si vous appuyez trop rapidement <strong>Ctrl-C</strong> une deuxième fois, Snakemake sera tué avant qu’il ne puisse terminer d’annuler tous les travaux avec <code>scancel</code>.</p>
<p>Le paramètre <code>cluster-generic-status-cmd: status-sacct.sh</code>  vérifie l’état des jobs soumis à slurm. Il est nécessaire surtout pour détecter les jobs qui échouent à cause du temps limite <code>--time</code> car par défaut Snakemake ne vérifie pas l’état <strong>TIMEOUT</strong>. <code>status-sacct.sh</code> est un  script parmi quatre autres proposé par <a href="https://github.com/jdblischak/smk-simple-slurm/tree/main/extras">snakemake</a>.<br>
Ces fichiers utilisent <code>sacct</code> ou <code>sacct</code>.<br>
<code>scontrol</code> ne montre que les informations sur les jobs en cours d’exécution ou qui sont récemment terminés (5 min) alors que <code>sacct</code> renvoie des informations de la base de données, et fonctionne donc pour tous les jobs.<br>
Le script de status doit être dans  le repertoire <strong>simple/</strong> et dois être éxécutable.</p>
<p><code>restart-times</code> reéxécute jusqu’à 3 fois la régle en cas d’échec.</p>
<p><strong>Attention:</strong> les jobs sont bien soumis au cluster si les informations de snakemake écrites à la console sont suivies de <code>Submitted job 28 with external jobid '32636155'.</code></p>
<h1 id="espo-on-snakemake-on-narval">ESPO on snakemake on narval</h1>
<p>Le workflow est stocké  dans le référentiel git  de la structure suivante :</p>
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
</code></pre>
<h3 id="snakefile">Snakefile</h3>
<p>Il faut obligatoirement avoir un fichier dans le répertoire courant, appelé <em><strong>Snakefile</strong></em> ou <em><strong>snakefile</strong></em> afin de pouvoir utiliser la commande <code>snakemake</code>. Pour des workflows ayant peu de règles, il n’est pas nécessaire d’avoir des fichiers <em>.smk</em>, toutes les règles peuvent être écrites dans le <em>Snakefile</em>. Cependant, la première règle qui doit être définie est la règle <strong>all</strong>.</p>
<p>Elle définit les fichiers cibles finaux que l’on souhaite obtenir à la fin du workflow. En d’autres termes, elle indique à Snakemake quels fichiers doivent être générés pour que le workflow soit considéré comme terminé.<br>
La règle all de ESPO-G est:</p>
<pre><code> rule all:  
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
<p>C’est aussi dans le <em><strong>Snakefile</strong></em>  qu’on associe le workflow à un fichier de <strong>configuration</strong>. Snakefile n’accepte qu’un seul fichier de configuration qu’on importe de la sorte:</p>
<pre><code>configfile: "config/config.yaml"
</code></pre>
<h3 id="config">Config</h3>
<p>Les fichiers de configuration sont utilisés à la fois par snakemake et par l’interpréteur python. Snakemake utilise  <code>config</code> exemple <code>config["custom"]["regions"]</code> et python utilise <code>xscen.CONFIG</code>.<br>
Le répertoire config/ contient:</p>
<ul>
<li><strong>config.yaml:</strong> fournie la plupart des arguments des fonctions utilisées dans les scripts</li>
<li><strong>off-properties_ESPO-G.yaml:</strong> fournie à <code>xs.properties_and_measures</code> présent dans les scripts des règles <em>off_diag_scen_prop_meas, off_diag_sim_prop_meas</em> et <em>off_diag_ref_prop</em>,  un chemin d’accès à un fichier YAML qui indique comment calculer les</li>
<li><strong>properties_ESPO-G.yaml:</strong> fournie à <code>xs.properties_and_measures</code> utilisé dans le script de la règle <em>DIAGNOSTICS</em> un chemin d’accès à un fichier YAML qui indique comment calculer les propriétés</li>
</ul>
<h3 id="simple">simple</h3>
<p>Le répertoire simple a deux fichier, le fichier <em><strong>config.v8+.yaml</strong></em> et <strong><code>status-sacct.sh</code></strong>. Comme discuté dans le chapitre Snakemake sur narval,  <em><strong>config.v8+.yaml</strong></em> est utiliser pour passer des paramètres à la commande <code>snakemake</code>. En plus des parametre donné en exemple dans le chapitre Snakemake sur narval, le profile de ESPO en  introduit d’autre pour</p>
<h3 id="workflow">workflow</h3>
<h3 id="section"></h3>
<h2 id="section-1"></h2>

