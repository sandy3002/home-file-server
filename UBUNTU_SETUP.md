# Ubuntu Server Setup with Cloudflare Tunnel

Complete step-by-step guide to deploy your Home File Server on Ubuntu with Cloudflare Tunnel for internet access via mobile hotspot.

---

## Prerequisites

- Ubuntu laptop (18.04 or newer)
- Internet connection (mobile hotspot is fine!)
- Domain name (you mentioned you have one)
- Cloudflare account (free tier works)

---

## Part 1: Ubuntu System Setup

### 1. Update System

```bash
sudo apt update
sudo apt upgrade -y
```

### 2. Install Required System Packages

```bash
# Install Python 3, pip, and development tools
sudo apt install -y python3 python3-pip python3-venv git curl

# Install MongoDB
wget -qO - https://www.mongodb.org/static/pgp/server-7.0.asc | sudo apt-key add -
echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu $(lsb_release -cs)/mongodb-org/7.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-7.0.list
sudo apt update
sudo apt install -y mongodb-org

# Start and enable MongoDB
sudo systemctl start mongod
sudo systemctl enable mongod
sudo systemctl status mongod  # Should show "active (running)"
```

### 3. Clone Your Project

```bash
# Navigate to home directory
cd ~

# Clone or copy your project
# If using git:
git clone <your-repo-url> home-file-server
# OR copy files manually

cd home-file-server
```

---

## Part 2: Application Setup

### 1. Create Python Virtual Environment

```bash
cd ~/home-file-server
python3 -m venv venv
source venv/bin/activate
```

### 2. Install Python Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Create Data Directory

```bash
# Create directory for file storage
mkdir -p ~/fileserver-data
chmod 755 ~/fileserver-data
```

### 4. Configure Environment Variables

```bash
# Copy the example env file
cp .env.example .env

# Generate a secure secret key
python3 -c "import secrets; print(secrets.token_hex(32))"
# Copy the output

# Edit the .env file
nano .env
```

Update the following in `.env`:

```bash
SECRET_KEY=<paste-the-generated-secret-key>
MONGODB_URI=mongodb://localhost:27017/
UPLOAD_FOLDER=/home/yourusername/fileserver-data
FLASK_ENV=production
HOST=127.0.0.1
PORT=8080
MAX_CONTENT_LENGTH=10737418240
```

Save with `Ctrl+O`, then `Ctrl+X`.

### 5. Test the Application

```bash
# Make sure virtual environment is activated
source venv/bin/activate

# Run the app
python app.py
```

Open another terminal and test:

```bash
curl http://localhost:8080
```

If you see HTML output, it's working! Press `Ctrl+C` to stop the app.

---

## Part 3: Cloudflare Tunnel Setup

### 1. Add Domain to Cloudflare

