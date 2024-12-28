import os
import subprocess, re

env_name = 'ping'
directory = os.path.dirname(os.path.realpath(__file__))

def conda_env_exists(env_name):
    result = subprocess.run('conda env list', shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    envs = result.stdout.splitlines()
    for env in envs:
        if re.search(rf'^{env_name}\s', env):
            return True
    return False

if conda_env_exists(env_name):
    print(f"Updating '{env_name}' environment ...")
    subprocess.run(os.path.join(directory, "Update.bat"), shell=True)
else:
    print(f"Creating '{env_name}' environment...")
    subprocess.run(os.path.join(directory, "Install.bat"), shell=True)

