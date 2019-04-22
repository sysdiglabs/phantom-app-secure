import os

# Before importing from kubernetes, we need to fix the google auth structure for
# Python 2.7
#
# We add a __init__.py file in google for handing those paths as Python Packages
empty_python_package = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dependencies', 'google', '__init__.py' )
open(empty_python_package, 'a').close()

from kubernetes import client, config


class KubernetesClient(object):
    def __init__(self, config_file):
        config.load_kube_config(config_file=config_file)

        self._v1 = client.CoreV1Api()
        self._batch_v1 = client.BatchV1Api()

    def find_node_running_pod(self, name):
        response = self._v1.list_pod_for_all_namespaces(watch=False)
        for item in response.items:
            if item.metadata.name == name:
                return item.spec.node_name
