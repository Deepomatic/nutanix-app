1. Build the nginx docker image and upload it to aws ecr
    docker build -t nginx:0.1 -f Dockerfile.nginx .
    docker tag <img> 770301640873.dkr.ecr.us-west-2.amazonaws.com/urlfeed/nginx:0.1
    docker push 770301640873.dkr.ecr.us-west-2.amazonaws.com/urlfeed/nginx:0.1


2. Build the urlfeed docker image and upload it to aws ecr
    docker build -t ufeed:0.1 -f Dockerfile.urlfeed .
    docker tag <img>  770301640873.dkr.ecr.us-west-2.amazonaws.com/urlfeed/app:0.3
    docker push 770301640873.dkr.ecr.us-west-2.amazonaws.com/urlfeed/app:0.3

3. Find a k8s cluster and deploy the app.
    kubectl apply -f urlfeed.yaml

4. Find the node ip of the pod running nginx and point browser to the following url
    http://<node_ip_of_nginx>:30090
