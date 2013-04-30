from __future__ import with_statement
from fabric.api import *
from fabric.contrib.console import confirm

env.hosts = ['apoc']
env.use_ssh_config = True

def deploy():
    code_dir = '/home/svenstaro/prj/flamejam'
    deploy_dir = '/var/flask-sites/flamejam'

    # clone/pull using keybearer first
    with settings(warn_only=True):
        if run("test -d %s" % code_dir).failed:
            run("git clone git@github.com:svenstaro/flamejam.git %s" % code_dir)
    with cd(code_dir):
        run("git pull")

    # then do local clone using web user
    with settings(warn_only=True):
        if run("test -d %s" % deploy_dir).failed:
            sudo("git clone %s %s" % (code_dir, deploy_dir))
    with cd(deploy_dir):
        sudo("git pull")
        sudo("touch flamejam.wsgi")
