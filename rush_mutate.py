from gql import Client, gql
from gql.transport.aiohttp import AIOHTTPTransport
from rush.graphql_client import CreateRun

# Define GraphQL endpoint
GRAPHQL_ENDPOINT = "https://tengu.qdx.ai"
MUTATION_QUERY="""
    mutation run_benchmark($input: CreateRun!, $benchmark_id: BenchmarkId!, $sample_pct: Float, $with_outs: Boolean) {
        run_benchmark(
            input: $input
            benchmark_id: $benchmark_id
            sample: $sample_pct
            with_outs: $with_outs
        ) {
            id
            source_run {
                id
            }
        }
    }
"""
# GraphQL Mutation
MUTATION_RUN_BENCHMARK = gql(MUTATION_QUERY)

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
# Function to execute GraphQL mutation
async def benchmark_mutation(input_data, benchmark_id, sample_pct, with_outs, auth_token):
    print(f"🚀 Running benchmark with ID: {benchmark_id}")

    transport = AIOHTTPTransport(
        url=GRAPHQL_ENDPOINT,
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    # Create GraphQL client
    async with Client(transport=transport, fetch_schema_from_transport=True) as session:
        try:
            # Prepare mutation variables
            variables = {
                "input": input_data.dict(exclude_unset=True),
                "benchmark_id": benchmark_id,
                "sample_pct": sample_pct,
                "with_outs": with_outs
            }
# 59dfc6a0-c77d-4373-9a39-b550110e89de
            return await session.execute(MUTATION_RUN_BENCHMARK, variable_values=variables, operation_name="run_benchmark")

        except Exception as e:
            print(f"❌ Error: {e}")
            return None


