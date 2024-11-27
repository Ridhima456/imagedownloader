import os
import re
import requests
from bs4 import BeautifulSoup
import zipfile
import io
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import streamlit as st

# Function to scrape Google Images for image URLs
def scrape_google_images(keyword, num_images):
    search_url = f"https://www.google.com/search?hl=en&q={keyword}&tbm=isch"
    headers = {"User-Agent": "Mozilla/5.0"}
    
    response = requests.get(search_url, headers=headers)
    if response.status_code != 200:
        st.error(f"Failed to retrieve search results: {response.status_code}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')

    # Use regex to find image URLs
    image_elements = soup.find_all("img", {"src": re.compile(r"^https://")})
    image_urls = [img['src'] for img in image_elements[:num_images]]
    
    st.success(f"Found {len(image_urls)} image URLs.")
    return image_urls

# Function to download images into memory
def download_images_in_memory(image_urls):
    image_data_list = []
    
    for i, url in enumerate(image_urls):
        try:
            image_data = requests.get(url).content
            image_data_list.append((f"image_{i+1}.jpg", image_data))  # Store image data and file name
            st.write(f"Downloaded image {i+1}")
        except Exception as e:
            st.error(f"Failed to download image {i+1}: {e}")
    
    return image_data_list

# Function to create a ZIP file in memory
def create_zip_in_memory(image_data_list):
    zip_buffer = io.BytesIO()  # Create an in-memory buffer for the ZIP file
    with zipfile.ZipFile(zip_buffer, 'w') as zipf:
        for image_name, image_data in image_data_list:
            zipf.writestr(image_name, image_data)  # Write the image to the ZIP file in memory
    zip_buffer.seek(0)  # Go back to the start of the BytesIO buffer
    return zip_buffer

# Function to send the ZIP file via Gmail
def send_email_with_zip_in_memory(sender_email, app_password, receiver_email, subject, body, zip_buffer, zip_name):
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))

    # Attach the in-memory ZIP file
    part = MIMEBase('application', 'octet-stream')
    part.set_payload(zip_buffer.read())
    encoders.encode_base64(part)
    part.add_header('Content-Disposition', f'attachment; filename={zip_name}')
    msg.attach(part)

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, app_password)
        server.sendmail(sender_email, receiver_email, msg.as_string())
        server.quit()
        st.success(f"Email sent successfully to {receiver_email} with ZIP attachment.")
    except Exception as e:
        st.error(f"Failed to send email: {e}")

# Main function to tie everything together
def main():
    st.title("Google Images Scraper and Email Sender")
    
    # Input fields for the user
    keyword = st.text_input("Enter the keyword for image search (e.g., sunset, nature):")
    num_images = st.number_input("Number of images to download:", min_value=1, max_value=50, value=5)
    receiver_email = st.text_input("Enter receiver's email address:")
    subject = st.text_input("Enter the subject/title for the email:")
    
    sender_email='ridhimachoudhary505@gmail.com'
    app_password='uclc kzdn juii itmn'

    if st.button("Send Images"):
        if not keyword or not receiver_email or not subject:
            st.error("Please fill in all fields.")
        else:
            # Step 1: Scrape image URLs
            image_urls = scrape_google_images(keyword, num_images)
            
            # Step 2: Download images into memory
            if image_urls:
                image_data_list = download_images_in_memory(image_urls)

                # Step 3: Create ZIP file in memory
                zip_buffer = create_zip_in_memory(image_data_list)
                zip_name = f"{keyword}_images.zip"

                # Step 4: Send ZIP via email
                send_email_with_zip_in_memory(
                    sender_email=sender_email,
                    app_password=app_password,
                    receiver_email=receiver_email,
                    subject=subject,
                    body=f"Please find the images related to '{keyword}' attached.",
                    zip_buffer=zip_buffer,
                    zip_name=zip_name
                )

if __name__ == "__main__":
    main()
