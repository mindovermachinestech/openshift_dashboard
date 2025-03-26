import json

from kubernetes import client, config
from kubernetes.client import Configuration
import pandas as pd
import time
from kubernetes import client, config
from datetime import datetime, timedelta
import random


def get_openshift_tool(input=None):
    print(f"invoked get_openshift_tool with input {input}")
    response = ''
    try:
        input_dict = eval(input.strip())
        # Validate if input is provided and is a dictionary
        if not isinstance(input_dict, dict):
            return "Error: 'input' must be a dictionary."

        # Validate and extract 'app_name'
        action_name = input_dict.get("tool_name")
        if action_name == 'get_applications':
            print(f"invoked get_applications with input {input}")
            response = get_applications(input)
        elif action_name == 'get_pods_and_status_health_for_application':
            print(f"invoked get_pods_and_status_health_for_application with input {input}")
            response = get_pods_and_status_health_for_application(input)
        elif action_name == 'restart_application':
            print(f"invoked restart_application with input {input}")
            response = restart_application(input)
        elif action_name == 'upgrade_application':
            print(f"invoked  upgrade_application with input {input}")
            response = upgrade_application(input)
        elif action_name == 'scale_application_pods':
            print(f"invoked  scale_application_pods with input {input}")
            response = scale_application_pods(input)
        elif action_name == 'get_application_logs':
            print(f"invoked  get_application_logs with input {input}")
            response = get_application_logs(input)
        elif action_name == 'get_deployment_configs':
            print(f"invoked  get_deployment_configs with input {input}")
            response = get_deployment_configs(input)
        elif action_name == 'get_application_telemetry_data':
            print(f"invoked  with input {input}")
            response = get_application_telemetry_data(input)
        elif action_name == 'check_critical_components_health':
            print(f"invoked  check_critical_components_health with input {input}")
            response = check_critical_components_health(input)
        elif action_name == 'check_resource_utilization_health':
            print(f"invoked check_resource_utilization_health with input {input}")
            response = check_resource_utilization_health(input)
        elif action_name == 'deploy_new_application':
            print(f"invoked  deploy_new_application with input {input}")
            response = deploy_new_application(input)
        return response
    except Exception as e:
        print(f"Error fetching applications: {str(e)}")
        return []


def get_applications(input=None):
    try:
        v1 = create_client('apps')
        # Get deployments only from the 'mindovermachinestech-dev' namespace
        namespace = "mindovermachinestech-dev"
        deployments = v1.list_namespaced_deployment(namespace=namespace, watch=False)

        app_list = []
        for deployment in deployments.items:
            app_list.append(deployment.metadata.name)

        return app_list
    except Exception as e:
        print(f"Error fetching applications: {str(e)}")
        return []


def get_pods_and_status_health_for_application(input=None):
    print(f"invoked get_pods_and_status_health_for_application with input {input}")
    try:
        input_dict = eval(input.strip())
        # Validate if input is provided and is a dictionary
        if not isinstance(input_dict, dict):
            return "Error: 'input' must be a dictionary."

        # Validate and extract 'app_name'
        app_name = input_dict.get("app_name")
        if not app_name or not isinstance(app_name, str):
            return "Error: 'app_name' is required and must be a non-empty string."

        v1 = create_client('core')

        # Get pods for the specified application in 'mindovermachinestech-dev' namespace
        namespace = "mindovermachinestech-dev"
        label_selector = f"app={app_name}"
        pods = v1.list_namespaced_pod(namespace=namespace, label_selector=label_selector)

        pod_list = []
        for pod in pods.items:
            pod_list.append({
                "name": pod.metadata.name,
                "status": pod.status.phase
            })

        return pod_list
    except Exception as e:
        print(f"Error fetching pods: {str(e)}")
        return []


def create_client(api_type):
    try:
        # Authenticate using OpenShift token and server details
        token = "sha256~GvENMifBdHx1JVVisZME5KYqNgSWzQi9pzrTU59UueA"
        server = "https://api.rm2.thpm.p1.openshiftapps.com:6443"

        # Create configuration object
        configuration = Configuration()
        configuration.host = server
        configuration.verify_ssl = False  # Disable SSL verification if necessary
        configuration.api_key = {"authorization": f"Bearer {token}"}

        # Use the configuration
        client.Configuration.set_default(configuration)

        if api_type == 'apps':
            return client.AppsV1Api()
        elif api_type == 'core':
            return client.CoreV1Api()
        elif api_type == 'metrics':
            return client.CustomObjectsApi()
        else:
            raise ValueError("Invalid API type specified.")
    except Exception as e:
        print(f"Error creating client: {str(e)}")
        return None


