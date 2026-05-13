# Ubuntu Server Setup with Cloudflare Tunnel

Complete step-by-step guide to deploy the Home File Server on Ubuntu with Cloudflare Tunnel for internet access — works even behind mobile hotspot / CGNAT.

---

## Prerequisites

- Ubuntu 20.04 or newer (18.04 should work but is EOL)
- Internet connection (mobile hotspot is fine)
- A domain name managed by Cloudflare (or ready to transfer to Cloudflare DNS)
- A free [Cloudflare account](https://cloudflare.com)

---

## Part 1: Ubuntu System Setup

### 1. Update System

```bash
sudo apt update && sudo apt upgrade -y
```

### 2. Install Required System Packages

```bash
sudo apt install -y python3 python3-pip python3-venv git curl
```

### 3. Install MongoDB

```bash
# Import MongoDB GPG key
wget -qO - https://www.mongodb.org/static/pgp/server-7.0.asc | sudo apt-key add -

# Add MongoDB repository
echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu $(lsb_release -cs)/mongodb-org/7.0 multiverse" \
  | sudo tee /etc/apt/sources.list.d/mongodb-org-7.0.list

# Install
sudo apt update
sudo apt install -y mongodb-org

# Enable and start MongoDB
sudo systemctl enable mongod
sudo systemctl start mongod
sudo systemctl status mongod   # Should show "active (running)"
```

### 4. Clone the Project

```bash
cd ~
git clone <your-repo-url> home-file-server
cd home-file-server
```

---

## Part 2: Application Setup

### 1. Create a Python Virtual Environment

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

Dependencies installed:
- `Flask==2.3.3`
- `Werkzeug==2.3.7`
- `requests==2.31.0`
- `pymongo==4.6.1`
- `bcrypt==4.1.2`
- `python-dotenv==1.0.1`

### 3. Create Data Directory

```bash
mkdir -p ~/fileserver-data
chmod 755 ~/fileserver-data
```

### 4. Configure Environment Variables

```bash
cp .env.example .env

# Generate a secure secret key
python3 -c "import secrets; print(secrets.token_hex(32))"
# Copy the output

# Edit the .env file
nano .env
```

Update `.env` with your values:

```env
SECRET_KEY=<paste-the-generated-secret-key>
MONGODB_URI=mongodb://localhost:27017/
UPLOAD_FOLDER=/home/yourusername/fileserver-data
FLASK_ENV=production
HOST=127.0.0.1
PORT=8080
MAX_CONTENT_LENGTH=10737418240
```

Save with `Ctrl+O`, then exit with `Ctrl+X`.

### 5. Fix the systemd Service File

Open `home-file-server.service` and replace `yourusername` with your actual Ubuntu username:

```bash
nano home-file-server.service
```

Change these lines:

```ini
User=yourusername
WorkingDirectory=/home/yourusername/home-file-server
Environment="PATH=/home/yourusername/home-file-server/venv/bin"
EnvironmentFile=/home/yourusername/home-file-server/.env
ExecStart=/home/yourusername/home-file-server/venv/bin/python run.py
```

> **Note:** The service runs `run.py` (not `app.py`). Verify `ExecStart` points to `run.py`.

### 6. Test the Application

```bash
source venv/bin/activate
python run.py
```

In another terminal:

```bash
curl http://localhost:8080
```

If you see HTML output the app is working. Press `Ctrl+C` to stop.

---

## Part 3: Cloudflare Tunnel Setup

### 1. Add Domain to Cloudflare

1. Log in to [cloudflare.com](https://cloudflare.com)
2. Click **Add a Site** → enter your domain → select the **Free** plan
3. Copy the nameservers Cloudflare provides
4. Update nameservers at your domain registrar (GoDaddy, Namecheap, etc.)
5. Wait for DNS propagation (up to 48 hours, usually much faster)

### 2. Install `cloudflared` on Ubuntu

```bash
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i cloudflared-linux-amd64.deb
cloudflared --version
```

### 3. Authenticate with Cloudflare

```bash
cloudflared tunnel login
```

A browser window opens — log in and select your domain. Credentials are saved to `~/.cloudflared/`.

### 4. Create the Tunnel

```bash
cloudflared tunnel create home-file-server
# Note the Tunnel ID printed (format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx)
```

### 5. Configure the Tunnel

```bash
mkdir -p ~/.cloudflared
cp cloudflared-config.yml ~/.cloudflared/config.yml
nano ~/.cloudflared/config.yml
```

Update with your actual values:

```yaml
tunnel: <YOUR-TUNNEL-ID>
credentials-file: /home/yourusername/.cloudflared/<YOUR-TUNNEL-ID>.json

ingress:
  - hostname: server.yourdomain.com
    service: http://localhost:8080
  - service: http_status:404
```

### 6. Route DNS to Your Tunnel

```bash
cloudflared tunnel route dns home-file-server server.yourdomain.com
```

### 7. Test the Tunnel

```bash
# Terminal 1 — start the Flask app
cd ~/home-file-server && source venv/bin/activate && python run.py

# Terminal 2 — start the tunnel
cloudflared tunnel run home-file-server
```

Visit `https://server.yourdomain.com` in your browser. You should see the login page.

Press `Ctrl+C` in both terminals when done.

---

## Part 4: Auto-Start with systemd

### 1. Create Log Directory

```bash
sudo mkdir -p /var/log/home-file-server
sudo chown yourusername:yourusername /var/log/home-file-server
```

### 2. Install Flask App as a Service

```bash
sudo cp home-file-server.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable home-file-server
sudo systemctl start home-file-server
sudo systemctl status home-file-server   # Should show "active (running)"
```

### 3. Install Cloudflare Tunnel as a Service

```bash
sudo cloudflared service install
sudo systemctl enable cloudflared
sudo systemctl start cloudflared
sudo systemctl status cloudflared
```

---

## Part 5: Verification & Testing

### Check All Services

```bash
sudo systemctl status home-file-server
sudo systemctl status cloudflared
sudo systemctl status mongod
```

All three should show **active (running)**.

### Check Logs

```bash
# Flask app logs
tail -f /var/log/home-file-server/output.log
tail -f /var/log/home-file-server/error.log

# Cloudflare tunnel logs
sudo journalctl -u cloudflared -f

# MongoDB logs
sudo tail -f /var/log/mongodb/mongod.log
```

### Create Your First Account

1. Visit `https://server.yourdomain.com`
2. Click **Register**
3. Create your admin account

---

## Part 6: Mobile Hotspot

**No special configuration needed!** Cloudflare Tunnel creates an outbound connection so:

- ✅ No port forwarding required
- ✅ Works behind CGNAT
- ✅ No static/public IP needed
- ✅ Automatically reconnects if the connection drops

To monitor data usage:

```bash
sudo apt install vnstat
vnstat -d
```

---

## Part 7: Maintenance

### Service Management

```bash
# Flask app
sudo systemctl start|stop|restart home-file-server

# Cloudflare tunnel
sudo systemctl start|stop|restart cloudflared

# MongoDB
sudo systemctl start|stop|restart mongod
```

### Update the Application

```bash
cd ~/home-file-server
git pull
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart home-file-server
```

### Backup

```bash
# Backup MongoDB
mongodump --out ~/backups/mongodb-$(date +%Y%m%d)

# Backup uploaded files
tar -czf ~/backups/fileserver-data-$(date +%Y%m%d).tar.gz ~/fileserver-data/
```

---

## Part 8: Security Best Practices

### Firewall (UFW)

```bash
sudo ufw enable
sudo ufw allow 22/tcp    # SSH only if needed for remote access

# Port 8080 does NOT need to be opened — Cloudflare Tunnel handles all traffic
sudo ufw status
```

### Regular System Updates

```bash
cat << 'EOF' > ~/update-system.sh
#!/bin/bash
sudo apt update && sudo apt upgrade -y && sudo apt autoremove -y
cloudflared update
EOF

chmod +x ~/update-system.sh

# Schedule weekly (Sunday at 02:00)
(sudo crontab -l 2>/dev/null; echo "0 2 * * 0 /home/yourusername/update-system.sh") | sudo crontab -
```

### Monitor Failed Logins

```bash
grep -i "invalid username or password" /var/log/home-file-server/output.log
```

### Strong Secrets

- Use a strong, randomly generated `SECRET_KEY` (see setup step 4)
- Never commit `.env` to version control
- Rotate `SECRET_KEY` periodically (users will need to log in again)

---

## Part 9: Performance

### Use Gunicorn Instead of Flask's Built-in Server

```bash
source venv/bin/activate
pip install gunicorn
gunicorn -w 2 -b 127.0.0.1:8080 "app:create_app()"
```

Update `ExecStart` in `home-file-server.service` accordingly:

```ini
ExecStart=/home/yourusername/home-file-server/venv/bin/gunicorn -w 2 -b 127.0.0.1:8080 "app:create_app()"
```

### MongoDB Memory Limit (Low-RAM Systems)

```bash
sudo nano /etc/mongod.conf
```

Add under `storage`:

```yaml
storage:
  wiredTiger:
    engineConfig:
      cacheSizeGB: 0.5
```

Then restart: `sudo systemctl restart mongod`

---

## Part 10: Troubleshooting

### Application Won't Start

```bash
# Check port conflicts
sudo netstat -tlnp | grep 8080

# Check journal for errors
sudo journalctl -u home-file-server -n 50

# Check environment file
cat ~/home-file-server/.env

# Check permissions
ls -la ~/fileserver-data/
```

### Cloudflare Tunnel Issues

```bash
sudo systemctl status cloudflared
cloudflared tunnel list
cloudflared tunnel run home-file-server   # test manually
cloudflared tunnel login                  # re-auth if credentials expired
```

### MongoDB Issues

```bash
sudo systemctl status mongod
sudo journalctl -u mongod -n 30
sudo tail -f /var/log/mongodb/mongod.log
sudo systemctl restart mongod
```

### Can't Access from Internet

1. `nslookup server.yourdomain.com` — verify DNS points to Cloudflare
2. `sudo systemctl status cloudflared` — tunnel must be running
3. `sudo systemctl status home-file-server` — Flask app must be running
4. `curl http://localhost:8080` — test locally first
5. Check Cloudflare dashboard → Zero Trust → Access → Tunnels

### High Mobile Data Usage

```bash
sudo apt install iftop nethogs
sudo iftop
sudo nethogs
```

---

## Quick Reference

```bash
# All service status
sudo systemctl status home-file-server cloudflared mongod

# Restart everything
sudo systemctl restart home-file-server cloudflared

# Follow all logs
sudo journalctl -f

# Disk space
df -h

# Memory
free -h

# System resources
htop
```

---

## Deployment Checklist

- [ ] System updated
- [ ] MongoDB installed, running, and enabled
- [ ] Python virtual environment created
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] `.env` configured with secure `SECRET_KEY` and correct `MONGODB_URI`
- [ ] `UPLOAD_FOLDER` directory created with correct permissions
- [ ] Domain added to Cloudflare, nameservers updated
- [ ] `cloudflared` installed and authenticated
- [ ] Tunnel created and `~/.cloudflared/config.yml` updated
- [ ] DNS route created (`cloudflared tunnel route dns ...`)
- [ ] `home-file-server.service` updated with correct username
- [ ] Flask service installed, enabled, and running
- [ ] Cloudflare tunnel service installed, enabled, and running
- [ ] Accessed site from internet via domain
- [ ] First user account registered
- [ ] File upload/download tested
- [ ] Media streaming tested

---

## Final Setup Summary

Once complete you will have:

| Component | Details |
|-----------|---------|
| Flask app | Running on `http://127.0.0.1:8080` (local only) |
| Cloudflare Tunnel | Securely exposes app at `https://server.yourdomain.com` |
| MongoDB | Running locally on port 27017, storing user accounts |
| File storage | Stored in `~/fileserver-data/` |
| Auto-start | All services start on boot via systemd |
| HTTPS | Automatic via Cloudflare — no certificate management needed |
| Port forwarding | Not required — tunnel is outbound only |
| Static IP | Not required |
| Hotspot compatibility | ✅ Full support |

**Congratulations! Your home file server is now accessible from anywhere on the internet. 🎉**
