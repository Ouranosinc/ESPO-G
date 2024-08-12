---


---

<h1 id="snakemake">Snakemake</h1>
<p>Snakemake est un outil inspiré de GNU Make, mais conçu pour être plus flexible et puissant. Il utilise une syntaxe basée sur Python pour définir des règles qui spécifient comment générer des fichiers de sortie à partir de fichiers d’entrée. Pour consulter la documentation officielle vous pouvez cliquer sur ce <a href="https://snakemake.readthedocs.io/en/stable/snakefiles/rules.html">lien</a>.<br>
Les workflows sont définis en termes de règles. Chaque règle spécifie comment créer un fichier de sortie à partir d’un ou plusieurs fichiers d’entrée. Voici un exemple de règle :</p>
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
<p>Une règle snakemake doit avoir un output c’est-à-dire le fichier qu’on veut créer. La manière dont le fichier et son contenu sont générés est spécifié dans le script, run ou shell. S’il s’agit d’un script, le chemin vers le fichier du script est donné comme dans l’exemple précédent. Dans le script on peut utiliser les paramètres de snakemake par exemple on utilise <code>snakemake.input</code>si la règle ne possède qu’un seul fichier input ou bien  <code>snakemake.input[0]</code>  si elle possède une liste de fichiers input. On peut aussi appeler chaque fichier input par un nom, par exemple  <code>snakemake.input.south</code>si on a:</p>
<pre><code>input:  
    middle=Path(config['paths']['final'])/"reference/ref_middle_nodup_default.zarr"  
    north=Path(config['paths']['final'])/"reference/ref_ north_nodup_default.zarr"  
    south=Path(config['paths']['final'])/"reference/ref_south_nodup_default.zarr"
</code></pre>
<p>La section input n’est pas obligatoire c’est le cas dans la règle <code>reference_DEFAULT</code> dans <code>Makeref.smk</code>. Dans la règle ci-haut j’utilise la section <code>params</code> pour passer des valeurs aux paramètres de dask.distributed.LocalCluster et qu’elles soient en adéquation avec les ressources demandées à slurm. À l’execption de <code>n_workers</code> qui est dans ressources par soucis de portabilité. En effet pour que <code>mem</code> soit exactement égale à <code>memory_limit</code>, j’utilise la fonction <code>lambda</code> qui ne peut pas prendre comme paramètre <code>params</code> . Donc le client sera appelé de la façon suivante dans le script <em>load_default_ref.py</em>:</p>
<pre><code>cluster = LocalCluster(n_workers=snakemake.resources.n_workers, threads_per_worker=snakemake.params.threads_per_worker,  
                       memory_limit=snakemake.params.memory_limit, **daskkws)  
client = Client(cluster)
</code></pre>
<p>La section <code>resources</code> est utilisée pour déterminer quelles tâches peuvent être exécutées en même temps sans dépasser les limites spécifiées sur la ligne de commande. C’est-à-dire que Snakemake ne vérifie pas la consommation de ressources des tâches en temps réel. Ainsi les variables de resources seront utiliser dans le script de soumission slurm à l’exception de <code>n_workers</code>. L’appel à <code>sbatch</code> ressemblera à:</p>
<pre><code>sbatch  
  --partition=c-frigon  
  --account=ctb-frigon  
  --constraint=genoa  
  --cpus-per-task={resources.cpus_per_task}  
  --qos={resources.qos}  
  --mem={resources.mem}  
  --job-name={rule}-{wildcards}  
  --output=s_logs/{rule}/{rule}-{wildcards}-%j.out  
  --time={resources.time}  
  --parsable
