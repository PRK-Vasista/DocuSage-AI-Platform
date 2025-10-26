# Use a Node.js image as the base environment
FROM node:18-alpine

# Set the working directory inside the container
WORKDIR /app

# Copy the package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy the rest of the application code
COPY . .

# Expose the port the React app runs on
EXPOSE 3000

# Command to start the application (starts development server)
CMD ["npm", "start"]
