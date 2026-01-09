FROM node:22-bullseye AS dev

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
ARG VITE_API_HOST=/master_topas-portal_backend

ADD ./ /root/vue-frontend
WORKDIR /root/vue-frontend
RUN NODE_OPTIONS="--max-old-space-size=4096" npm run build -- --outDir /root/dist

RUN echo "NODE_ENV: $NODE_ENV"
RUN echo "VITE_API_HOST: $VITE_API_HOST"

WORKDIR /root
RUN rm -rf /root/vue-frontend

CMD [ "sh", "-c", "http-server dist --port ${CI_FRONTEND_PORT:-3834}" ]



