import os
import yaml
import json
from conans.tools import save
from conans.tools import mkdir

def save(data, filename, format=None):
    path = os.path.abspath(filename)
    directory = os.path.dirname(path)
    mkdir(directory)
    raw = isinstance(data, (str, bytes))
    if not raw and not format:
        _, ext = os.path.splitext(filename)
        ext = ext.lower()
        if ext in ['.yml', '.yaml']:
            format = 'YAML'
        elif ext in ['.json']:
            format = 'JSON'
          
        else:
            raise Exception(f'Unkonwn format {filename}')
        
    mode = 'w'
    if raw and isinstance(data, bytes):
        mod += 'b'
    with open(filename, mode) as f:
        if raw:
            f.write(data)
        else:
            if format == 'YAML':
                yaml.dump(data, filename, default_flow_style=False)
            elif format == 'JSON':
                json.dump(data, f)
    
        