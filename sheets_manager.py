"""
Google Sheets Manager - All sheet operations
"""

import json
import time
from pathlib import Path
from datetime import datetime, timedelta, timezone

import gspread
from google.oauth2.service_account import Credentials
from gspread.exceptions import WorksheetNotFound, APIError

from config import Config

def get_pkt_time():
    """Get current Pakistan time"""
    return datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(hours=5)

def log_msg(msg, level="INFO"):
    """Logger"""
    ts = get_pkt_time().strftime('%H:%M:%S')
    print(f"[{ts}] [{level}] {msg}")
    import sys; sys.stdout.flush()

def clean_data(value):
    """Clean cell data"""
    if not value:
        return ""
    
    v = str(value).strip().replace('\xa0', ' ')
    bad = {
        "No city", "Not set", "[No Posts]", "N/A", 
        "no city", "not set", "[no posts]", "n/a",
        "[No Post URL]", "[Error]", "no set", "none", "null", "no age"
    }
    
    if v in bad:
        return ""
    
    import re
    return re.sub(r"\s+", " ", v)

# ==================== GOOGLE SHEETS CLIENT ====================

def create_gsheets_client():
    """Create authenticated Google Sheets client"""
    log_msg("Authenticating with Google Sheets API...")
    
    if not Config.GOOGLE_SHEET_URL:
        log_msg("GOOGLE_SHEET_URL is not set", "ERROR")
        raise ValueError("Missing GOOGLE_SHEET_URL")
    
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    
    try:
        # Try using raw JSON first (GitHub Actions)
        if Config.GOOGLE_CREDENTIALS_JSON:
            log_msg("Using credentials from GitHub Secrets")
            try:
                cred_data = json.loads(Config.GOOGLE_CREDENTIALS_JSON)
                creds = Credentials.from_service_account_info(cred_data, scopes=scope)
                return gspread.authorize(creds)
            except json.JSONDecodeError as e:
                log_msg(f"Invalid JSON in credentials: {e}", "ERROR")
                raise
        
        # Try file path (local development)
        cred_path = Config.get_credentials_path()
        
        if cred_path and Path(cred_path).exists():
            log_msg(f"Using credentials file: {cred_path}")
            creds = Credentials.from_service_account_file(str(cred_path), scopes=scope)
            return gspread.authorize(creds)
        
        # No credentials found
        log_msg("No valid credentials found", "ERROR")
        raise ValueError("Missing Google credentials")
    
    except Exception as e:
        log_msg(f"Google Sheets authentication failed: {e}", "ERROR")
        raise

# ==================== SHEETS MANAGER ====================

