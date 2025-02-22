import asyncio
import json
import os

from openai import OpenAI
from rush import build_blocking_provider
from rush.graphql_client import CreateRun

from rush_api_interactions.rush_fetch import benchmark_submission
from rush_api_interactions.rush_mutate import benchmark_mutation

RUSH_API_TOKEN = os.getenv("BIOHACK_ACCESS_TOKEN")
DS_API_TOKEN = os.getenv("DS_API_TOKEN")
rex_fn = r"""
let
    cust_runspec = RunSpec{
        target = 'Bullet',
        resources = Resources{
            storage = some 10,
            storage_units = some "MB",
            gpus = some 1
        }
    },
    prepare_protein = \protein_conformer_trc ->
        get 0 (
            prepare_protein_rex_s default_runspec { ph = some 7.4 , truncation_threshold= some 1, naming_scheme = none, capping_style = some "Never"} protein_conformer_trc
        ),
    auto3d = \smi -> map to_data (get 0 (auto3d_rex_s cust_runspec { k = 5, optimizing_engine= "AIMNET", window=2.5, max_confs=15, enumerate_isomer=true, opt_steps=4000, patience=750, threshold=0.6, convergence_threshold =0.002, verbose=true,capacity=30} [smi])),
    p2rank = \prot_conf -> p2rank_rex_s default_runspec {} prot_conf,
    gnina = \prot_conf -> \bounding_box -> \smol_conf ->
        get 0 (get 0 (gnina_rex_s default_runspec_gpu {exhaustiveness=32, num_modes=30, minimize=true} [prot_conf] [bounding_box] smol_conf []))
in
    \input ->
        let
            protein =   load (id (get 0 input)) "ProteinConformer",
            smol_id =  id (get 1 input),
            smiles = smi (load smol_id "Smol"),
            structure = load (structure_id protein) "Structure",
            pp_trc = [(topology structure, residues structure, chains structure)],
            trc =  [topology structure, residues structure, chains structure],
            bounding_box = get 0 (get 0 (p2rank trc)),
            smol_structure = auto3d smiles,
            prepared_protein = prepare_protein pp_trc,
            docked_structure = gnina prepared_protein bounding_box [smol_structure],
            min_affinity = list_min (map (get "affinity") (get "scores" docked_structure)),
            binding_affinity = BindingAffinity {
                affinity = min_affinity,
                affinity_metric = "kcal/mol",
                protein_id = protein_id protein,
                smol_id = smol_id,
                metadata = Metadata {
                    name = "Protein Binding Affinity",
                    description = none,
                    tags = []
                }
            }
        in
            [BenchmarkArg { entity = "BindingAffinity", id = save binding_affinity }]
"""

rush_client = build_blocking_provider(access_token=RUSH_API_TOKEN)
benchmark = rush_client.benchmark(name="OpenFF Protein-Ligand Binding Benchmark")

async def benchmark_workflow(rex, name, sample_pct, with_outs, wait_for_result=True):
    """
    Initiates a simple benchmark workflow for the Rush API.

    Parameters:
        rex (str): The rex function to send
        name (str): Name of the function
        sample_pct (float): the % of the sample to run the benchmark on
        with_outs (bool): withouts from the benchmark_mutation
        wait_for_result (bool): Whether to fetch the result of the benchmark or not. If not, then only the response containing run_benchmark_id and source_run_id is returned.
    """


    input_ = CreateRun(rex=rex, name=name, project_id = rush_client.project_id)
    print("✅ Requesting to run Benchmark")
    response = await benchmark_mutation(input_, benchmark.id, sample_pct=sample_pct, with_outs=with_outs, auth_token= RUSH_API_TOKEN)
    if response is not None :
        print(f"🚀 Running benchmark with submission ID: {response.data['run_benchmark']['id']} \t source submission ID: {response.data['run_benchmark']['source_run']['id']}")
        if wait_for_result :
            res = (rush_client.poll_run_blocking(response.data['run_benchmark']['source_run']['id'])).status
            if res == "DONE":
                await asyncio.sleep(180)
                return await benchmark_submission(response.data['run_benchmark']['id'], rush_client.project_id, RUSH_API_TOKEN)
        else:
            return response.data
    else :
        return response

async def main():
    res = await benchmark_workflow(rex=rex_fn, name="Benchmark Workflow training #12", sample_pct=0.03, with_outs=False)
    print(json.dumps(res, indent=1))



if __name__ == "__main__":
    asyncio.run(main())

