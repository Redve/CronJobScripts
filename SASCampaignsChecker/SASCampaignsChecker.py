import requests
from bs4 import BeautifulSoup
import smtplib
import sys
import os
from urllib.parse import urljoin, urlparse

def main():
    print("Running SAS Campaigns Checker")
    check()

def check():
    print("Checking for new SAS campaigns")
    file_path = "./SASCampaignsChecker/SASCampaigns.txt"
    
    # Read existing campaign URLs
    known_urls = set()
    try:
        with open(file_path, 'r') as file:
            known_urls = set(line.strip() for line in file if line.strip())
            print(f"Found {len(known_urls)} known campaigns")
    except FileNotFoundError:
        print(f"File '{file_path}' not found. This appears to be the first run.")
    except Exception as e:
        print("An error occurred reading file:", str(e))
    
    # SMTP configuration
    smtp_server = 'smtp-mail.outlook.com'
    smtp_port = 587
    smtp_username = sys.argv[1]
    smtp_password = sys.argv[2]
    to_email = sys.argv[3]
    from_email = sys.argv[1]
    
    base_url = 'https://onlineshopping.flysas.com'
    
    # Start from base campaigns page to discover all listing pages
    base_campaigns_url = 'https://onlineshopping.flysas.com/sv-SE/kampanjer'
    
    try:
        # Discover all Swedish campaign pages
        # The numbered pages like /kampanjer/1, /kampanjer/2, etc. appear to be individual campaigns
        print(f"Discovering Swedish campaign pages from: {base_campaigns_url}")
        campaign_pages_to_check = set()
        
        # Try to discover available campaign pages from the base page
        try:
            response = requests.get(base_campaigns_url, timeout=30)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                # Find all links to Swedish campaign pages
                for link in soup.find_all('a', href=True):
                    href = link.get('href', '')
                    if href.startswith('/'):
                        full_url = urljoin(base_url, href)
                    elif href.startswith('http'):
                        full_url = href
                    else:
                        full_url = urljoin(base_campaigns_url, href)
                    
                    parsed = urlparse(full_url)
                    path_parts = [p for p in parsed.path.strip('/').split('/') if p]
                    
                    # Look for Swedish campaign pages: /sv-SE/kampanjer/{number}
                    if (len(path_parts) == 3 and 
                        path_parts[0] == 'sv-SE' and 
                        path_parts[1] == 'kampanjer' and 
                        path_parts[2].isdigit()):
                        campaign_pages_to_check.add(full_url)
        except Exception as e:
            print(f"Error discovering campaign pages: {str(e)}")
        
        # Also check the base page itself
        campaign_pages_to_check.add(base_campaigns_url)
        
        # If no specific pages found, try common patterns as fallback (check pages 1-20)
        if len(campaign_pages_to_check) == 1:
            print("No specific campaign pages discovered, checking common patterns...")
            for page_num in range(1, 21):
                campaign_pages_to_check.add(f'{base_campaigns_url}/{page_num}')
        else:
            # Still check a range to make sure we don't miss any
            for page_num in range(1, 21):
                campaign_pages_to_check.add(f'{base_campaigns_url}/{page_num}')
        
        print(f"Found {len(campaign_pages_to_check)} Swedish campaign pages to check")
        
        # Now check each page and treat valid Swedish campaign pages as campaigns
        campaigns = []
        current_campaign_urls = set()
        
        for campaign_url in sorted(campaign_pages_to_check):
            print(f"Checking campaign page: {campaign_url}")
            try:
                response = requests.get(campaign_url, timeout=30, allow_redirects=False)
                print(f"  Response status code: {response.status_code}")
                
                # Only consider pages that exist (200) or redirect to valid pages
                if response.status_code == 200:
                    parsed = urlparse(campaign_url)
                    path_parts = [p for p in parsed.path.strip('/').split('/') if p]
                    
                    # Only track Swedish campaign pages
                    if (len(path_parts) >= 2 and 
                        path_parts[0] == 'sv-SE' and 
                        path_parts[1] == 'kampanjer'):
                        
                        # This is a valid Swedish campaign page
                        current_campaign_urls.add(campaign_url)
                        
                        # Extract campaign details if it's a new campaign
                        if campaign_url not in known_urls:
                            soup = BeautifulSoup(response.content, 'html.parser')
                            
                            # Try to extract title
                            title = "Untitled Campaign"
                            h1 = soup.find('h1')
                            if h1:
                                title = h1.get_text(strip=True)
                            else:
                                # Try to find title in other ways
                                title_elem = soup.find(['h2', 'h3'], string=lambda text: text and 'kampanj' in text.lower())
                                if title_elem:
                                    title = title_elem.get_text(strip=True)
                            
                            # Try to find description
                            description = ""
                            # Look for common description containers
                            desc_elem = soup.find(['p', 'div'], class_=lambda x: x and ('desc' in str(x).lower() or 'text' in str(x).lower() or 'content' in str(x).lower()))
                            if desc_elem:
                                description = desc_elem.get_text(strip=True)[:200]
                            
                            campaigns.append({
                                'url': campaign_url,
                                'title': title,
                                'description': description
                            })
                
            except requests.RequestException as e:
                print(f"  Error fetching {campaign_url}: {str(e)}")
                continue
        
        print(f"Found {len(current_campaign_urls)} total campaigns")
        print(f"Found {len(campaigns)} new campaigns")
        
        # On first run (no known URLs), don't send notifications
        is_first_run = len(known_urls) == 0
        
        if is_first_run:
            print("First run detected. Populating campaigns file without sending notifications.")
        
        # If there are new campaigns and it's not the first run, send email
        if campaigns and not is_first_run:
            print("New campaigns detected! Preparing email...")
            
            subject = f'New SAS Campaigns Found ({len(campaigns)} new)'
            body = f'New campaigns have been found on SAS Shopping:\n\n'
            
            for i, campaign in enumerate(campaigns, 1):
                body += f'{i}. {campaign["title"]}\n'
                body += f'   URL: {campaign["url"]}\n'
                if campaign["description"]:
                    body += f'   Description: {campaign["description"]}\n'
                body += '\n'
            
            body += f'\nTotal campaigns now: {len(current_campaign_urls)}\n'
            body += f'View all campaigns: {base_campaigns_url}\n'
            
            message = f'Subject: {subject}\n\n{body}'
            
            try:
                with smtplib.SMTP(smtp_server, smtp_port) as smtp:
                    smtp.starttls()
                    smtp.login(smtp_username, smtp_password)
                    smtp.sendmail(from_email, to_email, message)
                print("Email sent successfully")
            except Exception as e:
                print(f"Error sending email: {str(e)}")
        else:
            print("No new campaigns found")
        
        # Update the stored URLs file with all current campaigns
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'w') as file:
                for url in sorted(current_campaign_urls):
                    file.write(url + '\n')
            print(f"Updated campaigns file with {len(current_campaign_urls)} campaigns")
        except Exception as e:
            print(f"Error writing to file: {str(e)}")
            
    except requests.RequestException as e:
        print(f"Error fetching page: {str(e)}")
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

