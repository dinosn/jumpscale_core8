from JumpScale import j
import signal
import time
from multiprocessing import Pool
from threading import Thread
import requests


def run_action(repo_path, service_key, action_name, args=None):
    """
    run_action execute a single action from a service
    """
    if not args:
        args = {}

    repo = j.atyourservice.repoGet(repo_path)
    service = repo.db.services.get(service_key).objectGet(repo)

    job = service.getJob(action_name, args=args)
    job.executeInProcess()

    service.model.actions[action_name].lastRun = j.data.time.epoch
    service.saveAll()


def do_run(run_key, callback=None):
    """
    do_run execute a run asynchronously
    at the end of the run or if an error occurs during exection a request is made to callback to
    notify the event (ok/error)
    """
    error_msg = None

    try:
        run = j.core.jobcontroller.db.runs.get(run_key).objectGet()
        run.execute()
    except Exception as e:
        error_msg = str(e)
    finally:
        if callback:
            body = {
                'state': str(run.state),
                'key': run.key
            }
            if error_msg:
                body['error'] = error_msg
            requests.post(callback, json=body)


class Server:
    """AtYourService server"""

    def __init__(self, redis_config=None):
        redis_config = redis_config or j.atyourservice.config['redis']
        self._command_queue = j.servers.kvs.getRedisStore("ays_server", namespace='db', **redis_config)

        self.logger = j.atyourservice.logger

        # RecurringLoop is used for dispatching the requests (events/execute/run) asynchronously
        self._recurring_loop = RecurringLoop()
        self._workers = Pool()

        # self._set_signale_handler()

        self._running = False

    def _set_signale_handler(self):
        def stop(signum, stack_frame):
            self.stop()

        # HANDLE INTERRUPT SIGNAL using stop method.
        signal.signal(signal.SIGINT, stop)

    def start(self):
        """
        Starting AYS Server.
        """
        if self._running is True:
            return

        # START THE RECURRING LOOP.
        self._recurring_loop.start()

        self.logger.info('starting server')
        self._running = True

        while self._running:
            # FETCH COMMAND FROM THE QUEUE AND MAKE A `REQUEST` TO DISPATCH.
            # COMMAND CAN BE ONE OF (execute/run/event)
            # (i.e) payload = {"command": "event", "event": "producer_installed", "args":[""]}
            payload = self._command_queue.queueGet('command', timeout=2)
            if payload is None:
                # timeout without receiving command
                continue

            try:
                request = j.data.serializer.json.loads(payload.decode())
            except Exception as e:
                self.logger.error("can't deserialize payload : %s" % str(e))
                continue

            if not j.data.types.dict.check(request) or 'command' not in request:
                self.logger.error("request doesn't have proper format, should be a dict with a 'command' key. request is: %s" % request)
                continue

            # DISPATCH REQUEST TO THE APPROPRIATE HANDLER.
            self._dispatch(request)

        self.logger.info('server stopped')

    def stop(self):
        if self._recurring_loop.is_alive():
            self.logger.info("stopping monitor recurring process")
            self._recurring_loop.stop()
            # FIXME: why:  assert self._parent_pid == os.getpid(), 'can only join a child process'
            # self._recurring_loop.join()

        if self._running:
            self._running = False
            self.logger.info("stopping server")

        self.logger.info("wait for all jobs to finish")
        self._workers.close()
        self._workers.join()

    def _dispatch(self, request):
        """
        Dispatch the request to the appropriate handler.
        """
        self.logger.info('dispatch request %s' % request)

        # TODO: implement other commands
        if request['command'] == 'execute':
            self._execute(request)

        elif request['command'] == 'event':
            self._propagate_event(request)

        elif request['command'] == 'run':
            self._do_run(request)

    def _execute(self, request):
        if 'action' not in request:
            self.logger.error('execute command received but not action specified in request.')
            return

        try:
            self.logger.info("execute action {action} on {service_key}".format(**request))
            self._workers.apply_async(run_action, (
                request['repo_path'],
                request['service_key'],
                request['action'],
                request.get('args', {})))
        except Exception as e:
            self.logger.error('error: %s' % str(e))

    def _propagate_event(self, request):
        """
         propagate event to the underlying services in all repos for the subscribed services.
        """
        if 'event' not in request:
            self.logger.error('event command received but not event type specified in request.')
            return

        event_type = request['event']
        args = request.get('args', {})

        for repo in j.atyourservice.reposList():
            for service in repo.services:
                # SEARCH FILTERS TO CHECK IF `service` IS INTERESTED IN THAT KIND OF EVENT `event_type`
                filters = service.model.eventFiltersFind(command=event_type)
                if not len(filters):
                    continue

                for f in filters:
                    action = f.action
                    self._workers.apply_async(run_action, (
                        service.aysrepo.path,
                        service.model.key,
                        action,
                        {'event_args': args}))

    def _do_run(self, request):
        """
        do run asynchronously.
        """
        if 'run_key' not in request:
            self.logger.error("run_key not present in request. can't execute run")
            return

        self.logger.info("execute run {}".format(request['run_key']))
        self._workers.apply_async(do_run, (
            request['run_key'],
            request.get('callback_url')))


class RecurringLoop(Thread):
    """
    Loop that triggers the recurring action of all the services

    The loop walks over all the services from all the repos. When it find a service with recurring actions,
    it send a command to the main server to ask to execute the action.
    The main server then received the request, create the jobs and execute it asynchronously.
    The main server doesn't wait for the job to complete but instead send the execute of the job to a pool of processes
    that take care of waiting for the job to complete and saving it's state back the db.
    """

    def __init__(self):
        super(RecurringLoop, self).__init__()
        self.logger = j.atyourservice.logger
        self._running = False
        self._workers = Pool()

    def run(self):
        self.logger.info('starting recurring thread')
        self._running = True

        while self.is_alive() and self._running:
            repos = j.atyourservice.reposList()
            for repo in repos:
                self.logger.debug('inspect %s for recurring actions' % repo)
                for service in repo.services:
                    if len(service.model.actionsRecurring) <= 0:
                        continue

                    now = j.data.time.epoch
                    for action_name, recurring_obj in service.model.actionsRecurring.items():
                        # FIXME: FIX THE dependency_chain check.
                        # deptree = service._build_actions_chain(action=action_name)
                        # ### PLEASE EXPLAIN
                        # for acname in deptree[:-1]:
                        #     ac = service.model.actions[acname]
                        #     if ac.state != 'ok':
                        #         break
                        # else:
                        #     continue
                        if recurring_obj.lastRun == 0 or now > (recurring_obj.lastRun + recurring_obj.period):
                            self.logger.info('recurring job for %s' % service)
                            try:
                                self._workers.apply_async(run_action, (
                                    service.aysrepo.path,
                                    service.model.key,
                                    action_name,
                                ))
                            except Exception as e:
                                self.logger.error('error: %s' % str(e))
            time.sleep(5)

    def stop(self):
        if self._running:
            self._running = False


def main():
    """
    only for testing
    """
    server = Server()
    server.start()


if __name__ == '__main__':
    main()
