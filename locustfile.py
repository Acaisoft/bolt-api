# local testing of testrunner, use with 6 slaves hitting on an nginx
from locust import HttpLocust, TaskSet


def index(l):
    l.client.get('/')


class UserBehavior(TaskSet):
    tasks = {
        index: 1,
    }


class WebsiteUser(HttpLocust):
    task_set = UserBehavior
    min_wait = 5
    max_wait = 8
