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

# Ideally, we will want to define a bulk mutator and a bulk fetcher,
# Both of these will do exactly what their name suggests
# Intermediate controller will be some kind of traffic_controller that can try to
# ensure that there is almost zero waste in time.
# The only problem would be to decide what inputs to give bulk mutator, and that needs to be specifically studied under **kwargs
# since it is relatively un-explored.

async def main():
    input_ = CreateRun(rex=rex_fn,name="Benchmark Request pushed from Adi's Computer", project_id=client.project_id)
    # response = await benchmark_mutation(input_,benchmark.id,0.02,False,API_TOKEN)
    # run_benchmark_id = response['run_benchmark']['id']

    # response = await benchmark_submission(run_benchmark_id, client.project_id, auth_token=API_TOKEN)
    # print(json.dumps(response.data, indent=1))  # Print the API response


if __name__ == "__main__":
    asyncio.run(main())

