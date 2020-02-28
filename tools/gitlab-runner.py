import gitlab


gl = gitlab.Gitlab.from_config('root.ci', ['python-gitlab.cfg'])
runners = gl.runners.all()
#runner = gl.runners.create({'token': 'HuTeuBHHCHS-zGnxQRY8'})
print(runners)