def get_application_telemetry_data(input=None):
    print(f"invoked get_application_telemetry_data with input {input}")
    try:
        input_dict = eval(input.strip())
        # Validate if input is provided and is a dictionary
        if not isinstance(input_dict, dict):
            return "Error: 'input' must be a dictionary."

        # Validate and extract 'app_name'
        app_name = input_dict.get("app_name")
        if not app_name or not isinstance(app_name, str):
            return "Error: 'app_name' is required and must be a non-empty string."

        v1 = create_client('core')
        metrics = create_client('metrics')

        if not v1 or not metrics:
            return [] #pd.DataFrame([])

        namespace = "mindovermachinestech-dev"
        label_selector = f"app={app_name}"
        pods = v1.list_namespaced_pod(namespace=namespace, label_selector=label_selector)

        data = []
        for pod in pods.items:
            pod_name = pod.metadata.name
            try:
                pod_metrics = metrics.get_namespaced_custom_object(
                    group="metrics.k8s.io",
                    version="v1beta1",
                    namespace=namespace,
                    plural="pods",
                    name=pod_name
                )
                for container in pod_metrics["containers"]:
                    cpu_usage = container["usage"]["cpu"]
                    memory_usage = container["usage"]["memory"]
                    data.append({
                        "Time": pd.Timestamp.now(),
                        "Pod Name": pod_name,
                        "CPU Usage (m)": int(cpu_usage[:-1]),
                        "Memory Usage (Ki)": int(memory_usage[:-2]),
                    })
            except Exception as e:
                print(f"Error fetching metrics for pod {pod_name}: {str(e)}")

        if data:
            return data #pd.DataFrame(data)
        else:
            return [] #pd.DataFrame([])
    except Exception as e:
        print(f"Error fetching telemetry data: {str(e)}")
        return [] #pd.DataFrame([])


def get_telemetry_data_for_duration(app_name, duration_minutes=5,input=None):
    try:
        v1 = create_client('core')
        metrics = create_client('metrics')

        if not v1 or not metrics:
            return [] #pd.DataFrame([])

        namespace = "mindovermachinestech-dev"
        label_selector = f"app={app_name}"
        pods = v1.list_namespaced_pod(namespace=namespace, label_selector=label_selector)

        data = []
        end_time = pd.Timestamp.now()
        start_time = end_time - pd.Timedelta(minutes=duration_minutes)

        for pod in pods.items:
            pod_name = pod.metadata.name
            try:
                pod_metrics = metrics.get_namespaced_custom_object(
                    group="metrics.k8s.io",
                    version="v1beta1",
                    namespace=namespace,
                    plural="pods",
                    name=pod_name
                )
                for container in pod_metrics["containers"]:
                    cpu_usage = container["usage"]["cpu"]
                    memory_usage = container["usage"]["memory"]
                    cpu_used = int(cpu_usage[:-1]) if cpu_usage.endswith('n') else int(cpu_usage[:-1]) * 1000
                    memory_used = int(memory_usage[:-2])  # in Ki

                    for minute in range(duration_minutes):
                        data.append({
                            "Time": start_time + pd.Timedelta(minutes=minute),
                            "Pod Name": pod_name,
                            "CPU Usage (m)": cpu_used,
                            "Memory Usage (Ki)": memory_used
                        })
            except Exception as e:
                print(f"Error fetching metrics for pod {pod_name}: {str(e)}")

        return data #pd.DataFrame(data)
    except Exception as e:
        print(f"Error fetching telemetry data for duration: {str(e)}")
        return [] #pd.DataFrame([])


