import os
import datetime
import pandas as pd
import csv
import time
from datetime import datetime, timedelta
from collections import defaultdict
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import seaborn as sns

# Configure plotting style
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")

STORAGE_FILE = "teams_storage_state.json"

class TeamsScraper:
    """
    ENHANCED VERSION: Increased scrolling + Login/Logout tracking
    """
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.debug_log = []
        
    def log(self, message):
        """Log messages with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}"
        print(log_message)
        self.debug_log.append(log_message)
        
    def initialize(self):
        """Initialize the browser with saved session"""
        if not os.path.exists(STORAGE_FILE):
            self.log("❌ storage_state.json not found. Please run login setup first.")
            messagebox.showerror("Login Required", 
                                 "storage_state.json file not found!\n\nPlease run the login setup to create this file.")
            return False

        try:
            self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.launch(
                headless=False,
                args=['--disable-blink-features=AutomationControlled']
            )
            self.context = self.browser.new_context(
                storage_state=STORAGE_FILE,
                viewport={'width': 1400, 'height': 900}
            )
            self.page = self.context.new_page()

            self.log("🔐 Logging in using storage_state.json...")
            self.page.goto("https://teams.microsoft.com", wait_until="networkidle", timeout=120000)

            # Wait for Teams to load completely
            self.log("⏳ Waiting for Teams to load...")
            self.page.wait_for_timeout(10000)

            current_url = self.page.url
            self.log(f"🌐 Current URL: {current_url}")

            if "teams.microsoft.com" in current_url and "login" not in current_url:
                self.log("✅ Successfully logged in to Teams!")
                return True
            else:
                self.log("❌ Not on Teams main page. Possible login issue.")
                self.page.screenshot(path="teams_debug.png")
                self.log("📸 Screenshot saved as teams_debug.png")
                return False

        except Exception as e:
            self.log(f"❌ Error initializing Teams: {e}")
            messagebox.showerror("Initialization Error", f"Failed to initialize Teams: {e}")
            return False

    def setup_login(self):
        """Setup Teams login and save session"""
        try:
            self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.launch(headless=False)
            self.context = self.browser.new_context(viewport={'width': 1400, 'height': 900})
            self.page = self.context.new_page()

            self.log("🔐 Please log in to Teams manually...")
            self.page.goto("https://teams.microsoft.com", wait_until="networkidle")
            
            messagebox.showinfo("Login Required", 
                                "Please log in to Teams in the browser window.\n\n"
                                "After successful login, press OK to save your session.")
            
            self.context.storage_state(path=STORAGE_FILE)
            self.log("✅ Login session saved to storage_state.json!")
            
            self.context.close()
            self.browser.close()
            self.playwright.stop()
            
            messagebox.showinfo("Login Successful", 
                                "Teams login completed successfully!\n\n"
                                "Your session has been saved to storage_state.json")
            return True
            
        except Exception as e:
            self.log(f"❌ Error during login setup: {e}")
            messagebox.showerror("Login Error", f"Failed to setup login: {e}")
            return False

    def _get_chat_frame(self):
        """
        Try to find the main chat content iframe.
        The "New Teams" client nests the chat in an iframe.
        """
        self.log("🔍 Locating chat iframe...")
        
        # Try known iframe selectors for New Teams
        iframe_selectors = [
            "iframe[id*='chat-content']",
            "iframe[id*='experience-container']",
            "iframe[title*='Chat content']",
            "iframe[name*='chat']"
        ]
        
        for selector in iframe_selectors:
            try:
                frame_locator = self.page.frame_locator(selector)
                frame_locator.first.wait_for(timeout=2000) 
                self.log(f"✅ Found iframe with selector: {selector}")
                return frame_locator.first
            except:
                self.log(f"ℹ️ No iframe found with: {selector}")
                
        self.log("⚠️ No specific chat iframe found. Assuming content is on main page.")
        return self.page

    def wait_for_chat_messages(self, timeout=20000):
        """
        Wait for chat messages using Fluent UI classes.
        """
        self.log("🔍 Waiting for chat messages to load...")
        
        search_context = self._get_chat_frame()
        
        selector = "div[class*='fui-ChatMessage '], div[class*='fui-ChatMyMessage ']"
        
        try:
            self.log(f"Trying selector in context: {selector}")
            search_context.wait_for_selector(selector, timeout=10000)
            self.log(f"✅ Found messages with selector: {selector}")
            return True
        except:
            self.log("❌ No messages found with any selector in the context")
            return False

    def __scroll_to_load_messages(self, search_context, scrolls=800, delay=1600):
        """
        ENHANCED: Aggressive scrolling to load ALL messages from the beginning
        """
        self.log(f"🔄 Loading older messages ({scrolls} scrolls with {delay}ms delay)...")
        
        previous_height = 0
        no_change_count = 0
        
        for i in range(scrolls):
            try:
                # Get current scroll height
                current_height = search_context.evaluate("document.body.scrollHeight")
                
                # Scroll to the very top
                search_context.evaluate("window.scrollTo(0, 0)")
                self.page.wait_for_timeout(delay)
                
                # Check if we've reached the top (no new content loaded)
                if current_height == previous_height:
                    no_change_count += 1
                    if no_change_count >= 15:
                        self.log(f"✅ Reached the beginning of chat (no new messages after {no_change_count} attempts)")
                        break
                else:
                    no_change_count = 0
                    previous_height = current_height
                
                if (i + 1) % 10 == 0:
                    self.log(f"⬆️ Scrolled {i + 1}/{scrolls} times (Height: {current_height})")
                    
            except Exception as e:
                self.log(f"⚠️ Error during scroll: {e}. Stopping scroll.")
                break
        
        # Final scroll to top to ensure we're at the beginning
        try:
            search_context.evaluate("window.scrollTo(0, 0)")
            self.page.wait_for_timeout(3000)
        except:
            pass
            
        self.log("✅ Message loading complete - starting from first message")

    def scrape_teams_chat(self):
        """
        ENHANCED: Scrape Teams chat data with Login/Logout detection
        """
        self.log("📖 Starting Teams chat scraping...")
        chat_data = []

        try:
            search_context = self._get_chat_frame()

            if not self.wait_for_chat_messages():
                self.log("❌ No chat messages found. Please ensure you're in a Teams chat.")
                self.log("📸 Taking screenshot: no_messages_found.png")
                self.page.screenshot(path="no_messages_found.png")
                return chat_data

            # INCREASED SCROLLING: 100 scrolls instead of 20
            self.__scroll_to_load_messages(search_context, scrolls=800, delay=3200)

            self.log("🔍 Extracting chat messages...")

            message_containers = search_context.query_selector_all(
                "div[class*='fui-ChatMessage '], div[class*='fui-ChatMyMessage ']"
            )

            self.log(f"📨 Total message containers found: {len(message_containers)}")
            
            if not message_containers:
                self.log("❌ No message containers found. Scraping cannot continue.")
                self.log("📸 Taking screenshot: no_containers_found.png")
                self.page.screenshot(path="no_containers_found.png")
                return chat_data

            for i, message_container in enumerate(message_containers):
                try:
                    # 1. Get Author
                    author_element = message_container.query_selector("span[data-tid='message-author-name']")
                    
                    # 2. Get Timestamp
                    timestamp_element = message_container.query_selector("time[class*='__timestamp']")
                    
                    # 3. Get Content
                    content_element = message_container.query_selector("div[id^='content-']")

                    if not author_element or not timestamp_element or not content_element:
                        self.log(f"⚠️ Skipping message {i}, missing author, timestamp, or content.")
                        continue
                        
                    sender = author_element.inner_text().strip()
                    timestamp_str = timestamp_element.get_attribute('title') 
                    content = content_element.inner_text().strip()

                    if not sender or not timestamp_str or not content:
                        self.log(f"⚠️ Skipping message {i}, extracted data was empty.")
                        continue

                    formatted_ts = self._format_timestamp(timestamp_str, sender)
                    chat_data.append([formatted_ts, "Teams Chat", content])
                    
                    if len(chat_data) % 50 == 0:
                        self.log(f"📝 Processed {len(chat_data)} messages...")

                except Exception as e:
                    self.log(f"⚠️ Error processing message container {i}: {e}")

            self.log(f"✅ Scraping completed. Total valid messages: {len(chat_data)}")

        except Exception as e:
            self.log(f"❌ Error during scraping: {e}")
            try:
                self.page.screenshot(path="scraping_error.png")
                self.log("📸 Screenshot saved as scraping_error.png")
            except: pass

        return chat_data

    def _format_timestamp(self, timestamp_str, sender):
        """
        Format timestamp to standard format.
        """
        try:
            current_time = datetime.now()
            timestamp_str = timestamp_str.strip().replace(',', '').replace(' at ', ' ')

            dt_obj = None

            if 'today' in timestamp_str.lower():
                time_part = timestamp_str.lower().replace('today', '').strip()
                try:
                    dt_obj = datetime.strptime(time_part, '%H:%M').replace(year=current_time.year, month=current_time.month, day=current_time.day)
                except ValueError:
                    dt_obj = datetime.strptime(time_part, '%I:%M %p').replace(year=current_time.year, month=current_time.month, day=current_time.day)
            
            elif 'yesterday' in timestamp_str.lower():
                time_part = timestamp_str.lower().replace('yesterday', '').strip()
                yesterday = current_time - timedelta(days=1)
                try:
                    dt_obj = datetime.strptime(time_part, '%H:%M').replace(year=yesterday.year, month=yesterday.month, day=yesterday.day)
                except ValueError:
                    dt_obj = datetime.strptime(time_part, '%I:%M %p').replace(year=yesterday.year, month=yesterday.month, day=yesterday.day)
            
            elif '/' in timestamp_str:
                try:
                    dt_obj = datetime.strptime(timestamp_str, '%m/%d/%Y %I:%M %p')
                except ValueError:
                     dt_obj = datetime.strptime(timestamp_str, '%m/%d/%Y %H:%M')
            
            else:
                 dt_obj = datetime.strptime(timestamp_str, '%I:%M %p').replace(year=current_time.year, month=current_time.month, day=current_time.day)

            time_str = dt_obj.strftime('%I:%M %p')
            date_str = dt_obj.strftime('%m/%d/%Y')
            
            return f"[{time_str}, {date_str}] {sender}:"

        except Exception as e:
            self.log(f"⚠️ Error parsing timestamp '{timestamp_str}': {e}. Using current time.")
            time_str = datetime.now().strftime('%I:%M %p')
            date_str = datetime.now().strftime('%m/%d/%Y')
            return f"[{time_str}, {date_str}] {sender}:"

    def get_debug_log(self):
        """Get the debug log"""
        return "\n".join(self.debug_log)

    def close(self):
        """Close browser resources"""
        self.log("🔒 Closing browser...")
        try:
            if self.context: self.context.close()
            if self.browser: self.browser.close()
            if self.playwright: self.playwright.stop()
            self.log("✅ Browser closed.")
        except Exception as e:
            self.log(f"⚠️ Error closing browser: {e}")


def process_chat_data(chat_data):
    """
    ENHANCED: Process chat data with Login/Logout tracking added to tasks
    """
    sessions_data = []
    breaks_data = []
    tasks_data = []

    activity_tracker = defaultdict(dict)

    for row in chat_data:
        timestamp, chat_name, message = row
        try:
            if ']' not in timestamp or '[' not in timestamp:
                continue
            
            timestamp_part, contact_part = timestamp.split(']', 1)
            timestamp_part = timestamp_part.strip('[').strip()
            
            if ',' not in timestamp_part:
                continue
                
            time_part, date_part = timestamp_part.split(',', 1)
            time_part = time_part.strip()
            date_part = date_part.strip()
            
            trainer_name = contact_part.strip().split(':', 1)[0].strip()
            if not trainer_name or trainer_name == "Unknown":
                continue

            try:
                dt_obj = datetime.strptime(f"{date_part} {time_part}", '%m/%d/%Y %I:%M %p')
            except ValueError as e:
                print(f"⚠️ Skipping row. Cannot parse datetime: {date_part} {time_part} -> {e}")
                continue
            
            formatted_date = dt_obj.strftime('%d/%m/%Y')
            message_lower = message.lower()

            # --- ENHANCED: Login/Logout Detection ---
            login_patterns = ['login', 'Login', 'LOGIN', 'joining']
            logout_patterns = ['logout', 'logged out', 'LOGOUT', 'Logout', 'signing off']
            
            # Check for Login
            if any(pattern in message_lower for pattern in login_patterns):
                time_str = dt_obj.strftime('%I:%M %p')
                tasks_data.append([formatted_date, trainer_name, "Login", time_str, "N/A", 0, message, 1])
                print(f"🔑 Recorded Login: {trainer_name} at {time_str}")
                continue
            
            # Check for Logout
            if any(pattern in message_lower for pattern in logout_patterns):
                time_str = dt_obj.strftime('%I:%M %p')
                tasks_data.append([formatted_date, trainer_name, "Logout", time_str, "N/A", 0, message, 1])
                print(f"🔑 Recorded Logout: {trainer_name} at {time_str}")
                continue

            # --- Keyword Definitions ---
            session_start_patterns = ['started', 'CDA', 'Started', 'STARTED', 'CBR', 'DM', 'DA', 'DS', 'BA' ]
            session_end_patterns = ['finished', 'Finished', 'FINISHED', 'done', '- finished', '- Finished']
            break_patterns = ['break', 'namaz break', 'BREAK', 'Break', 'Namaz Break']
            back_patterns = ['back', ' Back', 'BACK']
            task_keywords = ['task', 'project', 'Induction', 'Task', 'Project', 'INDUCTION']

            # --- Task Detection ---
            if any(keyword in message_lower for keyword in task_keywords):
                task_name = "Task/Project"
                try:
                    if '-' in message: task_name = message.split("-")[0].strip()
                    elif ':' in message: task_name = message.split(":")[0].strip()
                except: pass

                # Check for Login as task start time
                login_patterns = ['login', 'Login', 'LOGIN', 'joining']
                if any(pattern in message_lower for pattern in login_patterns):
                    activity_tracker[trainer_name]['task_dt'] = dt_obj
                    activity_tracker[trainer_name]['current_task'] = task_name
                    print(f"🔍 Found task start at login: {task_name} by {trainer_name}")
                
                # Check for Logout as task end time
                logout_patterns = ['logout', 'logged out', 'LOGOUT', 'Logout', 'signing off']
                if any(pattern in message_lower for pattern in logout_patterns):
                    if 'task_dt' in activity_tracker[trainer_name]:
                        start_dt = activity_tracker[trainer_name]['task_dt']
                        finish_dt = dt_obj
                        duration = max(0, int((finish_dt - start_dt).total_seconds() // 60))
                        
                        if duration > 0:
                            start_time_str = start_dt.strftime('%I:%M %p')
                            finish_time_str = finish_dt.strftime('%I:%M %p')
                            current_task = activity_tracker[trainer_name].get('current_task', 'Task/Project')
                            
                            tasks_data.append([formatted_date, trainer_name, current_task, start_time_str, finish_time_str, duration, message, 1])
                            print(f"✅ Recorded task: {current_task} by {trainer_name} - {duration} minutes")
                            
                            del activity_tracker[trainer_name]['task_dt']
                            if 'current_task' in activity_tracker[trainer_name]:
                                del activity_tracker[trainer_name]['current_task']
                    else:
                        tasks_data.append([formatted_date, trainer_name, task_name, "N/A", dt_obj.strftime('%I:%M %p'), 0, message, 1])

            # --- Break Detection ---
            elif any(pattern in message.lower() for pattern in break_patterns):
                activity_tracker[trainer_name]['break_dt'] = dt_obj
                print(f"🔍 Found break start: {trainer_name} at {dt_obj.strftime('%I:%M %p')}")

            elif any(pattern in message.lower() for pattern in back_patterns):
                if 'break_dt' in activity_tracker[trainer_name]:
                    start_dt = activity_tracker[trainer_name]['break_dt']
                    finish_dt = dt_obj
                    duration = max(0, int((finish_dt - start_dt).total_seconds() // 60))
                    
                    if duration > 0:
                        start_time_str = start_dt.strftime('%I:%M %p')
                        finish_time_str = finish_dt.strftime('%I:%M %p')
                        
                        breaks_data.append([formatted_date, trainer_name, start_time_str, finish_time_str, duration, message, 1])
                        print(f"✅ Recorded break: {trainer_name} - {duration} minutes")
                        
                        del activity_tracker[trainer_name]['break_dt']
                else:
                    breaks_data.append([formatted_date, trainer_name, "N/A", dt_obj.strftime('%I:%M %p'), 0, message, 1])

            # --- Session Detection ---
            elif any(pattern in message_lower for pattern in session_start_patterns):
                activity_tracker[trainer_name]['start_dt'] = dt_obj
                print(f"🔍 Found session start: {trainer_name} at {dt_obj.strftime('%I:%M %p')}")

            elif any(pattern in message_lower for pattern in session_end_patterns):
                if 'start_dt' in activity_tracker[trainer_name]:
                    start_dt = activity_tracker[trainer_name]['start_dt']
                    finish_dt = dt_obj
                    duration = max(0, int((finish_dt - start_dt).total_seconds() // 60))
                    
                    if duration > 0:
                        start_time_str = start_dt.strftime('%I:%M %p')
                        finish_time_str = finish_dt.strftime('%I:%M %p')
                        
                        sessions_data.append([formatted_date, trainer_name, start_time_str, finish_time_str, duration, message, 1])
                        print(f"✅ Recorded session: {trainer_name} - {duration} minutes")
                        
                        del activity_tracker[trainer_name]['start_dt']
                else:
                    sessions_data.append([formatted_date, trainer_name, "N/A", dt_obj.strftime('%I:%M %p'), 0, message, 1])

        except Exception as e:
            print(f"⚠️ Error processing message row: {row} -> {e}")

    print(f"📊 Processing complete: {len(sessions_data)} sessions, {len(breaks_data)} breaks, {len(tasks_data)} tasks (including logins/logouts)")
    return sessions_data, breaks_data, tasks_data


def save_data_to_csv(sessions_data, breaks_data, tasks_data):
    """Save processed data to CSV files"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    sessions_file = f"teams_sessions_{timestamp}.csv"
    breaks_file = f"teams_breaks_{timestamp}.csv"
    tasks_file = f"teams_tasks_{timestamp}.csv"
    
    if sessions_data:
        with open(sessions_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["Date", "Trainer Name", "Start Time", "Finish Time", "Duration (min)", "Message", "Finished Count"])
            writer.writerows(sessions_data)
        print(f"✅ Sessions saved to: {sessions_file}")
    else:
        print("⚠️ No sessions data to save")
    
    if breaks_data:
        with open(breaks_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["Date", "Trainer Name", "Start Time", "Finish Time", "Duration (min)", "Message", "Break Count"])
            writer.writerows(breaks_data)
        print(f"✅ Breaks saved to: {breaks_file}")
    else:
        print("⚠️ No breaks data to save")
    
    if tasks_data:
        with open(tasks_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["Date", "Trainer Name", "Task", "Start Time", "Finish Time", "Duration (min)", "Message", "Task Count"])
            writer.writerows(tasks_data)
        print(f"✅ Tasks saved to: {tasks_file}")
    else:
        print("⚠️ No tasks data to save")
    
    return sessions_file, breaks_file, tasks_file


