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

    def _find_pod_namespace(self, name):
        response = self._v1.list_pod_for_all_namespaces(watch=False)
        for item in response.items:
            if item.metadata.name == name:
                return item.metadata.namespace

    def start_sysdig_capture_for(self, pod_name, event_time,
                                 duration_in_seconds, s3_bucket,
                                 aws_access_key_id, aws_secret_access_key):
        job_name = 'sysdig-{}-{}'.format(pod_name, event_time)

        node_name = self.find_node_running_pod(pod_name)
        namespace = self._find_pod_namespace(pod_name)
        body = self._build_sysdig_capture_job_body(job_name,
                                                   node_name,
                                                   duration_in_seconds,
                                                   s3_bucket,
                                                   aws_access_key_id,
                                                   aws_secret_access_key)

        return self._batch_v1.create_namespaced_job(namespace, body)

    def _build_sysdig_capture_job_body(self, job_name, node_name,
                                       duration_in_seconds, s3_bucket,
                                       aws_access_key_id, aws_secret_access_key):
        return client.V1Job(
            metadata=client.V1ObjectMeta(
                name=job_name
            ),
            spec=client.V1JobSpec(
                template=client.V1PodTemplateSpec(
                    metadata=client.V1ObjectMeta(
                        name=job_name
                    ),
                    spec=client.V1PodSpec(
                        containers=[client.V1Container(
                            name='capturer',
                            image='sysdig/capturer',
                            image_pull_policy='Always',
                            security_context=client.V1SecurityContext(
                                privileged=True
                            ),
                            env=[
                                client.V1EnvVar(
                                    name='AWS_S3_BUCKET',
                                    value=s3_bucket
                                ),
                                client.V1EnvVar(
                                    name='CAPTURE_DURATION',
                                    value=str(duration_in_seconds)
                                ),
                                client.V1EnvVar(
                                    name='CAPTURE_FILE_NAME',
                                    value=job_name
                                ),
                                client.V1EnvVar(
                                    name='AWS_ACCESS_KEY_ID',
                                    value=aws_access_key_id,
                                ),
                                client.V1EnvVar(
                                    name='AWS_SECRET_ACCESS_KEY',
                                    value=aws_secret_access_key,
                                )
                            ],
                            volume_mounts=[
                                client.V1VolumeMount(
                                    mount_path='/host/var/run/docker.sock',
                                    name='docker-socket'
                                ),
                                client.V1VolumeMount(
                                    mount_path='/host/dev',
                                    name='dev-fs'
                                ),
                                client.V1VolumeMount(
                                    mount_path='/host/proc',
                                    name='proc-fs',
                                    read_only=True
                                ),
                                client.V1VolumeMount(
                                    mount_path='/host/boot',
                                    name='boot-fs',
                                    read_only=True
                                ),
                                client.V1VolumeMount(
                                    mount_path='/host/lib/modules',
                                    name='lib-modules',
                                    read_only=True
                                ),
                                client.V1VolumeMount(
                                    mount_path='/host/usr',
                                    name='usr-fs',
                                    read_only=True
                                ),
                                client.V1VolumeMount(
                                    mount_path='/dev/shm',
                                    name='dshm'

                                )
                            ]
                        )],
                        volumes=[
                            client.V1Volume(
                                name='dshm',
                                empty_dir=client.V1EmptyDirVolumeSource(
                                    medium='Memory'
                                )
                            ),
                            client.V1Volume(
                                name='docker-socket',
                                host_path=client.V1HostPathVolumeSource(
                                    path='/var/run/docker.sock'
                                )
                            ),
                            client.V1Volume(
                                name='dev-fs',
                                host_path=client.V1HostPathVolumeSource(

                                    path='/dev'
                                )
                            ),
                            client.V1Volume(
                                name='proc-fs',
                                host_path=client.V1HostPathVolumeSource(
                                    path='/proc'
                                )
                            ),

                            client.V1Volume(
                                name='boot-fs',
                                host_path=client.V1HostPathVolumeSource(
                                    path='/boot'
                                )
                            ),
                            client.V1Volume(
                                name='lib-modules',
                                host_path=client.V1HostPathVolumeSource(
                                    path='/lib/modules'
                                )
                            ),
                            client.V1Volume(
                                name='usr-fs',
                                host_path=client.V1HostPathVolumeSource(
                                    path='/usr'
                                )
                            )
                        ],
                        node_name=node_name,
                        restart_policy='Never'
                    )
                )
            )
        )
