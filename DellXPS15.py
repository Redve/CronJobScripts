import requests
from bs4 import BeautifulSoup
import smtplib
import sys

def main ():
    print("Running Dustin XPS 15 Price Check")
    check()

def check():
    print("Checking")
    
    smtp_server = 'smtp-mail.outlook.com'
    smtp_port = 587
    smtp_username = sys.argv[1]
    smtp_password = sys.argv[2]

    from_email = sys.argv[1]
    to_email = sys.argv[3]
    subject = 'Price Update on Dell XPS 15 on Dell.com'
    response = requests.get(
        'https://www.dell.com/sv-se/shop/b%C3%A4rbara-datorer-och-minidatorer-fr%C3%A5n-dell/xps-15-b%C3%A4rbar-dator/spd/xps-15-9530-laptop/cn95311cc',
    )
    print(response.status_code)

    soup = BeautifulSoup(response.content, 'html.parser')
    
    price = soup.find('span', class_='h3 font-weight-bold mb-1 text-nowrap sale-price')

    print(price.text)   

    body = 'The Current Price of the Dell XPS 15 on Dell.com is: ' + price.text
    message = f'Subject: {subject}\n\n{body}'

    with smtplib.SMTP(smtp_server, smtp_port) as smtp:
        smtp.starttls()
        smtp.login(smtp_username, smtp_password)
        smtp.sendmail(from_email, to_email, message)  



if __name__ == "__main__":
    main()