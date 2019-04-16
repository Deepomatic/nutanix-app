FROM node:10.15.3-alpine as node

WORKDIR /app

COPY js/package.json /app
COPY js/yarn.lock /app

RUN yarn install

COPY js/ /app/
RUN yarn build


FROM nginx:1.15.8-alpine

RUN apk update && apk add nginx-mod-rtmp
RUN mkdir -p /url-feed/www/hls
RUN mkdir -p /run/nginx  # otherwise nginx doesn't run

COPY nginx/nginx.conf /etc/nginx/nginx.conf
COPY --from=node /app/dist/ /url-feed/www/

CMD ["/usr/sbin/nginx", "-g", "daemon off;"]
