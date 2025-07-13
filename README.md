# Sample MERN with Microservices



For `helloService`, create `.env` file with the content:
```bash
PORT=3001
```

For `profileService`, create `.env` file with the content:
```bash
PORT=3002
MONGO_URL="specifyYourMongoURLHereWithDatabaseNameInTheEndOk"
```

Finally install packages in both the services by running the command `npm install`.

<br/>
For frontend, you have to install and start the frontend server:

```bash
cd frontend
npm install
npm start
```
---------------------------------------------------------------------------------------------------------------------------------------------------------

# Ankit Documentation

## Step 1: Set Up AWS CLI and Boto3:
### Install AWS CLI and configure it with AWS credentials.
1. Download and install the installer following the link https://awscli.amazonaws.com/AWSCLIV2.msi. Follow the instructions
2. Verify by ***aws --version***
       
#### Configuring AWS.
1. Requirement Access KeyID, Secret Access Key, Region name, Output format.
       To get Acess KeyID & Secret Access key : Login to AWS Console → IAM → Users → Select your user → Security Credentials → Create access key → Choose "CLI" use case → Copy Access Key ID & Secret Access Key.
2. On the terminal type ***aws configure*** and provide the details gathered in point #1 
    
### Install python
   
1. python --version
2. sudo apt update
3. sudo apt install python3 python3-pip
    
### Install Boto
1. pip install boto3
2. To verify : python -c "import boto3; print(boto3.__version__)"


## Step 2: Prepare the MERN Application

1. Create Dockerfile in helloservice, profile service and frontend folders

2. Create 3 repos in ECR and name them in their service name.

3. Build the images using *docker build -t complete-AWS-repo-name-url : tag* like ```docker build -t  975050024946.dkr.ecr.ap-south-1.amazonaws.com/ankitanand/backendhelloservice:latest .```

4. Authenticate docker to push images to  ECR

Pre-requisite: AWS configured ; IAM user with ECR permissions ; Docker installed
   
   ```aws ecr get-login-password --region **ap-south-1** | docker login --username AWS --password-stdin **975050024946.dkr.ecr.ap-south-1.amazonaws.com**```   

Note: Only highlighted should be adjust as per the user.
   
Verify : ```docker info | grep -i ecr```

5. Push images to ECR by : ```docker push 975050024946.dkr.ecr.ap-south-1.amazonaws.com/ankitanand/backendhelloservice:latest```

## Step 3: Create Github repo of the source code

1. Create the repo.
2. Git clone the repo and then git push all the content to the repo.

## Step 4: Continuous Integration with Jenkins 

#### EC2 pre-requisites
1.  t2.medium (at least 2 GB RAM)
2.  Security Group: 
          Allow SSH (port 22) – your IP 
          Allow HTTP (port 8080) – your IP or 0.0.0.0/0 (for Jenkins access)

#### Jenkins Setup :
1. Install Jenkins
   
```
# run the following at once
sudo apt update
sudo apt upgrade -y
sudo apt install openjdk-17-jre -y
curl -fsSL https://pkg.jenkins.io/debian-stable/jenkins.io-2023.key | sudo tee \
/usr/share/keyrings/jenkins-keyring.asc > /dev/null
 echo deb [signed-by=/usr/share/keyrings/jenkins-keyring.asc] \
https://pkg.jenkins.io/debian-stable binary/ | sudo tee \
/etc/apt/sources.list.d/jenkins.list > /dev/null
sudo apt-get update
sudo apt-get install jenkins -y
sudo systemctl enable jenkins
sudo systemctl start jenkins

```

2. Access Jenkins here : http://EC2-Public-IP:8080

3. Unlock the passoword : ``` sudo cat /var/lib/jenkins/secrets/initialAdminPassword ```

4. **Docker installation:**
   ```
   sudo apt-get update
   sudo apt-get install -y docker.io
   sudo systemctl enable --now docker
   ```
5. Install Plugins:  Go to Manage Jenkins → Plugins → Available and install: ✅ Docker Pipeline, ✅ Amazon ECR, ✅ GitHub Integration / Git Plugin, ✅ Pipeline

6. Install AWS cli (ubuntu):
```
sudo apt update
sudo apt install -y unzip curl
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install
```
7. AWS configure

8. Configure AWS Credentials in Jenkins: Navigate to Manage Jenkins → Credentials → System → Global Credentials → Add Credentials, then set Kind to *Username with password*, Username to *AWS*, Password to the output of ``aws ecr get-login-password```, and ID to *aws-ecr-credentials*.

9. Github webhook setup:

| Field            | Value                                                                    |
| ---------------- | ------------------------------------------------------------------------ |
| **Payload URL**  | `http://<your-jenkins-url>/github-webhook/`                              |
| **Content type** | `application/json`                                                       |
| **Secret**       | *(optional)* Add a secret if you want to secure communication            |
| **Events**       | Choose “**Just the push event**” (or also enable Pull request if needed) |

You can test the setup by hitting on recent deliveries. 

Note : **<your-jenkins-url>** it should not include your pipeline name. **github-webhook** is constant component.

8. 







    
    











Note: This will run the frontend in the development server. To run in production, build the application by running the command `npm run build`