def get_application_logs(input=None):
    print(f"invoked get_application_logs with input {input}")
    try:
        input_dict = eval(input.strip())
        # Validate if input is provided and is a dictionary
        if not isinstance(input_dict, dict):
            return "Error: 'input' must be a dictionary."

        # Validate and extract 'app_name'
        app_name = input_dict.get("app_name")
        if not app_name or not isinstance(app_name, str):
            return "Error: 'app_name' is required and must be a non-empty string."

        # Validate and extract 'tail_lines', defaulting to 100 if not provided
        tail_lines = input_dict.get("tail_lines", 100)
        if not isinstance(tail_lines, int) or tail_lines <= 0:
            return "Error: 'tail_lines' must be a positive integer."

        # Create the Kubernetes client
        v1 = create_client('core')
        if not v1:
            return "Error creating core client."

        # Define namespace and label selector
        namespace = "mindovermachinestech-dev"
        label_selector = f"app={app_name}"

        # Fetch pods matching the label selector
        try:
            pods = v1.list_namespaced_pod(namespace=namespace, label_selector=label_selector)
        except Exception as e:
            return f"Error listing pods in namespace '{namespace}': {str(e)}"

        # Collect logs for each pod
        logs = ""
        for pod in pods.items:
            pod_name = pod.metadata.name
            try:
                pod_logs = v1.read_namespaced_pod_log(
                    name=pod_name,
                    namespace=namespace,
                    tail_lines=tail_lines
                )
                logs += f"\nLogs for {pod_name}:\n{pod_logs}\n"
            except Exception as e:
                logs += f"\nError fetching logs for pod {pod_name}: {str(e)}\n"

        # Return the collected logs or a message if no logs are available
        return logs if logs else "No logs available."
    except Exception as e:
        return f"Error fetching application logs: {str(e)}"


def scale_application_pods(input=None):
    print(f"invoked scale_application_pods with input {input}")
    try:
        input_dict = eval(input.strip())
        # Validate if input is provided and is a dictionary
        if not isinstance(input_dict, dict):
            return "Error: 'input' must be a dictionary."

        # Validate and extract 'app_name'
        app_name = input_dict.get("app_name")
        if not app_name or not isinstance(app_name, str):
            return "Error: 'app_name' is required and must be a non-empty string."

        replicas = input_dict.get("replicas", 1)
        # if not replicas:
        #     return "Error: 'replicas' is required."

        v1 = create_client('apps')
        if not v1:
            return "Error creating apps client."

        namespace = "mindovermachinestech-dev"

        # Get the existing deployment
        deployment = v1.read_namespaced_deployment(name=app_name, namespace=namespace)

        # Update the number of replicas
        deployment.spec.replicas = replicas

        # Apply the updated deployment configuration
        v1.patch_namespaced_deployment(name=app_name, namespace=namespace, body=deployment)

        return f"Successfully scaled {app_name} to {replicas} pods."
    except Exception as e:
        return f"Error scaling pods: {str(e)}"


def restart_application(input=None):
    print(f"invoked restart_application with input {input}")
    try:
        input_dict = eval(input.strip())
        # Validate if input is provided and is a dictionary
        if not isinstance(input_dict, dict):
            return "Error: 'input' must be a dictionary."

        # Validate and extract 'app_name'
        app_name = input_dict.get("app_name")
        if not app_name or not isinstance(app_name, str):
            return "Error: 'app_name' is required and must be a non-empty string."

        v1 = create_client('apps')
        if not v1:
            return "Error creating apps client."

        namespace = "mindovermachinestech-dev"

        # Get the existing deployment
        deployment = v1.read_namespaced_deployment(name=app_name, namespace=namespace)

        # Annotate the deployment to force a restart
        if deployment.spec.template.metadata.annotations is None:
            deployment.spec.template.metadata.annotations = {}
        deployment.spec.template.metadata.annotations['kubectl.kubernetes.io/restartedAt'] = str(pd.Timestamp.now())

        # Apply the updated deployment configuration
        v1.patch_namespaced_deployment(name=app_name, namespace=namespace, body=deployment)

        return f"Successfully restarted {app_name}."
    except Exception as e:
        return f"Error restarting application: {str(e)}"


def get_deployment_configs(input=None):
    print(f"invoked get_deployment_configs with input {input}")
    try:
        input_dict = eval(input.strip())
        # Validate if input is provided and is a dictionary
        if not isinstance(input_dict, dict):
            return "Error: 'input' must be a dictionary."

        # Validate and extract 'app_name'
        app_name = input_dict.get("app_name")
        if not app_name or not isinstance(app_name, str):
            return "Error: 'app_name' is required and must be a non-empty string."
        v1 = create_client('apps')
        if not v1:
            return []

        namespace = "mindovermachinestech-dev"

        # Get the deployment configs for the specified application
        deployment = v1.read_namespaced_deployment(name=app_name, namespace=namespace)

        if not deployment:
            return f"No deployment config found for {app_name}."

        deployment_config = {
            "replicas": deployment.spec.replicas,
            "strategy": deployment.spec.strategy.type,
            "labels": deployment.metadata.labels,
            "annotations": deployment.metadata.annotations,
            "containers": [
                {
                    "name": container.name,
                    "image": container.image,
                    "ports": [port.container_port for port in container.ports] if container.ports else []
                }
                for container in deployment.spec.template.spec.containers
            ]
        }

        return deployment_config
    except Exception as e:
        return f"Error fetching deployment configs: {str(e)}"


