from rush import build_blocking_provider
import os

API_TOKEN = os.getenv("BIOHACK_ACCESS_TOKEN")

client = build_blocking_provider(access_token=API_TOKEN)

benchmark = client.benchmark(name="OpenFF Protein-Ligand Binding Benchmark")

rex_code = r"""
let
    auto3d = \smi -> map to_data (get 0 (auto3d_rex_s default_runspec_gpu { k = 1 } [smi])),

    p2rank = \prot_conf -> p2rank_rex_s default_runspec {} prot_conf,

    gnina = \prot_conf -> \bounding_box -> \smol_conf ->
        get 0 (get 0 (gnina_rex_s default_runspec_gpu {} [prot_conf] [bounding_box] smol_conf [])),

in
\input ->
    let
        protein = load (id (get 0 input)) "ProteinConformer",
        smol_id = id (get 1 input),
        smiles = smi (load smol_id "Smol"),

        structure = load (structure_id protein) "Structure",
        trc = [
            topology structure,
            residues structure,
            chains structure
        ],

        bounding_box = get 0 (get 0 (p2rank trc)),

        smol_structure = auto3d smiles,

        docked_structure = gnina trc bounding_box [smol_structure],

        min_affinity = list_min (map (get "affinity") (get "scores" docked_structure)),

        binding_affinity = BindingAffinity {
            affinity = min_affinity,
            affinity_metric = "kcal/mol",
            protein_id = protein_id protein,
            smol_id = smol_id,
            metadata = Metadata {
                name = "binding affinity for smol and protein",
                description = none,
                tags = []
            }
        }
    in
        [BenchmarkArg {
            entity = "BindingAffinity",
            id = save binding_affinity
        }]
"""