</code></pre>
<p>Le répertoire <em>workflow</em> contient des fichiers <em>.smk</em> qui sont des ensembles de règles regroupées par tâches. C’est-à-dire que chaque tâche dans <code>tasks</code>de <em>config.yaml</em>, a son fichier <em>.smk</em>.<br>
Dans un fichier <em>.smk</em> l’ordre d’exécution des règles est dicté par les fichiers <code>input</code>. Par exemple dans <em>Makeref.smk</em>, la règle <code>reference_DEFAULT</code> est exécutée en premier, car elle sert d’input pour le reste des règles présent dans ce fichier y compris la règle <code>concat_diag_ref_prop</code>qui a comme input, le output de la règle <code>diagnostics</code>, qui dépend lui même de <code>reference_DEFAULT</code>. On aurait pu utiliser <code>ruleorder</code>pour imposer un ordre d’exécution des règles <code>reference_NOLEAP, reference_360_DAY et diagnostics</code>puisqu’elles sont indépendantes les unes les autres, mais cela n’est pas nécessaire dans ce cas-ci.</p>
<h2 id="snakefile-et-règle-all">Snakefile et règle all</h2>
<p>Le fichier  <em><strong>Snakefile</strong></em>  est essentiel dans Snakemake. Il faut obligatoirement avoir un fichier dans le rpertoire courant, applé <em><strong>Snakefile</strong></em> ou <em><strong>snakefile</strong></em> afin  de pouvoir utiliser la commande <code>snakemake</code>. Pour des workflow ayant peu de règles, il n’est pas nécessaire d’avoir des fichiers <em>.smk</em>, toutes les règles peuvent être écrites dans le  <em>Snakefile</em>. Cependant, la première règle qui doit être définie est la règle <strong>all</strong>.</p>
<p>La règle  <strong>all</strong>  est souvent utilisée pour définir les fichiers cibles finaux que l’on souhaite obtenir à la fin du workflow.  En d’autres termes, elle indique à Snakemake quels fichiers doivent être générés pour que le workflow soit considéré comme terminé.<br>
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
<p>La fonction <code>expand()</code> génère une liste de fichiers avec tous les wildcards résolus. Exemple les wildcards sample=[A, B] et num=[1, 2], la sortie de</p>
<pre><code>expand("échantillon{sample}.{num}", sample=[A, B],  num=[1, 2])
</code></pre>
<p>sera</p>
<pre><code>["échantillonA.1", "échantillonA.2", "échantillonB.1", "échantillonB.2"]
</code></pre>
<p>Il est aussi possible de résoudre seulement le wildcards {sample} en faisant:</p>
<pre><code>expand("échantillon{sample}.{{num}}", sample=[A, B])
</code></pre>
<p>qui aura comme sortie:</p>
<pre><code>["échantillonA.{num}", "échantillonA.{num}"]
</code></pre>
<p>Pour utiliser des fichiers <em>.smk</em> il faut les inclure dan le <em><strong>Snakefile</strong></em> de cette façon:</p>
<pre><code>include: "workflow/rules/common.smk
</code></pre>
<p>C’est aussi dans le <em><strong>Snakefile</strong></em>  qu’on associe le workflow à un fichier de <strong>configuration</strong>. Snakefile n’accepte qu’un seul fichier de configuration qu’on importe de la sorte:</p>
<pre><code>configfile: "config/config.yaml"
</code></pre>
<p>Il faut utiliser les paramètres du fichier config.yaml avec l’outil <code>config</code> de snakemake, exemple <code>config["custom"]["regions"]</code>.</p>
<p>On peut contraindre snakemake à utiliser une version minimale en ajoutant dans le Snakefile:</p>
<pre><code>from snakemake.utils import min_version  
 