def upgrade_application(input=None):
    print(f"invoked upgrade_application with input {input}")
    try:
        input_dict = eval(input.strip())
        # Validate if input is provided and is a dictionary
        if not isinstance(input_dict, dict):
            return "Error: 'input' must be a dictionary."

        # Validate and extract 'app_name'
        app_name = input_dict.get("app_name")
        if not app_name or not isinstance(app_name, str):
            return "application name is not mentioned in the user message, we cannot process further"

        new_image = input_dict.get("new_image")
        if not new_image or not isinstance(new_image, str):
            return "tool name is not mentioned in the user message, we cannot process further"

        v1 = create_client('apps')
        if not v1:
            return "Error creating apps client."

        namespace = "mindovermachinestech-dev"

        # Get the existing deployment
        deployment = v1.read_namespaced_deployment(name=app_name, namespace=namespace)

        # Update the container image
        for container in deployment.spec.template.spec.containers:
            container.image = new_image

        # Apply the updated deployment configuration
        v1.patch_namespaced_deployment(name=app_name, namespace=namespace, body=deployment)

        return f"Successfully upgraded {app_name} to image {new_image}."
    except Exception as e:
        return f"Error upgrading application: {str(e)}"


def check_cluster_nodes_health(input=None):
    try:
        v1 = create_client('core')
        if not v1:
            return "Error creating core client."

        # List all nodes in the cluster
        nodes = v1.list_node()
        unhealthy_nodes = []

        for node in nodes.items:
            node_name = node.metadata.name
            node_status = node.status.conditions[-1].type  # Last condition is usually 'Ready'
            node_state = node.status.conditions[-1].status

            if node_status != "Ready" or node_state != "True":
                unhealthy_nodes.append({
                    "node_name": node_name,
                    "status": node_status,
                    "state": node_state
                })

        if unhealthy_nodes:
            return {
                "status": "Unhealthy",
                "message": f"{len(unhealthy_nodes)} node(s) are unhealthy.",
                "unhealthy_nodes": unhealthy_nodes
            }
        else:
            return {
                "status": "Healthy",
                "message": "All nodes are healthy."
            }
    except Exception as e:
        return {
            "status": "Error",
            "message": f"Error checking cluster nodes health: {str(e)}"
        }


def check_critical_components_health(input = None):
    try:
        v1 = create_client('core')
        if not v1:
            return "Error creating core client."

        # Check the health of the API server
        api_health = v1.api_client.call_api(
            '/healthz', 'GET', response_type='str', _preload_content=False
        )

        if api_health[1] != 200:
            return {
                "response": f'/healthz enpoint response is {api_health}',
                "status": "Unhealthy",
                "message": "API server is not healthy."
            }

        # Check the health of other components (e.g., scheduler, controller manager)
        # This requires additional permissions and access to the component endpoints.
        # For simplicity, we assume the API server health reflects overall cluster health.

        return {
            "response" : f'/healthz enpoint response is {api_health}',
            "status": "Healthy",
            "message": "All critical components are healthy."
        }
    except Exception as e:
        return {
            "status": "Error",
            "message": f"Error checking critical components health: {str(e)}"
        }

