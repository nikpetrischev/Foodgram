# build env
#FROM node:13.12.0-alpine as build
#WORKDIR /app
#COPY package*.json ./
#RUN npm install --legacy-peer-deps
#COPY . ./
#RUN npm run build
#CMD cp -r build result_build
FROM node:18
WORKDIR /app

COPY package.json package.json
COPY package-lock.json package-lock.json

RUN npm ci

COPY . .
RUN npm run build
RUN npm install --global http-server

CMD ["npx", "-y", "http-server", "-p", "8000", "/app/build"]