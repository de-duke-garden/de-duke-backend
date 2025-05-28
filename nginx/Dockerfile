FROM nginx:latest

# Copy the startup script
COPY startup.sh /startup.sh

# Make the script executable
RUN chmod +x /startup.sh

# Set the script as the container's entrypoint
ENTRYPOINT ["/startup.sh"]