import csv
import logging
import pickle
import os
import time
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

# Configuration
USERNAME = "your_instagran_username"
PASSWORD = "your_instagran_password"
HASHTAG = "your_hashtag"
collected_user_data = []

# Batch and pause settings
BATCH_SIZE = 50
SHORT_PAUSE = (1, 3)
BATCH_PAUSE = (300, 600)

# Logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

# Initialize the browser
options = webdriver.ChromeOptions()
options.add_argument("--headless")
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)


def login_instagram():
    """Log into Instagram and save session cookies."""
    logger.info("Logging into Instagram")
    driver.get("https://www.instagram.com/accounts/login/")
    time.sleep(3)

    # Login form
    driver.find_element(By.NAME, "username").send_keys(USERNAME)
    driver.find_element(By.NAME, "password").send_keys(PASSWORD)
    driver.find_element(By.XPATH, "//button[@type='submit']").click()
    time.sleep(5)

    # Save cookies
    with open("cookies.pkl", "wb") as file:
        pickle.dump(driver.get_cookies(), file)
    logger.info("Login successful and cookies saved")


def load_cookies():
    """Load cookies if they exist, otherwise log in."""
    logger.info("Loading cookies for session")
    driver.get("https://www.instagram.com/")
    time.sleep(2)

    if os.path.exists("cookies.pkl"):
        with open("cookies.pkl", "rb") as file:
            cookies = pickle.load(file)
            for cookie in cookies:
                driver.add_cookie(cookie)
        logger.info("Cookies loaded successfully")
    else:
        logger.info("Cookies not found, logging in")
        login_instagram()
    time.sleep(2)
    driver.refresh()


def scroll_collect_posts(keyword, max_results):
    """Scroll through the hashtag page and collect post links."""
    formatted_keyword = keyword.replace(" ", "_")
    logger.info(f"Collecting posts for hashtag: {formatted_keyword}")
    driver.get(f"https://www.instagram.com/explore/tags/{formatted_keyword}/")
    time.sleep(3)

    post_links = set()

    while len(post_links) < max_results:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(random.uniform(*SHORT_PAUSE))

        try:
            links = driver.find_elements(By.TAG_NAME, 'a')
            for link in links:
                post_url = link.get_attribute('href')
                if post_url and '/p/' in post_url and post_url not in post_links:
                    post_links.add(post_url)
                    logger.info(f"Collected post URL: {post_url}")
                    if len(post_links) >= max_results:
                        break
        except StaleElementReferenceException:
            logger.warning("Stale element encountered. Retrying...")
            continue

        # Pause between batches
        if len(post_links) < max_results:
            time.sleep(random.uniform(*BATCH_PAUSE))

    return post_links


def extract_user_data(post_links):
    """Visit each post and extract the username and profile picture source."""
    for post_link in post_links:
        driver.get(post_link)
        time.sleep(2)

        try:
            # Extract the username
            username_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "span._ap3a._aaco._aacw._aacx._aad7._aade"))
            )
            username = username_element.text

            # Locate the profile picture using a refined selector
            profile_pic_element = driver.find_element(By.CSS_SELECTOR, "img[alt$=' profile picture']")
            profile_pic_src = profile_pic_element.get_attribute("src")

            if username and profile_pic_src:
                collected_user_data.append((username, profile_pic_src))
                logger.info(f"Collected data - Username: {username}, Profile Picture: {profile_pic_src}")
        except (TimeoutException, NoSuchElementException) as e:
            logger.warning(f"Could not retrieve data for post: {post_link} - {e}")

    return collected_user_data

def get_user_stats(username):
    """Retrieve the number of followers, followings, posts, and profile picture URL for a given username."""
    user_url = f"https://www.instagram.com/{username}/"
    driver.get(user_url)
    time.sleep(3)  # Wait for the page to load

    try:
        # Find elements containing stats
        stats_elements = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "ul li"))
        )

        # Extract text based on expected order (posts, followers, followings)
        posts = stats_elements[0].find_element(By.TAG_NAME, "span").get_attribute("title") or stats_elements[0].text
        followers = stats_elements[1].find_element(By.TAG_NAME, "span").get_attribute("title") or stats_elements[1].text
        followings = stats_elements[2].find_element(By.TAG_NAME, "span").text

        # Retrieve profile picture URL
        profile_pic_element = driver.find_element(By.CSS_SELECTOR, "img[alt$=' profile picture']")
        profile_pic_src = profile_pic_element.get_attribute("src")

        logger.info(f"User {username} has {posts} posts, {followers} followers, {followings} followings, and profile picture URL: {profile_pic_src}")
        return {
            "username": username,
            "posts": posts,
            "followers": followers,
            "followings": followings,
            "profile_pic_url": profile_pic_src
        }
    except (TimeoutException, NoSuchElementException) as e:
        logger.warning(f"Could not retrieve stats for user {username}: {e}")
        return None


def export_to_csv(user_data, filename="collected_user_data.csv"):
    """Exports usernames and profile pictures to a CSV file."""
    with open(filename, "w", newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Username", "Profile Picture URL"])
        for username, profile_pic_src in user_data:
            writer.writerow([username, profile_pic_src])
    logger.info(f"Exported user data to {filename}")


# Execute the process
num_results = int(input("Enter the number of usernames to collect: "))
load_cookies()
post_links = scroll_collect_posts(HASHTAG, num_results)
collected_user_data = extract_user_data(post_links)

export_to_csv(collected_user_data)

# Close the driver
driver.quit()
