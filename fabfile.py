from __future__ import with_statement
from fabric.api import *
from fabric.contrib.console import confirm

env.hosts = ['apoc']
env.use_ssh_config = True

def deploy():
    code_dir = '/home/svenstaro/prj/flamejam'
    deploy_dir = '/srv/flamejam'

    # clone/pull using keybearer first
    with settings(warn_only=True):
        if run("test -d %s" % code_dir).failed:
            run("git clone git@github.com:svenstaro/flamejam.git %s" % code_dir)
    with cd(code_dir):
        run("git pull")
        sudo("make install")
        sudo("touch %s/flamejam.wsgi" % deploy_dir)
