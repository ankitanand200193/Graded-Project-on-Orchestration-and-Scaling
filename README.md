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
.env variable for frontend:

Port: 3000
REACT_APP_PROFILE_API: 
REACT_APP_HELLO_API:

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

3. Unlock the password : ``` sudo cat /var/lib/jenkins/secrets/initialAdminPassword ```

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

10. Write the Jenkinsfile in the SCM and build the pipline.Enter the github url, main branch name, select the credentials.
11. Go to the github and make a commit to see the pipeline being triggered.

## Step 5-9 : Building infrastructure with Boto3

#### Check-list before provisioning infrastructure:

1. VPC and subnets should be created in public and subnet should be allowed assigning IPs to the EC2.
2. Security group should have port open : 3000(frontend), 3001(helloService), 3002(profileService), 22(SSH), 80(nginx & load balancer)
3. Ensure route table should is attached to the internet gateway.
4. Ensure target group health check path is / or /health.
5. Create a ECR role so that the EC2 can access the ECR service
6. Keep handy an AMI, key-pair and MONG_URL for the ease of provising the infrastructure.
7. Create a destroy.py file also to turndown all the resources.
    

#### Testing the infrastructure:

1. Check the VPC, security group, subnets and route table on the console.
2. SSH into the frontend and backend ec2 to check the ECR images being pulled 
3. Check the ALB and ensure the rule and listener are correct. Target groups are healthy.
4. Hit the frontend IP:3000 to access the services.
5. Hit the backend IP:3001/3002 to check the hello and profile services are accessible.

#### Configuring DNS for frontend:
##### 1. Install Nginx

```bash
sudo apt update -y && sudo apt install nginx -y
sudo systemctl enable nginx --now
```

##### 2. Open Ports

* **AWS Security Group:** Allow HTTP (80) & HTTPS (443).
* **Firewall:** `sudo ufw allow 'Nginx Full'`

##### 3. Point Domain to EC2

* Add **A Record:** `ankitanand.sbs → <Frontend_EC2_PUBLIC_IP>`
* Test: `ping ankitanand.sbs`

##### 4. Configure Nginx for Frontend

```bash
sudo nano /etc/nginx/sites-available/ankitanand.sbs
```

**Config:**

```nginx
server {
    listen 80;
    server_name ankitanand.sbs;
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

Enable & reload:

```bash
sudo ln -s /etc/nginx/sites-available/ankitanand.sbs /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

## Step 10: EKS cluster deployement:

##### **1. Pre-Requisites**

* **IAM Permissions:** User/role must have EKS, EC2, VPC, and IAM privileges.
* **AWS CLI Installed:**

  ```bash
  aws --version
  ```
* **kubectl Installed:**

  ```bash
  kubectl version --client
  ```
* **Key Pair:** Create an EC2 key pair for SSH access if needed.

---

## **2. Create an EKS Cluster (AWS Console)**

### **2.1 Navigate to EKS**

* Go to **AWS Console → EKS → Add cluster → Create.**

### **2.2 Configure Cluster**

* **Cluster name:** `mern-cluster` (or your desired name).
* **Kubernetes version:** Use the default/latest.
* **Role:** Create/assign a new IAM role `EKS-ClusterRole` with `AmazonEKSClusterPolicy`.

Click **Next**.

### **2.3 Networking**

* **VPC:** Choose existing or create a new VPC.
* **Subnets:** Select at least two subnets (e.g., `ap-south-1a` & `ap-south-1b`).
* **Security group:** Default or custom.
* **Cluster endpoint access:** Public and private (recommended).

Click **Next → Create.**

---

## **3. Add Node Group (Worker Nodes)**

### **3.1 Open Node Group Creation**

* Go to **EKS Console → Clusters → mern-cluster → Compute → Add Node Group**.

### **3.2 Configure Node Group**

