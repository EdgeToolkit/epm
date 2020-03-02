import os
import yaml
import argparse
import gitlab

_DIR = os.path.abspath(os.path.dirname(__file__))


class Register(object):

    def __init__(self, filename, hosts):
        self._register = {}
        self._gitlab = None
        if not filename or not hosts:
            return

        self._rootdir = os.path.dirname(os.path.abspath(hosts))
        with open(filename) as f:
            self._items = yaml.safe_load(f)
        self._url = self._items['gitlab_ci_url']

    @property
    def gitlab(self):
        if self._gitlab is None:
            self._gitlab = gitlab.Gitlab.from_config('root.ci', os.path.join(_DIR, 'python-gitlab.cfg'))
        return self._gitlab

    def run(self):
        gl = self.gitlab
        for runner_name, runner in self._items['runners'].items():
            self._register[runner_name] = {}
            tags = runner['tags']
            desc = runner['description']

            for hostname in self._items['hosts'][runner_name]:
                for reg_token in runner['tokens']:
                    metadata = {'token': reg_token,
                                'description': desc.format(hostname=hostname),
                                'tag_list': tags
                                }
                    reg = gl.runners.create(metadata)
                    items = {'id': reg.id, 'token': reg.token}
                    self._register[runner_name][hostname] = dict(metadata, **items)

        for name, runner in self._register.items():
            path = os.path.join(self._rootdir, 'group_vars', name)
            if not os.path.exists(path):
                os.makedirs(path)
            with open(os.path.join(path, 'runner.yml'), 'w') as f:
                yaml.safe_dump({'gitlab_runners': runner}, f)

    def unregister(self):
        gl = self.gitlab
        rootdir = 'group_vars'

        for i in os.listdir(rootdir):
            path = os.path.join('group_vars', i, 'runner.yml')
            if os.path.exists(path):
                with open(path) as f:
                    info = yaml.safe_load(f)
                    for host, item in info['gitlab_runners'].items():
                        try:
                            runner = gl.runners.get(item['id'])
                            if item['token'] == runner.token:
                                gl.runners.delete(item['id'])
                            else:
                                print('gitlab runner <%s> error.')
                        except Exception as e:
                            print('gitlab runner %s error. %s' % (item['id'], e))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config', help="path of configure file.")
    parser.add_argument('-i', '--hosts', help="inventory hosts file of register.")
    parser.add_argument('--unregister', default=False, action='store_true')

    args = parser.parse_args()
    register = Register(args.config, args.hosts)
    if args.unregister:
        register.unregister()
    else:
        register.run()


if __name__ == '__main__':
    main()
