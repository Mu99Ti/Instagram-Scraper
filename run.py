import tkinter as tk
from tkinter import messagebox
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
import logging
from random_user_agent.user_agent import UserAgent
from random_user_agent.params import SoftwareName, OperatingSystem

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize user-agent rotation
software_names = [SoftwareName.CHROME.value, SoftwareName.FIREFOX.value]
operating_systems = [OperatingSystem.WINDOWS.value, OperatingSystem.LINUX.value]
user_agent_rotator = UserAgent(software_names=software_names, operating_systems=operating_systems, limit=100)


# Function to add random delays to simulate human-like behavior
def random_delay(min_delay=2, max_delay=5):
    delay = random.uniform(min_delay, max_delay)
    logging.info(f"Sleeping for {delay:.2f} seconds to mimic human behavior.")
    time.sleep(delay)


# Function to check if we're being blocked
def check_for_block(response_text):
    if "detected unusual traffic" in response_text.lower():
        logging.warning("Bot detection or CAPTCHA detected!")
        return True
    return False


# Function to search Instagram profiles using Google
def search_instagram_on_google(keyword, num_results):
    logging.info(f"Searching for Instagram profiles with keyword: {keyword}")

    # Base Google search query and start URL
    query = f'{keyword} site:instagram.com'
    base_url = f'https://www.google.com/search?q={query}&start='

    usernames_and_urls = []
    start = 0
    session = requests.Session()  # Use a session to keep cookies

    while len(usernames_and_urls) < num_results:
        # Rotate User-Agent for each request
        headers = {
            'User-Agent': user_agent_rotator.get_random_user_agent()
        }

        # Construct the Google search URL for the current page
        url = base_url + str(start)
        logging.info(f"Making request to Google search: {url}")

        try:
            # Make the request to Google using session
            response = session.get(url, headers=headers)

            # Check if we're being blocked or redirected to CAPTCHA
            if check_for_block(response.text):
                logging.error("Request blocked or detected as bot. Exiting.")
                break

            # Check if the request was successful
            if response.status_code != 200:
                logging.error(f"Failed to retrieve Google search results. Status code: {response.status_code}")
                break

            # Parse the HTML content
            soup = BeautifulSoup(response.text, 'html.parser')

            # Extract Instagram profile links from the search results
            for link in soup.find_all('a', href=True):
                href = link['href']
                if 'instagram.com/' in href:
                    # Clean up the URL and filter only valid profile URLs
                    profile_url = href.split('&')[0].replace('/url?q=',
                                                             '')  # Remove unwanted Google prefix and parameters

                    # Ensure it's a proper Instagram profile link (exclude media, reel, and locale links)
                    if ("/p/" not in profile_url and
                            "/reel/" not in profile_url and
                            "locale" not in profile_url and
                            '?' not in profile_url and
                            '/reels/' not in profile_url):

                        if profile_url.endswith('/'):
                            profile_url = profile_url[:-1]
                        username = profile_url.split('/')[-1]  # Extract the username from the profile URL

                        # Only add unique profiles
                        if {'username': username, 'url': profile_url} not in usernames_and_urls:
                            usernames_and_urls.append({'username': username, 'url': profile_url})

                # Stop if we reach the required number of results
                if len(usernames_and_urls) >= num_results:
                    break

            # Log how many results have been found so far
            logging.info(f"Found {len(usernames_and_urls)} results so far...")

        except Exception as e:
            logging.error(f"An error occurred: {e}")
            break

        # If less than the requested results are found, try the next page
        start += 10
        random_delay()

    return usernames_and_urls


# Function to be triggered by the Run button
def run_scraper():
    keyword = keyword_entry.get()
    try:
        num_results = int(results_entry.get())
    except ValueError:
        messagebox.showerror("Input Error", "Please enter a valid number for results.")
        return

    if not keyword or num_results <= 0:
        messagebox.showerror("Input Error", "Please enter a valid keyword and number of results.")
        return

    # Run the scraper
    usernames_and_urls = search_instagram_on_google(keyword, num_results)

    if usernames_and_urls:
        # Export the usernames and URLs to an Excel file
        df = pd.DataFrame(usernames_and_urls)
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        excel_file = f'{keyword}_instagram_usernames_{timestamp}.xlsx'
        df.to_excel(excel_file, index=False)
        messagebox.showinfo("Success", f"Scraping complete! Data saved to {excel_file}")
    else:
        messagebox.showwarning("No Results", "No Instagram profiles found.")


# Create the Tkinter UI
root = tk.Tk()
root.title("Instagram Profile Scraper")

# Create and place the input fields
tk.Label(root, text="Keyword:").grid(row=0, column=0, padx=10, pady=10)
keyword_entry = tk.Entry(root)
keyword_entry.grid(row=0, column=1, padx=10, pady=10)

tk.Label(root, text="Number of Results:").grid(row=1, column=0, padx=10, pady=10)
results_entry = tk.Entry(root)
results_entry.grid(row=1, column=1, padx=10, pady=10)

# Create and place the Run button
run_button = tk.Button(root, text="Run", command=run_scraper)
run_button.grid(row=2, column=0, columnspan=2, pady=20)

# Start the Tkinter event loop
root.mainloop()
