# 🚀 DamaDam Scraper v4.0

Advanced automation bot for scraping DamaDam user profiles with dual-mode operation.

## ✨ Features

### 🎯 **Dual Scraping Modes**
- **Target Mode**: Scrapes users from the "Target" sheet
- **Online Mode**: Scrapes currently online users from https://damadam.pk/online_kon/

### 📊 **Data Management**
- Stores all profiles in a single "ProfilesTarget" sheet
- Tracks source (Target or Online) for each profile
- Separate "OnlineLog" sheet tracks when users are online
- Automatic duplicate detection and profile updates
- Change tracking with highlighted cells

### 🤖 **Automation**
- **Target Mode**: Manual trigger via GitHub Actions
- **Online Mode**: Runs automatically every 15 minutes
- Cookie-based session persistence
- Intelligent retry logic
- Rate limit handling

### 🛡️ **Robust Error Handling**
- Detects suspended accounts
- Identifies unverified users
- Graceful timeout handling
- Comprehensive logging

---

## 📁 Project Structure

```
Damadam-Scraper_v_4.0/
├── config.py              # Configuration & environment variables
├── browser.py             # Browser setup & login management
├── sheets_manager.py      # Google Sheets operations
├── scraper_target.py      # Target mode scraper
├── scraper_online.py      # Online mode scraper
├── main.py                # Main entry point
├── requirements.txt       # Python dependencies
├── .env                   # Local environment variables (create from .env_example)
├── .env_example           # Environment template
├── .gitignore            
├── README.md
└── .github/workflows/
    ├── scrape-target.yml  # Target mode workflow (manual)
    └── scrape-online.yml  # Online mode workflow (every 15 min)
```

---

## 🔧 Setup Instructions

### 1️⃣ **Clone Repository**

```bash
git clone https://github.com/yourusername/Damadam-Scraper_v_4.0.git
cd Damadam-Scraper_v_4.0
```

### 2️⃣ **Install Dependencies**

```bash
pip install -r requirements.txt
```

### 3️⃣ **Configure Environment Variables**

Copy the example file and fill in your credentials:

```bash
cp .env_example .env
```

Edit `.env`:

```bash
# DamaDam Credentials
DAMADAM_USERNAME=your_username
DAMADAM_PASSWORD=your_password

# Google Sheet URL
GOOGLE_SHEET_URL=https://docs.google.com/spreadsheets/d/your_sheet_id/edit

# Local development (use credentials.json file)
GOOGLE_APPLICATION_CREDENTIALS=credentials.json
```

### 4️⃣ **Setup Google Sheets**

1. Create a Google Sheet with these tabs:
   - **ProfilesTarget**: Main profile data
   - **Target**: List of users to scrape
   - **OnlineLog**: Tracks when users are online
   - **Dashboard**: Run statistics
   - **Tags** (optional): Tag mappings

2. Create a Google Cloud Service Account:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select existing
   - Enable Google Sheets API and Google Drive API
   - Create Service Account credentials
   - Download the JSON key file as `credentials.json`
   - Share your Google Sheet with the service account email

### 5️⃣ **Prepare Target Sheet**

In the "Target" sheet, add headers:

| Nickname | Status | Remarks | Source |
|----------|--------|---------|--------|
| user123  | ⚡ Pending |  | Target |

---

## 🚀 Usage

### **Local Execution**

#### Run Target Mode (from Target sheet)
```bash
# Scrape all pending targets
python main.py --mode target

# Scrape only 50 profiles
python main.py --mode target --max-profiles 50

# Custom batch size
python main.py --mode target --batch-size 10
```

#### Run Online Mode (from online users list)
```bash
# Scrape all online users
python main.py --mode online

# Custom batch size
python main.py --mode online --batch-size 15
```

### **GitHub Actions**

#### Setup Secrets
Go to Settings → Secrets and variables → Actions, and add:

| Secret Name | Description |
|-------------|-------------|
| `DAMADAM_USERNAME` | Your DamaDam username |
| `DAMADAM_PASSWORD` | Your DamaDam password |
| `GOOGLE_SHEET_URL` | Your Google Sheet URL |
| `GOOGLE_CREDENTIALS_JSON` | Raw JSON from credentials.json (entire content) |

**⚠️ Important**: For `GOOGLE_CREDENTIALS_JSON`, open your `credentials.json` file and copy the **entire content** (including braces) into the secret field.

#### Run Workflows

**Target Mode (Manual)**:
1. Go to Actions → Target Mode Scraper
2. Click "Run workflow"
3. Set parameters (max profiles, batch size)
4. Click "Run workflow"

**Online Mode (Automatic)**:
- Runs automatically every 15 minutes
- Can also be triggered manually from Actions → Online Mode Scraper

---

## 📊 Google Sheets Structure

### **ProfilesTarget Sheet**

