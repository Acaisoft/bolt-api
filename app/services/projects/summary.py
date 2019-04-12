from gql import gql

from app.hasura_client import hasura_client


def get_project_summary(config, project_id):

    gclient = hasura_client(config)

    resp = gclient.execute(gql('''query ($pid:uuid!) {
      scenarios: configuration_aggregate(where:{
        project_id:{_eq:$pid}
        is_deleted:{_eq:false}
      }) {
        aggregate {
          count
        }
      }
      
      sources: test_source_aggregate(where:{
        project_id:{_eq:$pid}
      }) {
        aggregate {
          count
        }
      }
      
      tests: result_aggregate_aggregate(
        where:{execution:{configuration:{project_id:{_eq:$pid}}}}
      ) {
        aggregate {
          sum {
            number_of_successes
            number_of_fails
          }
        }
      }
    }'''), {'pid': str(project_id)})

    return {
        'num_scenarios': resp['scenarios']['aggregate']['count'],
        'num_sources': resp['sources']['aggregate']['count'],
        'num_tests_passed': resp['tests']['aggregate']['sum']['number_of_successes'],
        'num_tests_failed': resp['tests']['aggregate']['sum']['number_of_fails'],
    }