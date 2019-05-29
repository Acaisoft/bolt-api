from services.hasura import hce


def get_project_summary(config, user_id):

    resp = hce(config, '''query ($uid: uuid!) {
      project(where: {is_deleted: {_eq: false}, userProjects: {user_id: {_eq: $uid}}}) {
        id
        name
        description
        image_url
        
        scenarios: configurations_aggregate(where: {
            is_deleted: {_eq: false}, 
            project: {is_deleted: {_eq: false}, userProjects: {user_id: {_eq: $uid}}}
        }) {
          aggregate {
            count
          }
        }
        
        sources: test_sources_aggregate(where: {
            is_deleted: {_eq: false}, 
            project: {is_deleted: {_eq: false}, userProjects: {user_id: {_eq: $uid}}}
        }) {
          aggregate {
            count
          }
        }
      }
      
      tests: execution_aggregate(
        distinct_on: configuration_id, 
        where: {
            configuration: {is_deleted: {_eq: false}, 
            project: {is_deleted: {_eq: false}, userProjects: {user_id: {_eq: $uid}}}}
        }
      ) {
        nodes {
          configuration {
            project_id
            executions_aggregate {
              aggregate {
                sum {
                  passed_requests
                  failed_requests
                }
              }
            }
          }
        }
      }
    }
    ''', {'uid': str(user_id)})

    out = {}

    for p in resp['project']:
        out[p['id']] = {
            'project_id': p['id'],
            'name': p['name'],
            'description': p['description'],
            'image_url': p['image_url'],
            'num_scenarios': p['scenarios']['aggregate']['count'],
            'num_sources': p['sources']['aggregate']['count'],
            'num_tests_passed': 0,
            'num_tests_failed': 0,
        }

    for i in resp['tests']['nodes']:
        pid = i['configuration']['project_id']
        item = i['configuration']['executions_aggregate']['aggregate']['sum']
        out[pid]['num_tests_passed'] += item['passed_requests']
        out[pid]['num_tests_failed'] += item['failed_requests']

    return list(out.values())