| Column | Description |
|--------|-------------|
| NICK NAME | Username |
| TAGS | User tags (from Tags sheet) |
| CITY | User's city |
| GENDER | Male/Female |
| MARRIED | Yes/No |
| AGE | User age |
| JOINED | Join date |
| FOLLOWERS | Follower count |
| STATUS | Normal/Banned/Unverified |
| POSTS | Post count |
| INTRO | User bio |
| SOURCE | Target/Online |
| DATETIME SCRAP | When scraped |
| LAST POST | Most recent post URL |
| LAST POST TIME | When last posted |
| IMAGE | Profile image URL |
| PROFILE LINK | User profile URL |
| POST URL | User posts page URL |

### **OnlineLog Sheet**

Tracks when users are seen online:

| Date Time | Nickname | Last Seen |
|-----------|----------|-----------|
| 15-Dec-24 06:30 PM | user123 | 15-Dec-24 06:30 PM |

### **Target Sheet**

Manages scraping queue:

| Nickname | Status | Remarks | Source |
|----------|--------|---------|--------|
| user123 | ⚡ Pending | | Target |
| user456 | Done 💀 | updated @ 02:30 PM | Target |
| user789 | Error 💥 | Unverified user | Target |

**Status Values**:
- `⚡ Pending`: Waiting to be scraped
- `Done 💀`: Successfully scraped
- `Error 💥`: Error occurred (see Remarks)

---

## ⚙️ Configuration

### **Environment Variables**

| Variable | Default | Description |
|----------|---------|-------------|
| `MAX_PROFILES_PER_RUN` | 0 | Max profiles to scrape (0 = all) |
| `BATCH_SIZE` | 20 | Profiles per batch |
| `MIN_DELAY` | 0.3 | Min delay between requests (seconds) |
| `MAX_DELAY` | 0.5 | Max delay between requests (seconds) |
| `PAGE_LOAD_TIMEOUT` | 30 | Page load timeout (seconds) |
| `SHEET_WRITE_DELAY` | 1.0 | Delay after sheet writes (seconds) |
| `ONLINE_MODE_DELAY` | 900 | Online mode run interval (15 min) |

---

## 🐛 Troubleshooting

### **Issue: GitHub Secrets Not Working**

**Problem**: Scraper uses default values instead of secrets

**Solution**:
1. Verify secrets are set in repository Settings → Secrets
2. Check secret names match exactly (case-sensitive)
3. For `GOOGLE_CREDENTIALS_JSON`, ensure you copied the entire JSON content
4. Check workflow file uses correct secret names

### **Issue: Invalid JSON Error**

```
Error: Invalid JSON in credentials: Expecting property name...
```

**Solution**:
1. Open your `credentials.json` file
2. Copy **entire content** starting from `{` to `}`
3. Paste into GitHub Secret `GOOGLE_CREDENTIALS_JSON`
4. Do not modify or format the JSON

### **Issue: Login Failed**

**Solution**:
1. Verify credentials in `.env` or GitHub Secrets
2. Try logging in manually to check account status
3. Check if account requires 2FA (not supported)
4. Add secondary account credentials as backup

### **Issue: Permission Denied on Google Sheets**

**Solution**:
1. Open your Google Sheet
2. Click "Share" button
3. Add service account email (from credentials.json)
4. Give "Editor" permissions

### **Issue: No Online Users Found**

**Solution**:
1. Check https://damadam.pk/online_kon/ manually
2. Verify page structure hasn't changed
3. Check browser console for errors
4. Increase `PAGE_LOAD_TIMEOUT`

---

## 🔐 Security

- **Never commit** `.env` or `credentials.json` to version control
- Store sensitive data in GitHub Secrets
- Rotate credentials regularly
- Use separate accounts for automation

---

## 📝 Workflow Details

### **Target Mode**
- Triggered: Manual
- Reads from: "Target" sheet
- Processes: Users with "⚡ Pending" status
- Updates: Status to "Done 💀" or "Error 💥"
- Writes to: "ProfilesTarget" sheet with SOURCE="Target"

### **Online Mode**
- Triggered: Every 15 minutes (automatic)
- Reads from: https://damadam.pk/online_kon/
- Logs to: "OnlineLog" sheet
- Writes to: "ProfilesTarget" sheet with SOURCE="Online"
- No status updates in "Target" sheet

---

## 📈 Dashboard Metrics

The Dashboard sheet tracks:
- Run number
- Timestamp
- Profiles processed
- Success/failure counts
- New/updated/unchanged profiles
- Trigger type (scheduled/manual)
- Start/end times

---

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

---

## 📄 License

This project is for educational purposes only. Respect website terms of service and robots.txt.

---

## 🆘 Support

For issues or questions:
1. Check troubleshooting section above
2. Review GitHub Actions logs
3. Open an issue with detailed error logs
4. Contact repository maintainer

---

## 🎯 Roadmap

- [ ] Add proxy support
- [ ] Implement email notifications
- [ ] Add profile image downloading
- [ ] Support for private profiles
- [ ] Export to CSV/Excel
- [ ] Advanced filtering options
- [ ] Web dashboard for monitoring

---

**Version**: 4.0  
**Last Updated**: December 2024  
**Author**: Your Name
