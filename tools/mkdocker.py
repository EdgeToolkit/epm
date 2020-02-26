#
#
#
# config file (YAML format)
# pip:
#   mirror: http://<hostname>:<port>/...
#   http_proxy: http://<hostname>:<port>
#
##########################################################
import os
import yaml
import jinja2
import argparse
from urllib.parse import urlparse

class Config(object):
    mirror = None
    http_proxy  = None    

    def __init__(self, filename=None):
      if filename:
          with open(filename) as f:
              self._items = yaml.safe_load(f)
          self.mirror = self._items.get('pip', {}).get('mirror')
          self.http_proxy = self._items.get('pip', {}).get('proxy') 

    @property
    def trusted_host(self):
        if self.mirror:
            result = urlparse(self.mirror)
            if result.scheme == 'http':
                return result.hostname
        return None



class Dockerfile(object):

    def __init__(self, name, version=None, dir=None, config=None):
      self._name = name
      self._dir = os.path.abspath( dir or 'tools/docker')
      m = __import__('./epm')
      self._version = version or m.__version__
      self._config = config or Config()


    def _render(self, **kwargs):
        if not os.path.exists(os.path.join(self._dir,self._name +'.j2')):
            raise Exception('Jinja2 template %s not exists' % self._name)

        loader = jinja2.FileSystemLoader(searchpath=self._dir)
        env = jinja2.Environment(loader=loader)
        template = env.get_template('%s.j2' % self._name)
        options=''
        if self._config.mirror:
            options += ' -i %s' % self._config.mirror
            if self._config.trusted_host:
                options += ' --trusted-host %s' % self._config.trusted_host
            if self._config.http_proxy:
                options += ' --proxy %s' % self._config.http_proxy
        vars = dict({'name': self._name,
                     'version': self._version,
                     'config': self._config,
                     'options': options,
                     },
                    **kwargs)

        return template.render(vars)

    def write(self, filename='Dockerfile'):
        content = self._render()
        with open(filename, 'w') as f:
            f.write(content)
      
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('name', nargs=1, help="name of the docker image to build.")
    parser.add_argument('--version', help="configure file path.")
    parser.add_argument('-c', '--config', help="configure file path.")
    parser.add_argument('-B', '--build', default=False, action="store_true", help="buildconfigure file path.")
    args = parser.parse_args()
    config = Config(args.config or None)
    m = __import__('./epm')
    version = args.version or m.__version__
    name = args.name[0]
    docerfile = Dockerfile(name,version, config=config)
    docerfile.write()
    if args.build:
        import subprocess
        command = ['docker', 'build','.', '-t', 'epmkit/%s:%s' % (name, version)]
        subprocess.run(command, check=True)

if __name__ == '__main__':
    print(os.path.abspath('.'))
    main()
