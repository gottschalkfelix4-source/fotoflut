FROM node:24-alpine
WORKDIR /app
COPY apps/api/package.json apps/api/
RUN cd apps/api && npm install --omit=dev --no-audit --no-fund
COPY apps/api/src apps/api/src
ENV PORT=8080
EXPOSE 8080
USER node
CMD ["node", "apps/api/src/server.ts"]