##### set minimum snakemake version #####  
min_version("8.12.0")
</code></pre>
<h2 id="arborescence-des-fichiers">Arborescence des fichiers</h2>
<p>Le workflow est stocké  dans le référentiel git  de la structure suivante :</p>
<pre><code>├── config
│   ├── config.yaml
|   ├── off-properties_ESPO-G.yaml
|   ├── portraits.yaml
|   └── properties_ESPO-G.yaml
├── workflow
│   ├── rules
|   │   ├── module1.smk
|   │   └── module2.smk
│   ├── scripts
|   │   ├── script1.py
|   │   └── script2.py
├── .gitignore
├── Snakefile
├── dag.png
├── README.md
</code></pre>
<h2 id="wildcards">Wildcards</h2>
<p>Les wildcards sont utilisés pour alléger le code et automatiser la notation des fichiers. En effets, au lieu de boucler sur les régions on utilise les wildcards dans les fichiers input et output. Les fichiers input ne doivent pas contenir des wildcards qui ne sont pas présents dans le output, alors que les fichiers log et benchmark doivent avoir exactement les mêmes wildcards que les fichiers output. La valeur des wildcards ne doit être spécifiée que lors de l’exécution du workflow, soit dans la règle  <code>all</code>, où toutes les valeurs possibles du wildcards sont passées à la fonction  <code>expand()</code>, soit avec la commande  <code>snakemake --cores</code>  à qui on donne le nombre de cores souhaités et le fichier qu’on veut généré.<br>
Exemple pour générer tous les fichiers output de la règle  <code>reference_DEFAULT</code>, on utilise la règle  <code>all</code>  avec comme input:</p>
<pre><code>expand(Path(config['paths']['final'])/"reference/ref_{region}_default.zarr", region=list(config["custom"]["regions"].keys())
</code></pre>
<p>La fonction expand() se charge de générer tous les chemins en remplaçant le wildcards <code>region</code> par ses valeurs. Donc pour les régions middle_nodup, north_nodup et south_nodup, c’est comme si on avait</p>
<pre><code>rule all:  
input:  
Path(config['paths']['final'])/"reference/ref_middle_nodup_default.zarr"  
Path(config['paths']['final'])/"reference/ref_ north_nodup_default.zarr"  
Path(config['paths']['final'])/"reference/ref_south_nodup_default.zarr"

</code></pre>
<p>Pour chaque fichier input, le script associé à  <code>reference_DEFAULT</code>  est exécuté et toutes les variables snakemake.wildcards.region présentes dans le script sont remplacées par la valeur actuelle du wildcard  <code>region</code> .</p>
<p>Pour générer un fichier en particulier, exemple: <code>Path(config['paths'['final'])/"reference/ref_{region}_default.zarr"</code>  pour <code>middle_nodup</code>, on exécute la commande:</p>
<pre><code>$ snakemake --cores 10 /project/ctb-frigon/oumou/ESPO-G6-stage/reference/ref_middle_nodup_default.zarr/
</code></pre>
<p>Lors de l’exécution de la commande  <code>snakemake --cores N all</code>  ou  <code>snakemake --cores N chemin/vers/le_fichiers_désiré.zarr</code>, Snakemake détermine automatiquement les dépendances entre les règles en faisant correspondre les noms de fichiers. C’est à dire pour</p>
<pre><code>rule all:
    input:
        expand(Path(config['paths']['exec_workdir']) / "ESPO-G_workdir/diag-improved_{sim_id}_{dom_name}.zarr", sim_id=sim_id_name,dom_name=dom)

</code></pre>
<p>snakemake va écrire tous les fichiers possibles en remplaçant toutes les valeurs de <code>sim_id</code> et <code>dome_name</code>. Il va ensuite chercher la règle qui a comme output  <code>Path(config['paths']['exec_workdir']) / "ESPO-G_workdir/diag-improved_{sim_id}_{dom_name}.zarr"</code>  afin de voir les dépendance (les fichiers input).<br>
<strong>Attention:</strong> la commande <code>snakemake --cores</code> bne soumet pas des jobs à un cluster. Elle exécute les règles localement. Pour soumettre les règles à un cluster il faut utiliser l’argument <code>cluster-generic-submit-cmd</code> qui sera discuté dans le prochain chapitre.</p>
<p>Ici la règle est</p>
<pre><code>rule diag_measures_improvement:
    input:
        sim=Path(config['paths']['exec_workdir']) / "ESPO-G_workdir/off-diag-sim-meas_{sim_id}_{dom_name}.zarr",
        scen=Path(config['paths']['exec_workdir']) / "ESPO-G_workdir/off-diag-scen-meas_{sim_id}_{dom_name}.zarr"
    output:
        directory(Path(config['paths']['exec_workdir']) / "ESPO-G_workdir/diag-improved_{sim_id}_{dom_name}.zarr")
    log:
        "logs/diag_measures_improvement_sim_{sim_id}_{dom_name}"
    wildcard_constraints:
        sim_id = "([^_]*_){6}[^_]*"
    script:
        f"{home}workflow/scripts/diag_measures_improvement.py"

</code></pre>
<p>Et pour chacun des fichiers retournés par  <code>expand()</code>, snakemake va remplacer la valeur de <code>sim_id</code> et <code>dom_name</code> dans les fichiers input.</p>
<p>Pour <code>sim_id = id1</code> et <code>dom_name= NAM</code>, on aura:</p>
<pre><code>sim=Path(config['paths']['exec_workdir']) / "ESPO-G_workdir/off-diag-sim-meas_id1_NAM.zarr",
scen=Path(config['paths']['exec_workdir']) / "ESPO-G_workdir/off-diag-scen-meas_id1_NAM.zarr"

</code></pre>
<p>De même, snakemake recherchera par la suite les règles qui génèrent</p>
<pre><code>Path(config['paths']['exec_workdir']) / "ESPO-G_workdir/off-diag-sim-meas_id1_NAM.zarr" 
</code></pre>
<p>et</p>
<pre><code> Path(config['paths']['exec_workdir']) / "ESPO-G_workdir/off-diag-scen-meas_id1_NAM.zarr"
</code></pre>
<p>remplace ses wildcards <code>sim_id</code> et <code>dom_name</code> par <code>id1</code> et <code>NAM</code> respectivement. Si les fichiers n’existent pas encore, snakemake fera la même chose jusqu’à touver un fichiers dépendant qui existent. Une fois un fichiers dépendant trouvé, snakemake fera le sens inverse vers le fichier</p>
<pre><code> Path(config['paths']['exec_workdir']) / "ESPO-G_workdir/diag-improved_id1_NAM.zarr"  
</code></pre>
<p>en exécutant le script associé aux règles des fichiers dépendants afin de créer ces derniers.</p>
<p>Plusieurs wildcards dans un même nom de fichier peuvent provoquer une ambiguïté. Considérez le nom fichier suivant:</p>
<pre><code>Path(config['paths']['exec_workdir'])/"ESPO-G_workdir/{sim_id}_{region}_extracted.zarr"  
</code></pre>
<p>dans la règle   <em>extract</em>  et supposez qu’un fichier  <em>CMIP6_ScenarioMIP_AS-RCEC_TaiESM1_ssp585_r1i1p1f1_global_middle_nodup_extracted.zarr</em>  est disponible. Il n’est pas clair si  <code>sim_id=CMIP6_ScenarioMIP_AS-RCEC_TaiESM1</code>  et  <code>region=ssp585_r1i1p1f1_global_middle_nodup</code>  ou  <code>sim_id=CMIP6_ScenarioMIP_AS-RCEC_TaiESM1_ssp585_r1i1p1f1_global</code>  et  <code>region=middle_nodup</code>  dans ce cas.<br>
C’est pourquoi une contrainte a été ajoutée à la wildcards <code>region</code> pour qu’il soit composé de deux chaînes de caractères séparées par un tiret du bas. Le wildcards sim_id est aussi contraint à avoir minimum 6 underscords.</p>
<h2 id="common.smk">Common.smk</h2>
<p>Le fichier <em>common.smk</em> permet de définir des fonctions qui seront utiliser par les autres fichiers .smk ce qui permet de ne pas trop les surcharger avec du code. C’est pour dans cette règle ci dessous la fonction <code>official_diags_inputfiles_ref</code> est directement appelée.</p>
<pre><code>rule off_diag_ref_prop:  
    input:  
        ref=official_diags_inputfiles_ref  
    output:  
        prop=temp(directory(Path(config['paths']['exec_workdir']) / "ESPO-G_workdir/off-diag-ref-prop_{sim_id}_{dom_name}.zarr"))  
    params:  
        threads_per_worker= lambda wildcards,threads, resources: int(resources.cpus_per_task / resources.n_workers),  
        memory_limit=lambda wildcards, resources: int(resources.mem.rstrip("GB")) / resources.n_workers   
  resources:  
        mem='30GB',  
        n_workers=3, 
        cpus_per_task=6, 
        time=60  
  wildcard_constraints:  
        sim_id = "([^_]*_){6}[^_]*"  
  script:  
        f"{home}workflow/scripts/off_diag_ref_prop.py"
</code></pre>
<p>et la d’efinition de la fonction dans <em>common.smk</em> est la suivante:</p>
<pre><code>def official_diags_inputfiles_ref(wildcards):  
    step_dict=config['off-diag']['steps']["ref"]  
    ref=Path(config['paths']['final'])/f"reference/ref_{step_dict['domain'][wildcards.dom_name]}_default.zarr"  
    return ref
</code></pre>
<p>Il faut noter l’argument <code>wildcards</code> de <code>official_diags_inputfiles_ref</code> qui est présent car la fonction fait appel aux wildcards de la règle dans laquelle elle est appelée.</p>
<h2 id="graphe-acyclique-dirigé">Graphe acyclique dirigé</h2>
<p>Snakemake construit automatiquement un graphe acyclique dirigé (DAG) des tâches à partir des dépendances entre les règles. Cela permet de paralléliser les tâches et d’optimiser l’exécution. Le DAG associé à ESPO-G est la suivante:</p>
<h1 id="création-denvironment">Création d’environment</h1>
<p>Puisque <code>conda</code> n’est pas utilisé sur narval on ne peut pas utiliser le paramètre <code>conda</code> de snakemake dans les règles. Donc il n’est pas possible de créer un environment pour chaque règles via <code>conda</code>. Il faut ainsi créer l’environment pour snakemake une seule fois en effectuant les étapes suivantes:</p>
<pre><code>[name@server ~]$ module load StdEnv/2023 gcc openmpi python/3.11 arrow/16.1.0 openmpi netcdf proj esmf geos mpi4py 
[name@server ~]$ ENVDIR=/tmp/$RANDOM
[name@server ~]$ virtualenv --no-download $ENVDIR
[name@server ~]$ source $ENVDIR/bin/activate
(xxxx)[name@server ~]$ pip install --no-index --upgrade pip
(xxxx)[name@server ~]$ pip install --no-index snakemake==8.12.0
(xxxx)[name@server ~]$ pip freeze --local &gt; requirements.txt
(xxxx)[name@server ~]$ deactivate
[name@server ~]$ rm -rf $ENVDIR
</code></pre>
<p>Cela produira un fichier appelé requirements.txt, avec comme contenu:</p>
<pre><code>appdirs==1.4.4+computecanada
argparse_dataclass==2.0.0+computecanada
attrs==23.2.0+computecanada
charset_normalizer==3.2.0+computecanada
conda_inject==1.3.2+computecanada
ConfigArgParse==1.7+computecanada
connection_pool==0.0.3+computecanada
datrie==0.8.2+computecanada
docutils==0.21.2+computecanada
dpath==2.2.0+computecanada
fastjsonschema==2.20.0+computecanada
gitdb==4.0.11+computecanada
GitPython==3.1.43+computecanada
humanfriendly==10.0+computecanada
idna==3.4+computecanada
immutables==0.20+computecanada
jinja2==3.1.4+computecanada
jsonschema==4.23.0+computecanada
jsonschema_specifications==2023.12.1+computecanada
MarkupSafe==2.1.5+computecanada
nbformat==5.10.4+computecanada
plac==1.4.3+computecanada
PuLP==2.8.0+computecanada
PyYAML==6.0.1+computecanada
referencing==0.35.1+computecanada
requests==2.31.0+computecanada
reretry==0.11.8+computecanada
rpds_py==0.18.1+computecanada
smart_open==7.0.4+computecanada
smmap==5.0.1+computecanada
snakemake==8.12.0+computecanada
snakemake_interface_common==1.17.2+computecanada
snakemake_interface_executor_plugins==9.2.0+computecanada
snakemake_interface_report_plugins==1.0.0+computecanada
snakemake_interface_storage_plugins==3.2.3+computecanada
stopit==1.1.2+computecanada
tabulate==0.9.0+computecanada
throttler==1.2.2+computecanada
toposort==1.10+computecanada
urllib3==2.1.0+computecanada
wrapt==1.16.0+computecanada
yte==1.5.4+computecanada
</code></pre>
<p>Ensuite,  dans le répertoire courant du fichier Snakefile,</p>
<h1 id="le-profile-de-snakemake">Le profile de snakemake</h1>
<p>La documentation complète peut-être consulter sur ce  <a href="https://github.com/jdblischak/smk-simple-slurm/tree/main">lien</a>.  Pour éxecuter un workflow snakemake dans un cluster, on utilise la commande</p>
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
<p>Pour plus de détail sur l’utilisation de la mémoire et des threads des jobs en temps réelle on peut consulter cette  <a href="https://portail.narval.calculquebec.ca/">page</a>.<br>
Lorsqu’on annule une job slurm associée à une règle snakemake, la règle échoue aussi. Par contre, si c’est le processus Snakemake qui est annuler avec <code>ctrl + c</code> les jobs slurm associés doivent être annulées séparement avec la commande:</p>
<pre><code>$ scancel &lt;JOBID&gt;
</code></pre>
<p>ou</p>
<pre><code>$ scancel -u &lt;USERNAME&gt;
</code></pre>
<p>Pour annuler tous les jobs soumis par l’utilisateur USERNAME.<br>
Pour annuler automatiquement tous les travaux en cours d’exécution lorsque vous annulez le processus principal de Snakemake (c’est-à-dire le comportement par défaut de --drmaa), vous pouvez spécifier <code>cluster-generic-cancel-cmd : scancel</code> dans <em>config.v8+.yaml</em> . De la même manière que pour --cluster-generic-status-cmd, vous devez inclure l’indicateur --parsable à la commande sbatch passée à --cluster-generic-cancel-cmd afin de transmettre l’ID de tâche à scancel.<br>
<strong>Remarque :</strong> N’appuyez qu’une seule fois sur Ctrl-C. Si vous appuyez trop rapidement une deuxième fois, Snakemake sera tué avant qu’il ne puisse terminer d’annuler tous les travaux avec scancel.</p>
<h1 id="arborescence-des-fichiers-1">Arborescence des fichiers</h1>
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

