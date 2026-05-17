FROM nginx:alpine

RUN rm -rf /usr/share/nginx/html/*
COPY nginx-https.conf /etc/nginx/conf.d/default.conf

EXPOSE 80 443

CMD ["nginx", "-g", "daemon off;"]