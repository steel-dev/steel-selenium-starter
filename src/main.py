import os
from dotenv import load_dotenv
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver
from steel import Steel
import http.client

# Load environment variables from .env file
load_dotenv()

# Initialize Steel client with the API key from environment variables
STEEL_API_KEY = os.getenv('STEEL_API_KEY')
client = Steel(steel_api_key=STEEL_API_KEY)

def main():
    session = None
    driver = None

    try:
        print("Creating Steel session...")

        # Create a new Steel session with all available options
        session = client.sessions.create(
            is_selenium=True,              # Enable Selenium mode (required)
            # session_timeout=1800000,     # Session timeout in ms (default: 15 mins, max: 60 mins)
        )

        print(f"""Session created successfully with Session ID: {session.id}.
You can view the session live at {session.session_viewer_url}
        """)

        # Create a custom HTTP connection class to handle Steel headers
        class SteelHTTPConnection(http.client.HTTPConnection):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                
            def putheader(self, header, *values):
                if header.lower() == 'host':
                    super().putheader('session-id', session.id)
                    super().putheader('steel-api-key', STEEL_API_KEY)
                super().putheader(header, *values)

        # Configure Selenium to use Steel's Selenium endpoint
        options = webdriver.ChromeOptions()
        driver = webdriver.Remote(
            command_executor='http://connect.steelbrowser.com/selenium',
            options=options,
            http_handler=SteelHTTPConnection
        )

        print("Connected to browser via Selenium")

        # ============================================================
        # Your Automations Go Here!
        # ============================================================

        # Example script - Navigate to Hacker News and extract the top 5 stories
        print("Navigating to Hacker News...")
        driver.get("https://news.ycombinator.com")
        
        # Wait for the story elements to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "titleline"))
        )

        # Extract the top 5 stories
        stories = []
        story_elements = driver.find_elements(By.CLASS_NAME, "athing")[:5]
        
        for element in story_elements:
            title_element = element.find_element(By.CLASS_NAME, "titleline").find_element(By.TAG_NAME, "a")
            subtext = element.find_element(By.XPATH, "following-sibling::tr[1]")
            score = subtext.find_element(By.CLASS_NAME, "score") if subtext.find_elements(By.CLASS_NAME, "score") else None
            
            stories.append({
                'title': title_element.text,
                'link': title_element.get_attribute('href'),
                'points': score.text.split()[0] if score else "0"
            })

        # Print the results
        print("\nTop 5 Hacker News Stories:")
        for i, story in enumerate(stories, 1):
            print(f"\n{i}. {story['title']}")
            print(f"   Link: {story['link']}")
            print(f"   Points: {story['points']}")

        # ============================================================
        # End of Automations
        # ============================================================

    except Exception as error:
        print("An error occurred:", error)
    finally:
        # Cleanup: Gracefully close browser and release session when done
        if driver:
            driver.quit()
            print("Browser closed")

        if session:
            print("Releasing session...")
            client.sessions.release(session.id)
            print("Session released")

        print("Done!")

if __name__ == "__main__":
    main()