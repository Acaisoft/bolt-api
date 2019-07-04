import enum


class ArgoFlow(enum.Enum):
    POD = 'Pod'
    RETRY = 'Retry'
    BUILD = 'build'
    MONITORING = 'monitoring'
    PRE_START = 'pre-start'
    POST_STOP = 'post-stop'
    LOAD_TESTS_MASTER = 'load-tests-master'
    LOAD_TESTS_SLAVE = 'load-tests-slave'


class Status(enum.Enum):
    ERROR = 'ERROR'
    FAILED = 'FAILED'
    PENDING = 'PENDING'
    RUNNING = 'RUNNING'
    SUCCEEDED = 'SUCCEEDED'
    TERMINATED = 'TERMINATED'
    FINISHED = 'FINISHED'
