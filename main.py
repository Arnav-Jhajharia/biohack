import asyncio
import json
import os

from rush import build_blocking_provider
from rush.graphql_client import CreateRun

from rush_fetch import benchmark_submission
from rush_mutate import benchmark_mutation

API_TOKEN = os.getenv("BIOHACK_ACCESS_TOKEN")
rex_fn = r"""
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

client = build_blocking_provider(access_token=API_TOKEN)
benchmark = client.benchmark(name="OpenFF Protein-Ligand Binding Benchmark")
async def main():
    input_ = CreateRun(rex=rex_fn,name="name", project_id=client.project_id)
    # response = await benchmark_mutation(input_,benchmark.id,0.02,False,API_TOKEN)
    # the actual ID is set under response.source_run
    response = await benchmark_submission("b11071e7-4662-4a0f-8579-815febd1f514", "0d2723d5-674e-430c-90be-7784d068247f", auth_token=API_TOKEN)
    print(json.dumps(response, indent=1))  # Print the API response


if __name__ == "__main__":
    asyncio.run(main())

