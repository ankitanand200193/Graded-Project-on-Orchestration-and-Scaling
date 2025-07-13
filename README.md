# Sample MERN with Microservices



For `helloService`, create `.env` file with the content:
```bash
PORT=3001
```

For `profileService`, create `.env` file with the content:
```bash
PORT=3002
MONGO_URL="specifyYourMongoURLHereWithDatabaseNameInTheEnd"
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

## Set Up AWS CLI and Boto3:
### Install AWS CLI and configure it with AWS credentials.
    1. Download and install the install following the link https://awscli.amazonaws.com/AWSCLIV2.msi. Follow the instructions
    2. Verify by ```aws --version```
       
#### Configuring AWS.
    1. Requirement Access KeyID, Secret Access Key, Region name, Output format.
       To get Acess KeyID & Secret Access key : ```Login to AWS Console → IAM → Users → Select your user → Security Credentials → Create access key → Choose "CLI" use case → Copy Access Key ID & Secret Access Key.```
    2. On the terminal type ```aws configure``` and provide the details gathered in point #1 
    
### Install python
   
     1. python --version
     2. sudo apt update
     3. sudo apt install python3 python3-pip
    
### Install Boto
      1. pip install boto3
      2. To verify : python -c "import boto3; print(boto3.__version__)"


    
    











Note: This will run the frontend in the development server. To run in production, build the application by running the command `npm run build`
