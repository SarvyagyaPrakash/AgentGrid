FROM node:18-alpine

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

ENV PORT 3333
EXPOSE 3333

CMD ["npm", "run", "dev", "--", "-p", "3333"]
