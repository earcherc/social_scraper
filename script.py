import argparse
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import requests
import os
import shutil
import csv


def download_image(url, filename):
    response = requests.get(url)
    if response.status_code == 200:
        with open(filename, "wb") as f:
            f.write(response.content)


def scrape_instagram_profile(profile_url):
    # Initialize WebDriver
    service = Service()
    driver = webdriver.Chrome(service=service)

    # Open the Instagram profile
    driver.get(profile_url)
    time.sleep(5)

    # Scroll to ensure items are loaded (optional, adjust as necessary)
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(5)

    # Find all post links
    posts = driver.find_elements(By.TAG_NAME, "a")
    post_links = [
        post.get_attribute("href")
        for post in posts
        if "/p/" in post.get_attribute("href")
    ]

    # Create a directory to store images
    if os.path.exists("instagram_images"):
        shutil.rmtree("instagram_images")
    os.makedirs("instagram_images")

    # Create a CSV file to store captions and image URLs
    if os.path.exists("instagram_captions.csv"):
        os.remove("instagram_captions.csv")

    csv_file = open("instagram_captions.csv", mode="w", newline="", encoding="utf-8")
    csv_writer = csv.writer(csv_file)
    csv_writer.writerow(["Post URL", "Caption", "Image URLs"])

    # Navigate to each post and handle image downloads
    for link in post_links:
        driver.get(link)
        time.sleep(10)

        # Extract caption from the meta tag
        try:
            meta_tag = driver.find_element(By.CSS_SELECTOR, 'meta[property="og:title"]')
            full_caption = meta_tag.get_attribute("content").strip()
            # Extract the actual caption between quotes using regex
            caption = re.search(r': "(.*?)"', full_caption).group(1)
        except:
            caption = "No caption"

        image_urls = []
        # Check if it's a carousel
        if len(driver.find_elements(By.CLASS_NAME, "_9zm2")) > 0:
            while True:
                # Check for the presence of a video element within the carousel
                video_elements = main_content.find_elements(By.CSS_SELECTOR, "video")
                if video_elements:
                    print(f"Post: {link} contains a video. Skipping this iteration.")
                    break

                # Extract all image URLs from the first div._aagv
                images = driver.find_elements(By.CSS_SELECTOR, "div._aagv img")
                images = main_content.find_elements(By.CSS_SELECTOR, "img")
                for image in images:
                    image_url = image.get_attribute("src")
                    if "cdninstagram" in image_url and image_url not in image_urls:
                        image_urls.append(image_url)
                        download_image(
                            image_url,
                            os.path.join(
                                "instagram_images",
                                f"{caption}_{len(image_urls)}.jpg",
                            ),
                        )

                # Click the right arrow if it exists
                right_arrow = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CLASS_NAME, "_9zm2"))
                )
                right_arrow.click()
                time.sleep(2)
        else:
            # Single image post
            main_content = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div._aagv"))
            )
            images = main_content.find_elements(By.CSS_SELECTOR, "img")
            for image in images:
                image_url = image.get_attribute("src")
                if "cdninstagram" in image_url:
                    image_urls.append(image_url)
                    download_image(
                        image_url,
                        os.path.join(
                            "instagram_images",
                            f"{caption}_{len(image_urls)}.jpg",
                        ),
                    )

        # Write the post data to the CSV file
        csv_writer.writerow([link, caption, ", ".join(image_urls)])

        print(f"Post: {link}")
        print(f"Caption: {caption}")
        print(f"Images: {image_urls}")

    # Close the CSV file and the WebDriver
    csv_file.close()
    driver.quit()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Scrape Instagram profile for images and captions."
    )
    parser.add_argument(
        "profile_url", type=str, help="URL of the Instagram profile to scrape"
    )

    args = parser.parse_args()
    scrape_instagram_profile(args.profile_url)