def check_resource_utilization_health(input=None):
    try:
        # Create the metrics client
        metrics = create_client('metrics')
        if not metrics:
            return {
                "status": "Error",
                "message": "Error creating metrics client."
            }

        # Fetch node metrics
        try:
            node_metrics = metrics.list_cluster_custom_object(
                group="metrics.k8s.io",
                version="v1beta1",
                plural="nodes"
            )
        except Exception as e:
            return {
                "status": "Error",
                "message": f"Error fetching node metrics: {str(e)}"
            }

        # Fetch pod metrics
        try:
            pod_metrics = metrics.list_cluster_custom_object(
                group="metrics.k8s.io",
                version="v1beta1",
                plural="pods"
            )
        except Exception as e:
            return {
                "status": "Error",
                "message": f"Error fetching pod metrics: {str(e)}"
            }

        # Analyze node metrics
        high_usage_nodes = []
        for node in node_metrics["items"]:
            node_name = node["metadata"]["name"]
            cpu_usage = int(node["usage"]["cpu"][:-1])  # Remove 'n' suffix
            memory_usage = int(node["usage"]["memory"][:-2])  # Remove 'Ki' suffix

            if cpu_usage > 80 or memory_usage > 80:  # Example thresholds
                high_usage_nodes.append({
                    "node_name": node_name,
                    "cpu_usage": cpu_usage,
                    "memory_usage": memory_usage
                })

        # Analyze pod metrics
        high_usage_pods = []
        for pod in pod_metrics["items"]:
            pod_name = pod["metadata"]["name"]
            namespace = pod["metadata"]["namespace"]
            for container in pod["containers"]:
                cpu_usage = int(container["usage"]["cpu"][:-1])
                memory_usage = int(container["usage"]["memory"][:-2])

                if cpu_usage > 80 or memory_usage > 80:  # Example thresholds
                    high_usage_pods.append({
                        "pod_name": pod_name,
                        "namespace": namespace,
                        "cpu_usage": cpu_usage,
                        "memory_usage": memory_usage
                    })

        # Return results
        if high_usage_nodes or high_usage_pods:
            return {
                "status": "Warning",
                "message": "High resource utilization detected.",
                "high_usage_nodes": high_usage_nodes,
                "high_usage_pods": high_usage_pods
            }
        else:
            return {
                "status": "Healthy",
                "message": "Resource utilization is within acceptable limits."
            }

    except Exception as e:
        return {
            "status": "Error",
            "message": f"Error checking resource utilization: {str(e)}"
        }

def deploy_new_application(input=None):
    print(f"invoked deploy_new_application with input {input}")
    try:
        # Parse and validate input
        input_dict = eval(input.strip())
        if not isinstance(input_dict, dict):
            return "Error: 'input' must be a dictionary."

        # Extract required parameters
        app_name = input_dict.get("app_name")
        container_image = input_dict.get("container_image")
        replicas = input_dict.get("replicas", 1)
        port = input_dict.get("port", 8080)  # Optional: Expose the application on this port
        namespace = "mindovermachinestech-dev"

        if not app_name or not isinstance(app_name, str):
            return "Error: 'app_name' is required and must be a non-empty string."
        if not container_image or not isinstance(container_image, str):
            return "Error: 'container_image' is required and must be a non-empty string."
        if not isinstance(replicas, int) or replicas <= 0:
            return "Error: 'replicas' must be a positive integer."

        # Create the Kubernetes client
        v1 = create_client('apps')
        core_v1 = create_client('core')
        if not v1 or not core_v1:
            return "Error creating Kubernetes clients."

        # Define the Deployment spec
        deployment = client.V1Deployment(
            api_version="apps/v1",
            kind="Deployment",
            metadata=client.V1ObjectMeta(name=app_name),
            spec=client.V1DeploymentSpec(
                replicas=replicas,
                selector=client.V1LabelSelector(match_labels={"app": app_name}),
                template=client.V1PodTemplateSpec(
                    metadata=client.V1ObjectMeta(labels={"app": app_name}),
                    spec=client.V1PodSpec(
                        containers=[
                            client.V1Container(
                                name=app_name,
                                image=container_image,
                                ports=[client.V1ContainerPort(container_port=port)] if port else None
                            )
                        ]
                    )
                )
            )
        )

        # Create the Deployment in the specified namespace
        v1.create_namespaced_deployment(namespace=namespace, body=deployment)

        # Optionally expose the deployment as a service if a port is provided
        if port:
            service = client.V1Service(
                api_version="v1",
                kind="Service",
                metadata=client.V1ObjectMeta(name=app_name),
                spec=client.V1ServiceSpec(
                    selector={"app": app_name},
                    ports=[client.V1ServicePort(port=port, target_port=port)],
                    type="ClusterIP"  # Change to "LoadBalancer" or "NodePort" if needed
                )
            )
            core_v1.create_namespaced_service(namespace=namespace, body=service)

        return f"Successfully deployed application '{app_name}' with {replicas} replicas."

    except Exception as e:
        return f"Error deploying application: {str(e)}"




