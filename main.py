import asyncio
import json
import os


from rush import build_blocking_provider
from rush.graphql_client import CreateRun

from PythonProject.rush_fetch import benchmark_submission
from rush_mutate import benchmark_mutation

API_TOKEN = os.getenv("BIOHACK_ACCESS_TOKEN")

rex_fn = r"""
let
    auto3d = \smi -> map to_data (get 0 (auto3d_rex_s default_runspec_gpu { k = 1 } [smi])),
    p2rank = \prot_conf -> p2rank_rex_s default_runspec {} prot_conf,
    gnina = \prot_conf -> \bounding_box -> \smol_conf ->
        get 0 (get 0 (gnina_rex_s default_runspec_gpu {} [prot_conf] [bounding_box] smol_conf []))
in
    \input ->
        let
            protein = load (id (get 0 input)) "ProteinConformer",
            smol_id = id (get 1 input),
            smiles = smi (load smol_id "Smol"),
            structure = load (structure_id protein) "Structure",
            trc = [topology structure, residues structure, chains structure],
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
                    name = "Protein Binding Affinity",
                    description = none,
                    tags = []
                }
            }
        in
            [BenchmarkArg { entity = "BindingAffinity", id = save binding_affinity }]
"""

client = build_blocking_provider(access_token=API_TOKEN)
benchmark = client.benchmark(name="OpenFF Protein-Ligand Binding Benchmark")

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


    input_ = CreateRun(rex=rex, name=name, project_id = client.project_id)
    print("✅ Requesting to run Benchmark")
    response = await benchmark_mutation(input_, benchmark.id, sample_pct=sample_pct, with_outs=with_outs, auth_token= API_TOKEN)
    print(f"🚀 Running benchmark with submission ID: {response.data['run_benchmark']['id']} \t source submission ID: {response.data['run_benchmark']['source_run']['id']}")
    if wait_for_result :
        res = (client.poll_run_blocking(response.data['run_benchmark']['source_run']['id'])).status
        if res == "DONE":
            return await benchmark_submission(response.data['run_benchmark']['id'], client.project_id, API_TOKEN)
    else:
        return response.data

async def main():
    res = await benchmark_workflow(rex=rex_fn, name="Benchmark Workflow Submission from Adi's Computer", sample_pct=0.01, with_outs=False)
    print(json.dumps(res, indent=1))

options={
    "auto3d": {
    "k": {
        "type": "int",
        "default": None,
        "description": "Output top k structures for each molecule.",
        "bounds": (1, None)  # Must be at least 1 if provided
    },
    "window": {
        "type": "float",
        "default": None,
        "description": "Outputs structures whose energies are within X kcal/mol from the lowest energy conformer.",
        "bounds": (0, None)  # Should be non-negative
    },
    "max_confs": {
        "type": "int",
        "default": None,
        "description": "Maximum number of isomers per SMILES. Defaults to (heavy_atoms - 1).",
        "bounds": (1, None)  # At least 1 isomer
    },
    "enumerate_tautomer": {
        "type": "bool",
        "default": False,
        "description": "When true, enumerates tautomers for the input."
    },
    "enumerate_isomer": {
        "type": "bool",
        "default": True,
        "description": "When true, cis/trans and R/S isomers are enumerated."
    },
    "optimizing_engine": {
        "type": "str",
        "default": "AIMNET",
        "description": "The engine used for optimization.",
        "choices": ["ANI2x", "ANI2xt", "AIMNET"]
    },
    "opt_steps": {
        "type": "int",
        "default": 5000,
        "description": "Maximum number of optimization steps.",
        "bounds": (1, None)  # Should be at least 1
    },
    "convergence_threshold": {
        "type": "float",
        "default": 0.003,
        "description": "Optimization is considered converged if maximum force is below this threshold.",
        "bounds": (0, None)  # Must be non-negative
    },
    "patience": {
        "type": "int",
        "default": 1000,
        "description": "If force does not decrease for patience steps, conformer drops out of optimization loop.",
        "bounds": (1, None)  # Must be at least 1
    },
    "threshold": {
        "type": "float",
        "default": 0.3,
        "description": "If RMSD between two conformers is within this threshold, one is removed as a duplicate.",
        "bounds": (0, None)  # Must be non-negative
    },
    "verbose": {
        "type": "bool",
        "default": False,
        "description": "When true, saves all metadata while running."
    },
    "capacity": {
        "type": "int",
        "default": 40,
        "description": "Number of SMILES the model handles per 1GB of memory.",
        "bounds": (1, None)  # At least 1
    },
    "batchsize_atoms": {
        "type": "int",
        "default": 1024,
        "description": "Number of atoms in one optimization batch per 1GB memory.",
        "bounds": (1, None)  # At least 1
    }
}


if __name__ == "__main__":
    asyncio.run(main())


