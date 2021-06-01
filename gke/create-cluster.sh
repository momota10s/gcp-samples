gcloud container clusters create hello-web \
--machine-type=n1-standard-1 \
--num-nodes=1 \
--disk-size=100 \
--region=asia-northeast1 \
--preemptible \
--scopes=cloud-platform \
--enable-cloud-logging \
--enable-stackdriver-kubernetes \
--image-type "COS"