* **Name:** `mern-node-group`.
* **Node IAM Role:** Create or use `EKS-Node-Role` with `AmazonEKSWorkerNodePolicy`, `AmazonEC2ContainerRegistryReadOnly`, and `AmazonEKS_CNI_Policy`.

Click **Next.**

### **3.3 Compute Settings**

* **Instance type:** `t3.medium` (or higher).
* **Scaling:** Desired = 2, Min = 1, Max = 3.
* **Disk size:** 20 GiB.

Click **Next.**

### **3.4 Networking**

* Select the **2 subnets** created above.

Click **Next → Create.**

---

## **4. Configure kubectl on your local machine**

### **4.1 Update kubeconfig**

Run:

```bash
aws eks --region ap-south-1 update-kubeconfig --name mern-cluster
```

Expected output:

```
Updated context arn:aws:eks:ap-south-1:xxx:cluster/mern-cluster in /home/user/.kube/config
```

### **4.2 Verify Connection**

```bash
kubectl get nodes
```

Expected output:

```
NAME                                        STATUS   ROLES    AGE   VERSION
ip-10-0-1-xx.ap-south-1.compute.internal    Ready    <none>   2m    v1.29.x
```

---


       

## Step 11 : Setting up Cloudwatch Alarm
##### Steps to Set Up a CloudWatch Alarm

1. **Navigate to CloudWatch Console**

   * Go to **CloudWatch** from AWS Management Console.

2. **Create a New Alarm**

   * Click **Alarms** > **All alarms** > **Create alarm**.

3. **Select a Metric**

   * Choose **Select metric**.
   * Browse **EC2 > Per-Instance Metrics > CPUUtilization** (or desired metric).
   * Select the instance and click **Select metric**.

4. **Define Conditions**

   * Set threshold (e.g., CPU > 2%).
   * Define evaluation period (e.g., 5 data points of 1 minute each).

5. **Configure Notifications**

   * Choose **Create new SNS topic** or existing one.
   * Add email endpoint (confirm subscription via email).

6. **Name and Create**

   * Give the alarm a name (e.g., `HighCPUAlarm`).
   * Click **Create alarm**.

7. **Verify Alarm**

   * Alarm appears under **CloudWatch > Alarms** with its status (OK/ALARM).
  
## Step 12: MongoDB Snapshot Backup with AWS Lambda (pymongo + bson)

### Step-by-Step Setup

#### Create IAM Role for Lambda

1. Go to **IAM > Roles > Create Role**
2. Choose: **Lambda**
3. Attach policies:

   * `AWSLambdaBasicExecutionRole`
   * `AmazonS3FullAccess`
4. Name the role: `lambda-mongo-backup-role`

---

#### Create Lambda Function

1. Go to **Lambda > Create Function**
2. Runtime: **Python 3.12**
3. Permissions: Use existing role → `lambda-mongo-backup-role`

---

#### Prepare Local Code Folder

1. Create a folder named `mongo_backup_lambda`
2. Add your backup script `lambda_function.py`
3. Install dependencies locally:

   ```bash
   pip install pymongo bson -t .
   ```
4. Zip everything:

   ```bash
   zip -r mongo_backup_lambda.zip .
   ```

---

#### Upload to Lambda

1. In Lambda > Code Source:

   * Click **Upload from > .zip file**
   * Upload `mongo_backup_lambda.zip`
2. Set Handler to:

   ```
   lambda_function.lambda_handler
   ```

---

#### Set Environment Variables

Go to **Lambda > Configuration > Environment Variables**, add:

| Key         | Value                      |
| ----------- | -------------------------- |
| `MONGO_URI` | Your MongoDB Atlas URI with db name     |
| `S3_BUCKET` | Your target S3 bucket name |

---

#### 6⃣ Test the Lambda Function

1. Use a blank test event:
2. Run the function
3. Check S3 bucket for backup files

   * Format:

     ```
     mongodb_backup/{collection_name}/{timestamp}.bson
     ```

---









    
    











Note: This will run the frontend in the development server. To run in production, build the application by running the command `npm run build`
