---


---

<h1 id="règles-snakemake">Règles snakemake</h1>
<p>Une règle snakemake doit avoir un output c’est-à-dire le fichier qu’on veut créer. La manière dont le fichier et son contenu sont générés est spécifié dans le script, run ou shell. S’il s’agit d’un script, le chemin vers le fichier du script est donné. La section input n’est pas obligatoire c’est le cas dans la règle <code>reference_DEFAULT</code> dans <code>Makeref.smk</code>où on utilise <code>xs.search_data_catalogs(**CONFIG['extraction']['reference']['search_data_catalogs'])</code>.</p>
<p>Dans d’autres règles où un <code>input</code>est nécessaire, on utilise pour la plupart <code>xr.open_zarr(snakemake.input[0])</code>si la règle ne possède qu’un seul fichier input ou bien <code>xr.open_zarr(snakemake.input)</code> si elle en possède plusieurs. On peut aussi avoir plusiueurs fichiers input, qu’on peut appeler chacun par leur nom, par exemple <code>xr.open_zarr(snakemake.input.south)</code>si on a:</p>
<pre><code>input:  
    middle=Path(config['paths']['final'])/"reference/ref_middle_nodup_default.zarr"  
    north=Path(config['paths']['final'])/"reference/ref_ north_nodup_default.zarr"  
    south=Path(config['paths']['final'])/"reference/ref_south_nodup_default.zarr"
</code></pre>
<p>Le répertoire <em>workflow</em> contient des fichiers <em>.smk</em> qui sont des ensembles de règles regroupées par tâches. C’est-à-dire que chaque tâche dans <code>tasks</code>de <em>config.yaml</em>, a son fichier <em>.smk</em>.<br>
Dans un fichier <em>.smk</em> l’ordre d’exécution des règles est dicté par les fichiers <code>input</code>. Par exemple dans <em>Makeref.smk</em>, la règle <code>reference_DEFAULT</code> est exécutée en premier, car elle sert d’input pour le reste des règles présent dans ce fichier y compris la règle <code>concat_diag_ref_prop</code>qui a comme input, le output de la règle <code>diagnostics</code>, qui dépend lui même de <code>reference_DEFAULT</code>. On aurait pu utiliser <code>ruleorder</code>pour imposer un ordre d’exécution des règles <code>reference_NOLEAP, reference_360_DAY et diagnostics</code>puisqu’elles sont indépendantes les unes les autres, mais cela n’est pas nécessaire dans ce cas-ci.</p>
<h1 id="wildcards">wildcards</h1>
<p>Les wildcards sont utilisés pour alléger le code et automatiser la notation des fichiers. En effets, au lieu de boucler sur les régions on utilise les wildcards dans les fichiers input et output. Les fichiers input ne doivent pas contenir des wildcards qui ne sont pas présents dans le output, alors que les fichiers log et benchmark doivent avoir exactement les mêmes wildcards que les fichiers output. La valeur des wildcards ne doit être spécifiée que lors de l’exécution du workflow, soit dans la règle <code>all</code>, où toutes les valeurs possibles du wildcards sont passées à la fonction <code>expand()</code>, soit avec la commande <code>snakemake --cores</code> à qui on donne le nombre de cores souhaités et le fichier qu’on veut généré.</p>
<p>Exemple pour générer tous les fichiers output de la règle <code>reference_DEFAULT</code>, on utilise la règle <code>all</code> avec comme input <code>expand(Path(config['paths']['final'])/"reference/ref_{region}_default.zarr", region=list(config["custom"]["regions"].keys())</code>la fonction expand se charge de générer tous les chemins en remplaçant le wildcards region par ses valeurs. Donc pour les régions middle_nodup, north_nodup et south_nodup, c’est comme si on avait</p>
<pre><code>rule all:  
input:  
Path(config['paths']['final'])/"reference/ref_middle_nodup_default.zarr"  
Path(config['paths']['final'])/"reference/ref_ north_nodup_default.zarr"  
Path(config['paths']['final'])/"reference/ref_south_nodup_default.zarr"
</code></pre>
<p>Pour chaque fichier input, le script associé à <code>reference_DEFAULT</code> est exécuté et toutes les variables snakemake.wildcards.region sont sont remplacées par la  actuelle du wildcard <code>region</code> .</p>
<p>Pour générer un fichier en particulier, exemple, <code>Path(config['paths'['final'])/"reference/ref_{region}_default.zarr"</code> pour middle_nodup, on exécute la commande: <code>snakemake --cores 10 /jarre/scenario/ocisse/ESPO-G6-stage/reference/ref_middle_nodup_default.zarr/</code></p>
<p>Plusieurs wildcards dans un même nom de fichier peuvent provoquer une ambiguïté. Considérez le modèle <code>Path(config['paths']['exec_workdir'])/"ESPO-G_workdir/{sim_id}_{region}_extracted.zarr"</code> dans le fichier <em>extract.smk</em> et supposez qu’un fichier <em>CMIP6_ScenarioMIP_AS-RCEC_TaiESM1_ssp585_r1i1p1f1_global_middle_nodup_extracted.zarr</em> est disponible. Il n’est pas clair si <code>sim_id=CMIP6_ScenarioMIP_AS-RCEC_TaiESM1</code> et <code>region=ssp585_r1i1p1f1_global_middle_nodup</code> ou <code>sim_id=CMIP6_ScenarioMIP_AS-RCEC_TaiESM1_ssp585_r1i1p1f1_global</code> et <code>region=middle_nodup</code> dans ce cas.<br>
C’est pourquoi une contrainte a été ajoutée à la wildcards region pour qu’il soit composé de deux chaînes de caractères séparées par un tiret du bas. Le wildcards sim_id est aussi contraint à avoir minimum 6 underscords.</p>
<h1 id="workflow-espo-g">Workflow ESPO-G</h1>
<p><img src="%5BImgur%5D(https://imgur.com/Bl5QVUe)" alt="Graphe acyclique dirigé"><br>
L’image au-dessus montre les dépendances des différents fichiers générés par le workflow pour atteindre son objectif (la règle all) qui est la création des fichiers:<code>expand(Path(config['paths']['exec_workdir']) / "ESPO-G_workdir/diag-improved_{sim_id}_{dom_name}.zarr", sim_id=sim_id_name,dom_name=dom)</code> de la règle <em>diag_measures_improvement</em> dans <em>official_diagnostics.smk</em> .<br>
C’est le cas de la <code>diag_improved_et_heatmap</code> dans <em>DIAGNOSTICS.smk</em>. Le graphe acyclique dirigé peut être obtenu avec la commande <code>snakemake --dag --all | dot -Tpng &gt; nom_du_fichier.png</code>, on peut aussi remplacer l’extension .png, par .svg ou .pdf.<br>
Tous les fichiers output du workflow ne sont pas présents. En effet certaines règles génèrent des  fichiers qui ne sont le input d’aucune autre règle. on peut changer les input de la règle all pour générer les fichiers manquants ou les appeler explicitement avec la commande <code>snakemake --cores N chemin/vers/le_fichier.zarr</code>.<br>
L’image ci-dessous montre le graphe acyclique dirigé pour la règle all ayant comme input, le output de la règle <code>diag_improved_et_heatmap</code> se trouvant dans le fichier <em>DIAGNOSTICS.smk</em>.</p>
<p><img src="https://1drv.ms/i/c/92521c06258a78c6/EUNN8VGLukxKnwAA3dgTGtcBgqk0eQRcwb9Rc-nrN-bErA?e=wVTvXx" alt="Graphe acyclique dirigé de la règle diag_improved_et_heatmap"></p>

