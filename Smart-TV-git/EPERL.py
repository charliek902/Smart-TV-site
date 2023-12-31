import time
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import mysql.connector
from mysql.connector import Error
import requests
import csv
import datetime


def timestamp_to_datetime(timestamp):
    dt = datetime.datetime.fromtimestamp(timestamp)
    return dt.strftime("%Y-%m-%d %H:%M:%S")

def convert_to_sql_date(date_list):
    year, month, day = date_list
    sql_date = datetime.date(year, month, day)
    return sql_date

def extract_date(datetime_str):
    datetime_obj = datetime.datetime.strptime(datetime_str, '%Y-%m-%d %H:%M:%S')
    date_only = datetime_obj.date()
    return date_only


def crawl_page(page_number):
    url = 'https://eprel.ec.europa.eu/api/products/electronicdisplays'
    params = {
        '_page': page_number,
        '_limit': 25,
        'sort0': 'onMarketStartDateTS',
        'order0': 'DESC',
        'sort1': 'energyClass',
        'order1': 'DESC'
    }

    response = requests.get(url, params=params)
    print(response.status_code)


    try:
        data = response.json()
        print(data)
        hits = data['hits']  

        for item in hits:
            time.sleep(1)
            try:
                model_number = item['modelIdentifier']
                manufacturer = item['organisation']['organisationName']
                power_on_mode_sdr = item['powerOnModeSDR']
                power_on_mode_hdr = item['powerOnModeHDR']
                energy_class_sdr = item['energyClassSDR']
                energy_class = item['energyClass']
                energy_class_hdr = item['energyClassHDR']
                screen_area = item['diagonalInch']
                first_publication_date = item['firstPublicationDateTS']
                on_market_start_date = item['onMarketStartDate']
                on_market_start_date = convert_to_sql_date(on_market_start_date)
                first_publication = timestamp_to_datetime(first_publication_date)
                first_publication = extract_date(first_publication)



                insert_into_database(model_number, manufacturer, power_on_mode_sdr, power_on_mode_hdr,
                                     energy_class_sdr, energy_class, energy_class_hdr, screen_area, 
                                     first_publication, on_market_start_date)

          
                insert_into_csv(model_number, manufacturer, power_on_mode_sdr, power_on_mode_hdr,
                                energy_class_sdr, energy_class, energy_class_hdr, screen_area, 
                                first_publication, on_market_start_date)

            except KeyError as e:
                print("Skipping device due to missing key:", e)


        if len(data) > 0:
            page_number += 1
            random1 = random.randint(0,9)
            time.sleep(random1)
            crawl_page(page_number)
        else:
            print("No more pages to crawl.")
            exit()

    except requests.exceptions.JSONDecodeError as e:
        send_email("JSON decoding error occurred on page " + str(page_number), str(e))
        print("JSON decoding error occurred:", str(e))
        retry_crawl_page(page_number)
        exit()



def validAPIRequest(page_number):
    url = 'https://eprel.ec.europa.eu/api/products/electronicdisplays'
    params = {
        '_page': page_number,
        '_limit': 25,
        'sort0': 'onMarketStartDateTS',
        'order0': 'DESC',
        'sort1': 'energyClass',
        'order1': 'DESC'
    }

    response = requests.get(url, params=params)
    if response.status_code == 200:
        return True
    else:
        return False


def insert_into_database(model_number, manufacturer, power_on_mode_sdr, power_on_mode_hdr,
                         energy_class_sdr, energy_class, energy_class_hdr, screen_area, first_publication, 
                         on_market_start_date):
    try:
        connection = mysql.connector.connect(
            host="####",
            user="####",
            password="#####",
            database="####"
        )

        if connection.is_connected():
            cursor = connection.cursor()
            query = "INSERT INTO displays (model_number, manufacturer, power_on_mode_sdr, power_on_mode_hdr, " \
                    "energy_class_sdr, energy_class, energy_class_hdr, screen_area, first_publication_date, on_market_start_date ) " \
                    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"

            values = (model_number, manufacturer, power_on_mode_sdr, power_on_mode_hdr,
                      energy_class_sdr, energy_class, energy_class_hdr, screen_area, first_publication, on_market_start_date)

            cursor.execute(query, values)
            connection.commit()
            cursor.close()

    except Error as e:
        print("Error inserting data into the database:", e)
        retry_crawl_page(page_number)


def insert_into_csv(model_number, manufacturer, power_on_mode_sdr, power_on_mode_hdr,
                    energy_class_sdr, energy_class, energy_class_hdr, screen_area, first_publication, on_market_start_date):
    csv_file_path = "/Users/charlieknox/EPREL.csv"
    try:
        with open(csv_file_path, "a", newline="") as csvfile:
            csv_writer = csv.writer(csvfile)
            csv_writer.writerow([model_number, manufacturer, power_on_mode_sdr, power_on_mode_hdr,
                                 energy_class_sdr, energy_class, energy_class_hdr, screen_area, first_publication, on_market_start_date])
        print("Data exported to CSV successfully")
    except Exception as e:
        error_message = 'An error occurred while exporting data to CSV: ' + str(e)
        send_email("Error occurred during data export", error_message)
        retry_crawl_page(page_number)
    
def retry_crawl_page(page_number):
    random = random.randint(0,9)
    time.sleep(5 + 10*random)
    crawl_page(page_number)


def send_email(subject, body):
    sender_email = "charlieknox2@hotmail.com"
    receiver_email = "ir22593@bristol.ac.uk"
    password = "#rl764jghung"

    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = receiver_email
    message["Subject"] = subject

    message.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP("smtp.office365.com", 587) as server:
            server.starttls()
            server.login(sender_email, password)
            server.send_message(message)
    except Exception as e:
        error_message = 'An error occurred while sending the email: ' + str(e)
        print(error_message)


page_number = 1
crawl_page(page_number)



