FROM node:14.18.3-bullseye AS dev

ARG DEBIAN_FRONTEND=noninteractive

####################
# Vue dependencies #
####################

ADD ./package.json /root/vue-frontend/
WORKDIR /root/vue-frontend
RUN npm install
RUN npm install -g http-server

#####################
# Vue build package #
#####################

ARG NODE_ENV=production
ARG VUE_APP_API_HOST=/master_topas_portal_backend

ADD ./ /root/vue-frontend
WORKDIR /root/vue-frontend
RUN npm run build

RUN echo "NODE_ENV: $NODE_ENV"
RUN echo "VUE_APP_API_HOST: $VUE_APP_API_HOST"

WORKDIR /root
CMD [ "http-server", "dist", "--port", "3834" ]



