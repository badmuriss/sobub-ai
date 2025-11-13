FROM nginx:alpine

# Install openssl for certificate generation
RUN apk add --no-cache openssl

# Remove default nginx config
RUN rm /etc/nginx/nginx.conf

# Copy custom nginx config
COPY conf/nginx.conf /etc/nginx/nginx.conf

# Copy entrypoint script
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# Expose HTTP and HTTPS ports
EXPOSE 80 443

# Use custom entrypoint that generates SSL certs if needed
ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["nginx", "-g", "daemon off;"]