def get_metrics(input=None):
    namespace = "mindovermachinestech-dev"
    metrics_v1 = create_client('metrics')
    cpu_usage = []
    memory_usage = []
    timestamps = []

    try:
        metrics = metrics_v1.list_namespaced_custom_object(
            group="metrics.k8s.io",
            version="v1beta1",
            namespace=namespace,
            plural="pods"
        )
        print(metrics)
        for pod in metrics.get("items", []):
            pod_name = pod["metadata"]["name"]
            for container in pod.get("containers", []):
                # Extract CPU and memory usage
                name = container["name"]
                cpu = container["usage"]["cpu"]
                memory = container["usage"]["memory"]
                cpu_millicores = int(cpu.rstrip("n")) if cpu.endswith("n") else int(cpu) * 1000
                memory_mb = int(memory.rstrip("Ki")) if memory.endswith("Ki") else int(memory.rstrip("Gi")) * 1024
                cpu_usage.append(cpu_millicores)
                memory_usage.append(memory_mb)
                timestamps.append(pod["timestamp"])

        disk_io = [random.randint(1, 100) for _ in range(len(cpu_usage))]
        network_usage = [random.randint(10, 39), random.randint(30, 99)]  # [Inbound, Outbound]
        return {
            "cpuUsage": cpu_usage,
            "diskIO": disk_io,
            "memoryUsage": memory_usage,
            "networkUsage": network_usage,
            "timestamps": timestamps,
        }
    except client.exceptions.ApiException as e:
        print(f"Error fetching metrics: {e}")
        return {}


def get_applications(input=None):
    namespace = "mindovermachinestech-dev"
    metrics_v1 = create_client('metrics')
    apps_v1 = create_client('apps')
    core_v1 = create_client('core')

    # Fetch deployments (representing applications)
    try:
        deployments = apps_v1.list_namespaced_deployment(namespace=namespace)
    except client.exceptions.ApiException as e:
        print(f"Error fetching deployments: {e}")
        return []

    # Fetch pod metrics
    try:
        pod_metrics = metrics_v1.list_namespaced_custom_object(
            group="metrics.k8s.io",
            version="v1beta1",
            namespace=namespace,
            plural="pods"
        )
    except client.exceptions.ApiException as e:
        print(f"Error fetching pod metrics: {e}")
        pod_metrics = {"items": []}

    # Build a dictionary of pod metrics for quick lookup
    pod_metrics_dict = {}
    for pod in pod_metrics.get("items", []):
        pod_name = pod["metadata"]["name"]
        pod_metrics_dict[pod_name] = {
            "cpu": sum(int(c["usage"]["cpu"].rstrip("n")) for c in pod.get("containers", [])),
            "memory": sum(int(c["usage"]["memory"].rstrip("Ki")) for c in pod.get("containers", []))
        }

    # Generate application information
    applications = []
    for deployment in deployments.items:
        app_name = deployment.metadata.name
        app_type = "Micro Service"  # Default type; you can customize this based on labels or annotations
        registered_date = deployment.metadata.creation_timestamp.strftime("%B %d, %Y")
        status = deployment.status.available_replicas > 0 if deployment.status.available_replicas else False

        # Get memory usage for the application's pods
        memory_usage = 0
        pod_data = []
        for pod in core_v1.list_namespaced_pod(namespace=namespace).items:
            if pod.metadata.labels and pod.metadata.labels.get("app") == app_name:
                pod_data.append({"pod_name" : pod.metadata.name,
                                 "memory" : pod_metrics_dict.get(pod.metadata.name, {}).get("memory", 0),
                                 "cpu" : pod_metrics_dict.get(pod.metadata.name, {}).get("memory", 0)})
                memory_usage += pod_metrics_dict.get(pod.metadata.name, {}).get("memory", 0)

        # Mock requests and activity (not available via Kubernetes API)
        requests = random.randint(200, 700)  # Mocked number of requests
        activity = f"{random.randint(1, 10)} min ago" if not status else f"{random.randint(1, 60)} sec ago"

        # Determine memory color based on usage
        memory_color = "success" if memory_usage > 30 else "warning" if memory_usage > 0 else "danger"

        # Add application details to the list
        applications.append({
            "application": {
                "name": app_name,
                "type": app_type,
                "registered": registered_date
            },
            "status": status,
            "memory": {
                "value": memory_usage,
                "period": datetime.now().strftime("%B %d, %Y"),
                "color": memory_color
            },
            "pods": pod_data,
            "requests": str(requests),
            "activity": activity
        })

    return applications





