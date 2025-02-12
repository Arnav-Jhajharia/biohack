import os
from gql import Client, gql
from gql.transport.aiohttp import AIOHTTPTransport

GRAPHQL_ENDPOINT = "https://tengu.qdx.ai"
QUERY_DATA ="""
    query benchmark_submission($id: BenchmarkSubmissionId!, $project_id: ProjectId!) {
        me {
            account {
                project(id: $project_id) {
                    benchmark_submission(id: $id) {
                        ...BenchmarkSubmissionFields
                    }
                }
            }
        }
    }

    fragment BenchmarkSubmissionFields on BenchmarkSubmission {
        id
        name
        description
        created_at
        updated_at
        deleted_at
        tags
        scores {
            nodes {
                id
                score
                name
                tags
            }
        }
        benchmark {
            id
        }
        data {
            nodes {
                id
                scores {
                    nodes {
                        id
                        score
                        name
                        tags
                    }
                }
            }
        }
        source_run {
            id
            status
            result
        }
    }
"""
# Define the GraphQL query
QUERY_BENCHMARK_SUBMISSION = gql(QUERY_DATA)

# Function to execute GraphQL query
async def benchmark_submission(benchmark_id, project_id, auth_token):
    # Set up GraphQL transport with authentication
    transport = AIOHTTPTransport(
        url=GRAPHQL_ENDPOINT,
        headers={"Authorization": f"Bearer {auth_token}"}
    )


    async with Client(transport=transport, fetch_schema_from_transport=True) as session:
        result = await session.execute(QUERY_BENCHMARK_SUBMISSION, variable_values={"id": benchmark_id, "project_id": project_id})
        return result