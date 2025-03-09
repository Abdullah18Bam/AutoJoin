# KAU Session Manager Project Setup
# -------------------------------
# Follow these steps to set up this project on your local machine:
#
# 1. Create a virtual environment:
#    python -m venv venv
# 
# 2. Activate the virtual environment:
#    - For Windows: venv\Scripts\activate
#    - For macOS/Linux: source venv/bin/activate
#
# 3. Install Flask web framework:
#    pip install Flask
#
# 4. Install Selenium for browser automation:
#    pip install selenium
#
# 5. Install ChromeDriver and place it in the same directory as this script, or update the code to the correct path:
#    - Download ChromeDriver from https://sites.google.com/chromium.org/driver/
#
# 6. Install additional dependencies (optional):
#    pip install webdriver-manager
#
# 7. Run the Flask app:
#    python your_flask_app.py
#
# The server will run on http://127.0.0.1:5000/ and can be accessed via your web browser.
#
# credit to aekoshak https://www.linkedin.com/in/aekoshak/?locale=ar_AE
# edited by @Abdullah_bam
#
# Happy coding!
from flask import Flask, render_template, request, jsonify
from datetime import datetime
import time
import os
import threading
import traceback
import sys
import webbrowser
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

app = Flask(__name__)

def setup_driver():
    try:
        options = Options()
        options.add_argument("--disable-infobars")
        options.add_argument("start-maximized")
        options.add_argument("--disable-extensions")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_experimental_option("prefs", {
            "profile.default_content_setting_values.media_stream_mic": 1,
            "profile.default_content_setting_values.media_stream_camera": 1,
            "profile.default_content_setting_values.geolocation": 1,
            "profile.default_content_setting_values.notifications": 1
        })

        # This automatically downloads the correct ChromeDriver version
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        print("ChromeDriver initialized successfully!")
        return driver

    except Exception as e:
        print(f"Error initializing ChromeDriver: {str(e)}")
        return None

def join_class(driver, userid, password, class_link, session_id):
    try:
        print("Attempting to join class...")
        # Login page
        driver.get('https://lms.kau.edu.sa/webapps/portal/execute/tabs/tabAction?tab_tab_group_id=_101_1')
        

        time.sleep(5)

        # Login credentials
        driver.find_element(By.NAME, 'userid').send_keys(userid)
        driver.find_element(By.NAME, 'password').send_keys(password)
        driver.find_element(By.CLASS_NAME, 'c-btn').click()

        time.sleep(5)
        print("Logged in successfully")

        # Navigate to class
        driver.get(class_link)
        time.sleep(5)
        print("Navigated to class page")

        # Switch to frame
        frame = driver.find_element(By.XPATH, '//*[@id="collabUltraLtiFrame"]')
        driver.switch_to.frame(frame)
        print("Switched to class frame")

        time.sleep(20)

        # Locate and expand dropdowns with precise targeting
        try:
            dropdown_buttons = driver.find_elements(By.CSS_SELECTOR, 'button[role="button"][aria-label="Toggle session occurrences"]')

            print(f"Found {len(dropdown_buttons)} dropdown buttons")

            for index, dropdown_button in enumerate(dropdown_buttons):
                try:
                    # Ensure the dropdown is expanded
                    dropdown_button.click()
                    print(f"Dropdown {index + 1} clicked.")

                    time.sleep(2)  # Wait for the dropdown to expand
                except Exception as e:
                    print(f"Could not click dropdown {index + 1}: {str(e)}")

            # If no dropdown buttons found, or you want to force a fallback
            if not dropdown_buttons:
                print("No dropdown buttons found. Attempting alternative method.")

                # Try alternative method to expand session
                try:
                    # Look for any expandable sections
                    expandable_sections = driver.find_elements(By.CSS_SELECTOR, '[aria-expanded="false"]')
                    for section in expandable_sections:
                        try:
                            section.click()
                            print("Expanded a section")
                            time.sleep(1)
                        except Exception as click_error:
                            print(f"Could not expand section: {click_error}")
                except Exception as alt_error:
                    print(f"Alternative expansion method failed: {alt_error}")

        except Exception as e:
            print(f"Error finding dropdown buttons: {str(e)}")

        # More flexible session finding strategy
        try:
            session_selectors = [
                f"#session-{session_id} > div.item-list__item-details",
                f"[id^='session-{session_id}'] > div.item-list__item-details",
                f"div[id$='{session_id}'] > div.item-list__item-details"
            ]

            element = None
            for selector in session_selectors:
                try:
                    element = driver.find_element(By.CSS_SELECTOR, selector)
                    if element:
                        print(f"Found session using selector: {selector}")
                        break
                except NoSuchElementException:
                    continue

            if element:
                element.click()
                time.sleep(5)
            else:
                print(f"Could not find session with ID: {session_id}")
                print(driver.page_source)
        except Exception as e:
            print(f"Error finding session: {str(e)}")

        # Click join button
        join_button = '#offcanvas-wrap > div.bb-offcanvas-panel.bb-offcanvas-right.peek.active.ng-scope > div > div > div > div > div:nth-child(3) > div > bb-loading-button > button'
        driver.find_element(By.CSS_SELECTOR, join_button).click()
        print("Clicked join button")

        # Add sleep to wait for the new window to load
        time.sleep(10)

        # Switch to new window
        driver.switch_to.window(driver.window_handles[-1])
        print("Switched to class window")

        # Handle audio check
        time.sleep(5)
        driver.find_element(By.CSS_SELECTOR, '.techcheck-audio > button').click()
        print("Handled audio check")

        time.sleep(10)

        # Close announcement
        try:
            WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, '#announcement-modal-page-wrap > button'))
            ).click()
            print("Closed announcement")
        except TimeoutException:
            print("Announcement modal did not appear or was not found.")
        except Exception as e:
            print(f"Error closing announcement modal: {str(e)}")

        return True
    except Exception as e:
        print(f"Error during class joining process: {str(e)}")
        return False

def join_session(target_time, userid, password, class_link, session_id):
    try:
        while True:
            current_time = datetime.now().strftime("%H:%M:%S")
            if current_time == target_time:
                print(f"Starting session for: {class_link}")
                driver = setup_driver()
                if driver:
                    try:
                        success = join_class(driver, userid, password, class_link, session_id)
                        if success:
                            print("Successfully joined the session!")
                        else:
                            print("Failed to join the session.")
                    except Exception as e:
                        print(f"Error during session joining: {str(e)}")
                    finally:
                        print("Keeping the session open despite errors.")
                        # Do not quit the driver to keep the session open
                else:
                    print("Failed to initialize the Chrome driver.")
                break
            time.sleep(0.5)
    except Exception as e:
        print(f"Error in join_session function: {str(e)}")
        traceback.print_exc()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/add_session', methods=['POST'])
def add_session():
    try:
        data = request.json
        target_time = data['target_time']
        userid = data['userid']
        password = data['password']
        class_link = data['class_link']
        session_id = data['session_id']

        thread = threading.Thread(target=join_session, args=(target_time, userid, password, class_link, session_id))
        thread.start()

        return jsonify({"message": "Session added successfully!"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    try:
        port = 5000
        url = f"http://127.0.0.1:{port}/"
        threading.Timer(1, lambda: webbrowser.open(url)).start()

        app.run(debug=True, port=port, use_reloader=False)
    except Exception as e:
        print("An error occurred while running Flask:")
        print(f"Error details: {str(e)}")
        traceback.print_exc()
        sys.exit(1)