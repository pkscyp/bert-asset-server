# BERT ASSET SERVER 
**Primitive version**
 
Environment Setup
 make you to have python3 installed. this version 1 does not requires docker
 **git clone repository**
 create python virtual environment
 **cd to bert-asset-server**
 **python3 -m venv .venv**
 activate virtual environment
 **.\venv\bin\activate**
 **pip3 install -r requirements.txt**
 to print up server
 **cd pwa-api**
 run command
 **python3 main.py**
 open a browser and navigate to** http://localhost:9000/ui/index.html**

it will ask **permission to access geolocation server** , please grant access
 **click open camera** , it will ask for** permission to access camera**, please do grant the permission
 click **take photo**
 enter **user id in input box** , avoid using spaces in id
 click **register** and wait for message at bottom apearing accepted
 againt **open the camera by click button**
**take photo**
 and click check-in
 you should see **Accepted.**

 continue to play with various face. 
 if photo has two faces it will be **rejected**
 
 
