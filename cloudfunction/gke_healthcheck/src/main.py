import os
import slackweb
import google.auth
import kubernetes.client

from google.cloud.container_v1 import ClusterManagerClient
from kubernetes.client.exceptions import ApiException

GKE_CONSOLE_LINK = os.environ.get("GKE_CONSOLE_LINK")
SLACK_WEBHOOK = os.environ.get("SLACK_WEBHOOK")
ENV = os.environ.get("ENV")
LOCATION = "asia-northeast1"
PROJECT_ID = ""
GKE_CLUSTER_NAME = ""

def notify_slack_abnormal(pod_name, values):
    slack = slackweb.Slack(url=SLACK_WEBHOOK)
    attachments = [
        {
            "author_name": "GKE health checker",
            "title": "The state of the pod is abnormal",
            "title_link": GKE_CONSOLE_LINK,
            "color": "danger",
            "fields": [
                {
                    "title": "Pod name",
                    "value": pod_name,
                    "short": False
                },
                {
                    "title": "message",
                    "value": values.message,
                    "short": False
                },
                {
                    "title": "reason",
                    "value": values.reason,
                    "short": False
                }
            ],
            "footer": "Slack API",
            "footer_icon": "https://platform.slack-edge.com/img/default_application_icon.png",
        }
    ]
    slack.notify(attachments=attachments)


def notify_slack_normal():
    slack = slackweb.Slack(url=SLACK_WEBHOOK)
    attachments = [
        {
            "author_name": "GKE health checker",
            "title": "The state of the pod is normal",
            "title_link": GKE_CONSOLE_LINK,
            "color": "good",
            "footer": "Slack API",
            "footer_icon": "https://platform.slack-edge.com/img/default_application_icon.png",
        }
    ]
    slack.notify(attachments=attachments)


def _get_cluster():
    credentials, project = google.auth.default(
        scopes=["https://www.googleapis.com/auth/cloud-platform"]
    )

    credentials.refresh(google.auth.transport.requests.Request())
    client = ClusterManagerClient(credentials=credentials)

    parent = f"projects/{PROJECT_ID}/locations/{LOCATION}/{GKE_CLUSTER_NAME}"
    response = client.list_clusters(parent=parent)

    clusters = [c for c in response.clusters]
    if len(clusters) == 0:
        raise Exception("Active Cluster Not Found")

    return clusters[0], credentials


def run(request, context=None):

    # configure client
    cluster, credentials = _get_cluster()
    configuration = kubernetes.client.Configuration()
    configuration.host = f"https://{cluster.endpoint}:443"
    configuration.verify_ssl = False
    configuration.api_key = {"authorization": f"Bearer {credentials.token}"}
    kubernetes.client.Configuration.set_default(configuration)

    # get list_namespaced_pod
    namespace = "airflow-v2"
    v1 = kubernetes.client.CoreV1Api()
    res = v1.list_namespaced_pod(namespace)

    for i in res.items:
        print("%s\t%s\t%s" % (i.status.phase, i.metadata.namespace, i.metadata.name))

        # 正常に動いてる場合はスルー
        if i.status.phase == "Running":
            continue

        # すでに使用されてないpodは掃除
        elif i.status.phase == "Failed" and (i.status.reason == "Terminated" or i.status.reason == "NodeShutdown"):
            try:
                v1.delete_namespaced_pod(i.metadata.name, i.metadata.namespace)
            except ApiException as e:
                raise Exception("Exception when calling CoreV1Api->delete_namespaced_pod: %s\n" % e)

        # その他は異常と判断してslackに通知
        else:
            for j in i.status.init_container_statuses:
                if j.state.waiting.reason != "PodInitializing":
                    notify_slack_abnormal(i.metadata.name, j.state.waiting)

    return "Success"
