from services.hasura import hce


def get_project_summary(config, user_id):

    resp = hce(config, '''query ($uid:uuid!) {
      scenarios: configuration_aggregate(where:{
          is_deleted: {_eq: false}, 
          project: {
            is_deleted: {_eq: false}, 
            userProjects: { user_id: {_eq: $uid} }
          }
      }) {
        aggregate {
          count
        }
      }
      
      sources: test_source_aggregate(where:{
          is_deleted: {_eq: false}, 
          project: {
            is_deleted: {_eq: false}, 
            userProjects: { user_id: {_eq: $uid} }
          }
      }) {
        aggregate {
          count
        }
      }
      
      tests: execution_aggregate(where: {
        configuration: {
          is_deleted: {_eq: false}, 
          project: {
            is_deleted: {_eq: false}, 
            userProjects: { user_id: {_eq: $uid} }
          }
        }
      }) {
        aggregate {
          sum {
            total_requests
            failed_requests
            passed_requests
          }
        }
      }
    }''', {'uid': str(user_id)})

    return {
        'num_scenarios': resp['scenarios']['aggregate']['count'],
        'num_sources': resp['sources']['aggregate']['count'],
        'num_tests_passed': resp['tests']['aggregate']['sum']['passed_requests'],
        'num_tests_failed': resp['tests']['aggregate']['sum']['failed_requests'],
    }