FROM node:18-alpine


# Working directory be app
WORKDIR /usr/src/app

COPY package*.json ./

###  Installing dependencies

RUN npm install 
# copy local files to app folder

COPY . .

EXPOSE 3000

CMD ["npm","start"]
