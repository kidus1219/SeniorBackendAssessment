bind = "0.0.0.0:8000"
workers = 1
preload_app = True


def when_ready(server):
    print('---------- READY -----------------')


def post_fork(server, worker):
    print('---------- POST FORK -----------------')


def post_worker_init(worker):
    print('---------- POST WORKER INIT -----------------')
