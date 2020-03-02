import gitlab


#gl = gitlab.Gitlab.from_config('root.ci', ['python-gitlab.cfg'])
#gitlab.Gitlab.from_config
#runners = gl.runners.all()
gl = gitlab.Gitlab('http://172.16.0.119:8000/')
runner = gl.runners.create({'token': 'HuTeuBHHCHS-zGnxQRY8'})
print(runner)
