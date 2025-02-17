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

# Function to execute GraphQL mutation
async def benchmark_mutation(input_data, benchmark_id, sample_pct, with_outs, auth_token):

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

            return await session.execute(MUTATION_RUN_BENCHMARK, variable_values=variables, operation_name="run_benchmark", serialize_variables=True, get_execution_result=True)

        except Exception as e:
            print(f"❌ Error: {e}")
            return None