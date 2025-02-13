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
    options = {
        simulation = {
            step_size_ps = 0.001,
            stages = [
                {
                    Nvt = {
                        temperature_kelvin = 300,
                        steps = 1000
                    }
                }
            ]
        },
        trajectory = {
            interval = 100,
            info = true
        }
    },
    dojo = \protein_trc -> dojo_rex_s default_runspec options [protein_trc] []
in
    \protein_trc -> dojo protein_trc
"""

client = build_blocking_provider(access_token=API_TOKEN)
benchmark = client.benchmark(name="OpenFF Protein-Ligand Binding Benchmark")
async def main():
    input_ = CreateRun(rex=rex_fn,name="Benchmark Request pushed from Adi's Computer", project_id=client.project_id)
    response = await benchmark_mutation(input_,benchmark.id,0.02,False,API_TOKEN)
    # the actual ID is set under response.run_benchmark.id
    run_benchmark_id = response['run_benchmark']['id']
    # Complepte automation has been achieved once we can use a Q to store the ids sequentially and then
    # via a reliever, get the benchmark_submission stats.
    # However, the most difficult thing to do right now is to understand the Rust code ig? I dont know, there must be
    # someway in which we can decipher which parts to keep and not to keep. Like are all modules required?
    # Lets see.i
    # response = await benchmark_submission("b11071e7-4662-4a0f-8579-815febd1f514", "0d2723d5-674e-430c-90be-7784d068247f", auth_token=API_TOKEN)
    # print(json.dumps(response, indent=1))  # Print the API response


if __name__ == "__main__":
    asyncio.run(main())