1. Go to [cloudflare.com](https://cloudflare.com) and sign up/login
2. Click "Add a Site" and enter your domain name
3. Select the Free plan
4. Copy the nameservers Cloudflare provides
5. Go to your domain registrar (GoDaddy, Namecheap, etc.) and update nameservers
6. Wait for DNS propagation (can take up to 48 hours, usually faster)

### 2. Install Cloudflared on Ubuntu

```bash
# Download cloudflared
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb

# Install it
sudo dpkg -i cloudflared-linux-amd64.deb

# Verify installation
cloudflared --version
```

### 3. Authenticate with Cloudflare

```bash
cloudflared tunnel login
```

This will open a browser window. Log in to Cloudflare and select your domain. The credentials will be saved automatically.

### 4. Create the Tunnel

```bash
# Create a tunnel named "home-file-server"
cloudflared tunnel create home-file-server

# Note the tunnel ID that appears (format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx)
```

### 5. Configure the Tunnel

```bash
# Create cloudflared config directory
mkdir -p ~/.cloudflared

# Copy the template and edit it
cp cloudflared-config.yml ~/.cloudflared/config.yml
nano ~/.cloudflared/config.yml
```

Update the config with your actual values:

```yaml
tunnel: <YOUR-TUNNEL-ID-FROM-STEP-4>
credentials-file: /home/yourusername/.cloudflared/<YOUR-TUNNEL-ID>.json

ingress:
  - hostname: server.yourdomain.com
    service: http://localhost:8080

  - service: http_status:404
```

Replace:

- `<YOUR-TUNNEL-ID-FROM-STEP-4>` with actual tunnel ID
- `yourusername` with your Ubuntu username
- `server.yourdomain.com` with your actual subdomain

Save with `Ctrl+O`, then `Ctrl+X`.

### 6. Route DNS to Your Tunnel

```bash
# Create DNS record for your subdomain
cloudflared tunnel route dns home-file-server server.yourdomain.com
```

### 7. Test the Tunnel

```bash
# In one terminal, make sure your Flask app is running:
cd ~/home-file-server
source venv/bin/activate
python app.py

# In another terminal, start the tunnel:
cloudflared tunnel run home-file-server
```

Wait a minute, then visit `https://server.yourdomain.com` in your browser. You should see your login page!

If it works, press `Ctrl+C` in both terminals.

---

## Part 4: Setup Auto-Start Services

### 1. Create Log Directory

```bash
sudo mkdir -p /var/log/home-file-server
sudo chown yourusername:yourusername /var/log/home-file-server
```

### 2. Setup Flask App Service

```bash
# Edit the service file with your username
nano home-file-server.service
```

Replace all occurrences of `yourusername` with your actual Ubuntu username.

```bash
# Copy service file
sudo cp home-file-server.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable and start the service
sudo systemctl enable home-file-server
sudo systemctl start home-file-server

# Check status
sudo systemctl status home-file-server
```

Should show "active (running)".

### 3. Setup Cloudflare Tunnel Service

```bash
# Install cloudflared as a service
sudo cloudflared service install

# Start the service
sudo systemctl start cloudflared
sudo systemctl enable cloudflared

# Check status
sudo systemctl status cloudflared
```

---

## Part 5: Verification & Testing

### 1. Check Services are Running

```bash
# Check Flask app
sudo systemctl status home-file-server

# Check Cloudflare tunnel
sudo systemctl status cloudflared

# Check MongoDB
sudo systemctl status mongod
```

All should show "active (running)".

### 2. Check Logs

```bash
# Flask app logs
tail -f /var/log/home-file-server/output.log

# Cloudflare tunnel logs
sudo journalctl -u cloudflared -f
```

### 3. Access Your Server

1. **From the internet**: Visit `https://server.yourdomain.com`
2. **From your laptop**: Visit `http://localhost:8080`

You should see the login page!

### 4. Create First User Account

1. Visit your domain
2. Click "Register"
3. Create your admin account

---

## Part 6: Mobile Hotspot Configuration

### Good News!

**No special configuration needed!** Cloudflare Tunnel works perfectly with mobile hotspots because:

- ✅ It creates an outbound connection (no port forwarding needed)
- ✅ Works behind CGNAT (Carrier-Grade NAT)
- ✅ Your laptop doesn't need a public IP
- ✅ Automatic reconnection if connection drops

### Tips for Mobile Hotspot Usage:

```bash
# Check data usage
vnstat -d

# Install vnstat if needed
sudo apt install vnstat
```

**To reduce data usage:**

- Compress uploaded files before uploading
- Use lower quality video streaming
- Consider data limits when sharing with others

---

## Part 7: Maintenance & Management

### Start/Stop/Restart Services

```bash
# Flask app
sudo systemctl start home-file-server
sudo systemctl stop home-file-server
sudo systemctl restart home-file-server

# Cloudflare tunnel
sudo systemctl start cloudflared
sudo systemctl stop cloudflared
sudo systemctl restart cloudflared
```

### View Logs

```bash
# Flask app logs
sudo tail -f /var/log/home-file-server/output.log
sudo tail -f /var/log/home-file-server/error.log

# Cloudflare tunnel logs
sudo journalctl -u cloudflared -f

# MongoDB logs
sudo tail -f /var/log/mongodb/mongod.log
```

### Update Application

```bash
cd ~/home-file-server
git pull  # or copy new files
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart home-file-server
```

### Backup Database

```bash
# Backup MongoDB
mongodump --out ~/backups/mongodb-$(date +%Y%m%d)

# Backup files
tar -czf ~/backups/fileserver-data-$(date +%Y%m%d).tar.gz ~/fileserver-data/
```

---

## Part 8: Security Best Practices

### 1. Firewall Setup (Optional but Recommended)

```bash
# Enable UFW firewall
sudo ufw enable

# Allow SSH (if you need remote access)
sudo ufw allow 22/tcp

# Note: You DON'T need to open port 8080 since Cloudflare Tunnel handles it
# The app only listens on localhost (127.0.0.1)

# Check firewall status
sudo ufw status
```

### 2. Regular Updates

```bash
# Create a weekly update script
cat << 'EOF' > ~/update-system.sh
#!/bin/bash
sudo apt update
sudo apt upgrade -y
sudo apt autoremove -y
cloudflared update
EOF

chmod +x ~/update-system.sh

# Run weekly
sudo crontab -e
# Add: 0 2 * * 0 /home/yourusername/update-system.sh
```

### 3. Monitor Failed Login Attempts

```bash
# Check app logs for failed logins
grep -i "invalid username or password" /var/log/home-file-server/output.log
```

### 4. Strong Passwords

- Use strong passwords for user accounts
- Change the SECRET_KEY regularly
- Never share your .env file

---

## Part 9: Troubleshooting

### Application Won't Start

```bash
# Check if port is already in use
sudo netstat -tlnp | grep 8080

# Check environment variables
cat ~/home-file-server/.env

# Check permissions
ls -la ~/home-file-server/
ls -la ~/fileserver-data/

# Check Python errors
sudo journalctl -u home-file-server -n 50
```

### Cloudflare Tunnel Issues

```bash
# Check tunnel status
sudo systemctl status cloudflared

# Test tunnel manually
cloudflared tunnel run home-file-server

# Check tunnel list
cloudflared tunnel list

# Re-login if needed
cloudflared tunnel login
```

### MongoDB Issues

```bash
# Check MongoDB status
sudo systemctl status mongod

# Check MongoDB logs
sudo tail -f /var/log/mongodb/mongod.log

# Restart MongoDB
sudo systemctl restart mongod
```

### Can't Access from Internet

1. Check DNS propagation: `nslookup server.yourdomain.com`
2. Check tunnel is running: `sudo systemctl status cloudflared`
3. Check Flask app is running: `sudo systemctl status home-file-server`
4. Check Cloudflare dashboard for tunnel status
5. Test locally first: `curl http://localhost:8080`

### High Mobile Data Usage

```bash
# Monitor bandwidth
sudo apt install iftop
sudo iftop -i <interface>

# Check which processes use data
sudo nethogs
```

---

## Part 10: Performance Optimization

### For Low-End Laptops

```bash
# Adjust worker threads if needed
nano ~/home-file-server/app.py
# Consider using gunicorn for production:
pip install gunicorn
gunicorn -w 2 -b 127.0.0.1:8080 app:app
```

### MongoDB Optimization

```bash
# Limit MongoDB memory usage (if RAM is limited)
sudo nano /etc/mongod.conf
# Add:
# storage:
#   wiredTiger:
#     engineConfig:
#       cacheSizeGB: 0.5
```

---

## Quick Command Reference

```bash
# View all services status
sudo systemctl status home-file-server cloudflared mongod

# Restart everything
sudo systemctl restart home-file-server cloudflared mongod

# View all logs
sudo journalctl -f

# Check disk space
df -h

# Check memory usage
free -h

# Monitor system resources
htop
```

---

## Success Checklist

- [ ] Ubuntu updated and packages installed
- [ ] MongoDB running and enabled
- [ ] Python virtual environment created
- [ ] Dependencies installed
- [ ] .env file configured with secure SECRET_KEY
- [ ] Domain added to Cloudflare
- [ ] Nameservers updated at domain registrar
- [ ] Cloudflared installed and authenticated
- [ ] Tunnel created and configured
- [ ] DNS routes created for domain
- [ ] Flask app service running
- [ ] Cloudflare tunnel service running
- [ ] Can access site from internet via domain
- [ ] First user account created
- [ ] Can upload/download files
- [ ] Can stream media

---

## Your Setup Summary

Once complete, you'll have:

✅ Flask app running on `http://127.0.0.1:8080` (local only)  
✅ Cloudflare Tunnel connecting to `https://server.yourdomain.com`  
✅ MongoDB storing user accounts locally  
✅ Files stored in `~/fileserver-data/`  
✅ All services auto-start on boot  
✅ Works perfectly with mobile hotspot  
✅ Secure HTTPS automatically via Cloudflare  
✅ No port forwarding needed  
✅ No static IP needed

---

## Support & Next Steps

If you encounter issues:

1. Check the Troubleshooting section
2. Review logs for error messages
3. Verify each step was completed
4. Check Cloudflare dashboard for tunnel status

**Congratulations!** Your home file server is now accessible from anywhere on the internet! 🎉