class SheetsManager:
    """Manages all Google Sheets operations"""
    
    def __init__(self, client=None):
        if client is None:
            client = create_gsheets_client()
        
        self.client = client
        self.spreadsheet = client.open_by_url(Config.GOOGLE_SHEET_URL)
        
        # Initialize worksheets
        self.profiles_ws = self._get_or_create(Config.SHEET_PROFILES, cols=len(Config.COLUMN_ORDER))
        self.target_ws = self._get_or_create(Config.SHEET_TARGET, cols=4)
        self.dashboard_ws = self._get_or_create(Config.SHEET_DASHBOARD, cols=11)
        self.online_log_ws = self._get_or_create(Config.SHEET_ONLINE_LOG, cols=3)
        
        # Optional sheets
        self.tags_ws = self._get_sheet_if_exists(Config.SHEET_TAGS)
        
        # Load data
        self.tags_mapping = {}
        self.existing_profiles = {}
        
        self._init_headers()
        self._load_tags()
        self._load_existing_profiles()
        
        log_msg("Google Sheets connected successfully", "OK")
    
    def _get_or_create(self, name, cols=20, rows=1000):
        """Get or create worksheet"""
        try:
            return self.spreadsheet.worksheet(name)
        except WorksheetNotFound:
            log_msg(f"Creating worksheet: {name}")
            return self.spreadsheet.add_worksheet(title=name, rows=rows, cols=cols)
    
    def _get_sheet_if_exists(self, name):
        """Get sheet if it exists, return None otherwise"""
        try:
            return self.spreadsheet.worksheet(name)
        except WorksheetNotFound:
            log_msg(f"Optional sheet '{name}' not found, skipping")
            return None
    
    def _init_headers(self):
        """Initialize headers for all sheets"""
        # ProfilesTarget
        try:
            vals = self.profiles_ws.get_all_values()
            if not vals or not vals[0] or all(not c for c in vals[0]):
                log_msg("Initializing ProfilesTarget headers...")
                self.profiles_ws.append_row(Config.COLUMN_ORDER)
        except Exception as e:
            log_msg(f"ProfilesTarget header init failed: {e}")
        
        # Target
        try:
            vals = self.target_ws.get_all_values()
            if not vals or not vals[0] or all(not c for c in vals[0]):
                log_msg("Initializing Target headers...")
                self.target_ws.append_row(["Nickname", "Status", "Remarks", "Source"])
        except Exception as e:
            log_msg(f"Target header init failed: {e}")
        
        # Dashboard
        try:
            vals = self.dashboard_ws.get_all_values()
            expected = ["Run#", "Timestamp", "Profiles", "Success", "Failed", 
                       "New", "Updated", "Unchanged", "Trigger", "Start", "End"]
            if not vals or vals[0] != expected:
                self.dashboard_ws.clear()
                self.dashboard_ws.append_row(expected)
        except Exception as e:
            log_msg(f"Dashboard header init failed: {e}")
        
        # OnlineLog
        try:
            vals = self.online_log_ws.get_all_values()
            if not vals or not vals[0] or all(not c for c in vals[0]):
                log_msg("Initializing OnlineLog headers...")
                self.online_log_ws.append_row(Config.ONLINE_LOG_COLUMNS)
        except Exception as e:
            log_msg(f"OnlineLog header init failed: {e}")
    
    def _load_tags(self):
        """Load tags mapping from Tags sheet"""
        if not self.tags_ws:
            return
        
        try:
            all_values = self.tags_ws.get_all_values()
            if not all_values or len(all_values) < 2:
                return
            
            headers = all_values[0]
            for col_idx, header in enumerate(headers):
                tag_name = clean_data(header)
                if not tag_name:
                    continue
                
                for row in all_values[1:]:
                    if col_idx < len(row):
                        nickname = row[col_idx].strip()
                        if nickname:
                            key = nickname.lower()
                            if key in self.tags_mapping:
                                if tag_name not in self.tags_mapping[key]:
                                    self.tags_mapping[key] += f", {tag_name}"
                            else:
                                self.tags_mapping[key] = tag_name
            
            log_msg(f"Loaded {len(self.tags_mapping)} tag mappings")
        
        except Exception as e:
            log_msg(f"Tags load failed: {e}")
    
    def _load_existing_profiles(self):
        """Load existing profiles from ProfilesTarget"""
        try:
            rows = self.profiles_ws.get_all_values()[1:]  # Skip header
            nick_idx = Config.COLUMN_ORDER.index("NICK NAME")
            
            for i, row in enumerate(rows, start=2):
                if len(row) > nick_idx and row[nick_idx].strip():
                    nickname = row[nick_idx].strip().lower()
                    self.existing_profiles[nickname] = {
                        'row': i,
                        'data': row
                    }
            
            log_msg(f"Loaded {len(self.existing_profiles)} existing profiles")
        
        except Exception as e:
            log_msg(f"Failed to load existing profiles: {e}")
    
    # ==================== PROFILE OPERATIONS ====================
    
    def write_profile(self, profile_data):
        """Write profile to ProfilesTarget sheet"""
        nickname = (profile_data.get("NICK NAME") or "").strip()
        if not nickname:
            return {"status": "error", "error": "Missing nickname"}
        
        # Add scrape timestamp
        profile_data["DATETIME SCRAP"] = get_pkt_time().strftime("%d-%b-%y %I:%M %p")
        
        # Add tags if available
        tags = self.tags_mapping.get(nickname.lower())
        if tags:
            profile_data["TAGS"] = tags
        
        # Build row data
        row_data = []
        for col in Config.COLUMN_ORDER:
            value = clean_data(profile_data.get(col, ""))
            row_data.append(value)
        
        key = nickname.lower()
        existing = self.existing_profiles.get(key)
        
        if existing:
            # Update existing profile
            row_num = existing['row']
            old_data = existing['data']
            
            # Detect changes
            changed_fields = []
            for i, col in enumerate(Config.COLUMN_ORDER):
                if col in {"DATETIME SCRAP", "LAST POST", "LAST POST TIME", "JOINED", "PROFILE LINK"}:
                    continue
                old_val = old_data[i] if i < len(old_data) else ""
                new_val = row_data[i]
                if old_val != new_val:
                    changed_fields.append(col)
            
            # Update row
            end_col = self._column_letter(len(Config.COLUMN_ORDER) - 1)
            self.profiles_ws.update(values=[row_data], range_name=f"A{row_num}:{end_col}{row_num}")
            time.sleep(Config.SHEET_WRITE_DELAY)
            
            # Update cache
            self.existing_profiles[key] = {'row': row_num, 'data': row_data}
            
            status = "updated" if changed_fields else "unchanged"
            return {"status": status, "changed_fields": changed_fields}
        
        else:
            # Add new profile
            self.profiles_ws.append_row(row_data)
            time.sleep(Config.SHEET_WRITE_DELAY)
            
            last_row = len(self.profiles_ws.get_all_values())
            self.existing_profiles[key] = {'row': last_row, 'data': row_data}
            
            return {"status": "new", "changed_fields": list(Config.COLUMN_ORDER)}
    
    def get_profile(self, nickname):
        """Fetch existing profile data by nickname"""
        if not nickname:
            return None
        record = self.existing_profiles.get(nickname.strip().lower())
        if not record:
            return None
        data = record['data']
        profile_dict = {}
        for idx, col in enumerate(Config.COLUMN_ORDER):
            value = data[idx] if idx < len(data) else ""
            profile_dict[col] = value
        return profile_dict

    def create_profile(self, profile_data):
        """Create a new profile row (compat wrapper)"""
        return self.write_profile(profile_data)

    def update_profile(self, nickname, profile_data):
        """Update an existing profile row (compat wrapper)"""
        # Ensure nickname carried over for lookup
        if nickname:
            profile_data = dict(profile_data)
            profile_data["NICK NAME"] = nickname
        return self.write_profile(profile_data)

    # ==================== TARGET OPERATIONS ====================
    
    def get_pending_targets(self):
        """Get pending targets from Target sheet"""
        try:
            rows = self.target_ws.get_all_values()[1:]  # Skip header
            targets = []
            
            for idx, row in enumerate(rows, start=2):
                nickname = (row[0] if len(row) > 0 else '').strip()
                status = (row[1] if len(row) > 1 else '').strip()
                source = (row[3] if len(row) > 3 else 'Target').strip() or 'Target'
                
                # Check if pending
                is_pending = (
                    not status or 
                    status == Config.TARGET_STATUS_PENDING or
                    "pending" in status.lower()
                )
                
                if nickname and is_pending:
                    targets.append({
                        'nickname': nickname,
                        'row': idx,
                        'source': source
                    })
            
            return targets
        
        except Exception as e:
            log_msg(f"Failed to get pending targets: {e}", "ERROR")
            return []
    
    def update_target_status(self, row, status, remarks):
        """Update target status"""
        try:
            # Normalize status
            lower = (status or "").lower().strip()
            if 'pending' in lower:
                status = Config.TARGET_STATUS_PENDING
            elif 'done' in lower or 'complete' in lower:
                status = Config.TARGET_STATUS_DONE
            elif 'error' in lower or 'suspended' in lower or 'unverified' in lower:
                status = Config.TARGET_STATUS_ERROR
            
            # Update with retry
            for attempt in range(3):
                try:
                    self.target_ws.update(values=[[status]], range_name=f"B{row}")
                    self.target_ws.update(values=[[remarks]], range_name=f"C{row}")
                    time.sleep(Config.SHEET_WRITE_DELAY)
                    break
                except APIError as e:
                    if '429' in str(e):
                        log_msg("API quota exceeded, waiting 60s...")
                        time.sleep(60)
                    else:
                        raise
        
        except Exception as e:
            log_msg(f"Failed to update target status: {e}", "ERROR")

    def update_runlist_status(self, row, status, remarks):
        """Backward compatible alias for target status updates"""
        return self.update_target_status(row, status, remarks)

    # ==================== ONLINE LOG OPERATIONS ====================
    
    def log_online_user(self, nickname, timestamp=None):
        """Log an online user to OnlineLog sheet"""
        if timestamp is None:
            timestamp = get_pkt_time().strftime("%d-%b-%y %I:%M %p")
        
        try:
            row = [timestamp, nickname, timestamp]
            self.online_log_ws.append_row(row)
            time.sleep(Config.SHEET_WRITE_DELAY)
        except Exception as e:
            log_msg(f"Failed to log online user: {e}", "ERROR")
    
    # ==================== DASHBOARD OPERATIONS ====================
    
    def update_dashboard(self, metrics):
        """Update dashboard with run metrics"""
        try:
            row = [
                metrics.get("Run Number", 1),
                metrics.get("Last Run", get_pkt_time().strftime("%d-%b-%y %I:%M %p")),
                metrics.get("Profiles Processed", 0),
                metrics.get("Success", 0),
                metrics.get("Failed", 0),
                metrics.get("New Profiles", 0),
                metrics.get("Updated Profiles", 0),
                metrics.get("Unchanged Profiles", 0),
                metrics.get("Trigger", "manual"),
                metrics.get("Start", ""),
                metrics.get("End", ""),
            ]
            
            self.dashboard_ws.append_row(row)
            time.sleep(Config.SHEET_WRITE_DELAY)
            log_msg("Dashboard updated", "OK")
        
        except Exception as e:
            log_msg(f"Dashboard update failed: {e}", "ERROR")
    
    # ==================== HELPERS ====================
    
    def _column_letter(self, index):
        """Convert 0-based index to Excel column letter"""
        result = ""
        index += 1
        while index > 0:
            index -= 1
            result = chr(index % 26 + 65) + result
            index //= 26
        return result

    def sort_profiles_by_date(self):
        """Sort profiles sheet by DATETIME SCRAP descending"""
        try:
            all_rows = self.profiles_ws.get_all_values()
            if len(all_rows) <= 1:
                return

            header, rows = all_rows[0], all_rows[1:]
            try:
                date_idx = header.index("DATETIME SCRAP")
            except ValueError:
                log_msg("DATETIME SCRAP column not found, skipping sort", "WARNING")
                return

            def parse_date(row):
                try:
                    value = row[date_idx]
                except IndexError:
                    value = ""
                try:
                    return datetime.strptime(value, "%d-%b-%y %I:%M %p") if value else datetime.min
                except Exception:
                    return datetime.min

            rows.sort(key=parse_date, reverse=True)
            self.profiles_ws.update([header] + rows)
            # Refresh cache to align row numbers
            self._load_existing_profiles()
        except Exception as e:
            log_msg(f"Failed to sort profiles by date: {e}", "ERROR")
