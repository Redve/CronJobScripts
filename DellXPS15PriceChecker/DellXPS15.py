import requests
from bs4 import BeautifulSoup
import smtplib
import sys

def main ():
    print("Running Dustin XPS 15 Price Check")
    check()

def check():
    print("Checking")
    file_path = "./DellXPS15PriceChecker/DellXPS15Price.txt"

    try:
        with open(file_path, 'r') as file:
            first_line = file.readline()
            print("The first line of the file is:", first_line)
    except FileNotFoundError:
        print(f"File '{file_path}' not found.")
    except Exception as e:
        print("An error occurred:", str(e))

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

    handled = price.text.replace('.', '')
    handled = handled.replace(' kr', '')
    handled = handled.replace(',00', '')


    if int(handled) != int(first_line):
        print("The price has changed")
        with open(file_path, 'w') as file:
            file.write(handled)
        print("The file has been updated")
        body = 'The Current Price of the Dell XPS 15 on Dell.com is: ' + price.text
        message = f'Subject: {subject}\n\n{body}'

        with smtplib.SMTP(smtp_server, smtp_port) as smtp:
            smtp.starttls()
            smtp.login(smtp_username, smtp_password)
            smtp.sendmail(from_email, to_email, message)
        print("Email sent")
    else:
        print("The price is the same as before")

if __name__ == "__main__":
    main()