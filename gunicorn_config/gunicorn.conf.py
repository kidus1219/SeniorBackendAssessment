bind = 'unix:/var/www/ideeza/app.sock'
workers = 1
# worker_class = "uvicorn.workers.UvicornWorker"
preload_app = True

accesslog = '-'   # log access logs to stdout
errorlog = '-'    # log error logs to stderr


def when_ready(server):
    print('---------- READY -----------------')
    open('/tmp/app-initialized', 'w').close()



def post_fork(server, worker):
    print('---------- POST FORK -----------------')


def post_worker_init(worker):
    print('---------- POST WORKER INIT -----------------')
