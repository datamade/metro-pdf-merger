import resource

from tasks import queue_daemon


MAX_VIRTUAL_MEMORY = 150 * 1024 * 1024
soft, hard = resource.getrlimit(resource.RLIMIT_AS)
resource.setrlimit(resource.RLIMIT_AS, (MAX_VIRTUAL_MEMORY, hard))
queue_daemon()