# ... [Dashboard class remains the same - keeping your existing TeamsDashboard code]


def run_automated_teams_dashboard():
    """Main function to run the complete automated Teams dashboard"""
    print("=" * 60)
    print("🚀 Starting Teams Automated Dashboard (ENHANCED v5)")
    print("=" * 60)
    
    if not os.path.exists(STORAGE_FILE):
        print("❌ storage_state.json not found!")
        choice = messagebox.askyesno("Login Setup Required", 
                                     "No login session found!\n\n"
                                     "Do you want to setup Teams login now?")
        if choice:
            scraper = TeamsScraper()
            if not scraper.setup_login():
                return
        else:
            return
    
    print("\n📥 Starting Teams data scraping...")
    scraper = TeamsScraper()
    
    if scraper.initialize():
        try:
            messagebox.showinfo("Action Required", 
                                "The browser is ready.\n\n"
                                "Please manually click on the chat you want to scrape.\n\n"
                                "Once the chat and its messages are VISIBLE, press OK here to begin scraping.\n\n"
                                "NOTE: This will scroll extensively to capture ALL messages from the beginning.")
            
            print("🎯 Scraping Teams chat...")
            chat_data = scraper.scrape_teams_chat()
            
            if chat_data:
                print(f"✅ Successfully scraped {len(chat_data)} raw messages")
                
                print("🔄 Processing chat data...")
                sessions_data, breaks_data, tasks_data = process_chat_data(chat_data)
                
                print("💾 Saving data to CSV files...")
                sessions_file, breaks_file, tasks_file = save_data_to_csv(sessions_data, breaks_data, tasks_data)
                
                debug_log = scraper.get_debug_log()
                
                print("📊 Launching dashboard...")
                # You'll need to import/paste your TeamsDashboard class here
                # dashboard = TeamsDashboard(sessions_file, breaks_file, tasks_file, debug_log)
                # dashboard.run()
                
            else:
                print("❌ No chat data was scraped!")
                
        except Exception as e:
            print(f"❌ An error occurred: {e}")
        finally:
            scraper.close()
    else:
        print("❌ Failed to initialize Teams!")


if __name__ == "__main__":
    run_automated_teams_dashboard()

