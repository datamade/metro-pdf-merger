REDIS_QUEUE_KEY = 'metro_merger'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,

    'formatters': {
        'all': {
            'format': '[%(asctime)s][%(levelname)s] '
                      '%(filename)s:line:%(lineno)d | %(message)s',
            'datefmt': "%B %d, %Y - %H:%M:%S",
        },
    },
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': 'debug.log',
            'formatter': 'all'
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'all',
        },
    },

    'loggers': {
        'tasks': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
            },
    }
}

DEBUG = True