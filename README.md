# pipeline-framework-demo
 
Environment Setup

1. install docker 
2. docker swarm init
3. docker network create pulsarnet --driver overlay --attachable
4. cd to middleware and run command
    docker build -f Dockerfile.pulsar -t synergy/pulsar:3.3.0 .
    this will build local image to docker images
5. bring up pulsar stand alone
    docker compose -f compose-standalone.yaml up -d
6. change directory to pipeline-apis
7. make sure you have python install and pip available
8. run following command to build virual environment
    python3 -m venv .venv
9. activate virual envirment. make sure to use activation process as per your OS. below is unix/macos format
    source .venv/bin/activate 
10. install dependencies
    pip install -r requirements.txt
11. find you IP address of host
12. change directory to scripts
13. edit config_loadbalancer.py and change LB IP address to your host IP address
14. update load balancer 
    python config_loadbalancer.py
15. run commands to see if any function configured
    python deploy_functions.py http://localhost:8088/admin get -t public -n default
16. run script to deploy the workflow
    python deploy_functions.py http://localhost:8088/admin deploy -w workflow.yaml -p MessageHttpFn.py
17. change directory to pipeline-apis
18. run api
    python main.py 
19. open browser navigate to - http://localhost:9000/ui/index.html
20. enter latitude and longitude and click send and wait for pipeline to finsh and get result on browser screen


Thanks a lot. contact me if you face issue.


