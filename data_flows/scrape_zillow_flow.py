import requests
import pandas as pd
from bs4 import BeautifulSoup  # Html search tool
import re  # Regular expressions
from datetime import date
from prefect import flow, task

"""

Author: Chase Sommer
Email: robertchasesommer@gmail.com

Summary:
This script scrapes Zillow.com for all homes in the city set in get_all_urls().
It collect simple metrics like price, beds, and baths. Additional data will be 
added at a later date.

"""

# Adding a header like this circumvents captchas on Zillow.
request_headers = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
    "accept-encoding": "gzip, deflate, br",
    "accept-language": "en-US,en;q=0.8",
    "upgrade-insecure-requests": "1",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36",
}


@task
def get_all_urls(city_state_abbr="raleigh-nc/"):
    """Collects all homedetails identifiers into a list to be later combined
    into a full url.

    Args:
        city_state_abbr (string): city_state_abbr

    Returns:
        list: flat_full_list_urls. A list of numbers converted into strings.

    """

    url_setup = "https://www.zillow.com/" + city_state_abbr
    main_request_setup = requests.get(url_setup, headers=request_headers)
    page_soup = BeautifulSoup(main_request_setup.content).find_all(
        "span", class_="Text-c11n-8-73-8__sc-aiai24-0 bKahKV"
    )

    page_soup_max_number = int(
        re.search(
            "Page <!-- -->1<!-- --> of <!-- -->(.+?)</span>", str(page_soup)
        ).group(1)
    )

    full_list_urls = []

    for page_number in range(1, page_soup_max_number + 1):
        url = "https://www.zillow.com/" + city_state_abbr + str(page_number) + "_p"
        main_request = requests.get(url, headers=request_headers)
        main_re_search = list(
            set(
                re.findall(
                    "https://www.zillow.com/homedetails/(.+?)_zpid",
                    str(main_request.content),
                )
            )
        )
        full_list_urls.append(main_re_search)

    flat_full_list_urls = [item for sublist in full_list_urls for item in sublist]

    return flat_full_list_urls


@task
def get_full_url_branch(re_search_set):
    """Uses a list of homedetails and converts them into usable urls. These urls
    will be used to go to each home and scrape its details.

    Args:
        re_search_set (list): List of homedetails.

    Returns:
        list: full_url_list. A list of full urls ready for data-scraping.

    """

    full_url_list = []

    for url in re_search_set:
        # print(url)
        full_url = "https://www.zillow.com/homedetails/" + url + "_zpid"
        # print(full_url)
        full_url_list.append(full_url)

    return full_url_list


@task
def get_request_soup_and_parse(list_of_full_urls_to_scrape):
    """Scrapes Zillow homedetails pages for data like price, beds, baths and
    more.

    Args:
        list_of_full_urls_to_scrape (list): List of full, usable urls that point 
        to each house in the state.

    Returns:
        list: final_data_list. A list of lists including all scraped raw data 
        ready for conversion to a dataframe and cleaning.

    """

    final_data_list = []

    for url in list_of_full_urls_to_scrape:
        branch_response = requests.get(url, headers=request_headers)
        soup = BeautifulSoup(branch_response.content, "html.parser")

        raw_price_soup = soup.find_all(
            "span",
            class_="Text-c11n-8-73-0__sc-aiai24-0 dpf__sc-1me8eh6-0 kGdfMs fzJCbY",
        )

        # Price
        raw_price_soup = str(
            soup.find_all(
                "span",
                class_="Text-c11n-8-73-0__sc-aiai24-0 dpf__sc-1me8eh6-0 kGdfMs fzJCbY",
            )
        )
        price_match_object = re.search("<span>(.+?)</span>", raw_price_soup)
        price = price_match_object.group(1)

        # Attributes list: 0 Bed, 1 bath,  2 sqft, 3 days on zillow, 5 views, 6 saves
        raw_bed_soup = str(soup.find_all("strong"))
        raw_bed_soup_list = raw_bed_soup.split(
            ", "
        )  # Sweet jambalaya I spent 4 hours on this.

        count_beds = re.search("<strong>(.+?)</strong>", raw_bed_soup_list[0]).group(1)
        count_baths = re.search("<strong>(.+?)</strong>", raw_bed_soup_list[1]).group(1)
        sq_ft = re.search("<strong>(.+?)</strong>", raw_bed_soup_list[2]).group(1)
        days_on_zillow = re.search("<strong>(.+?)", raw_bed_soup_list[3]).group(1)
        # count_views = re.search("<strong>(.+?)</strong>", raw_bed_soup_list[4])#.group(1)
        # count_saves = re.search("<strong>(.+?)</strong>", raw_bed_soup_list[5])#.group(1)

        raw_address_soup = soup.find("h1")
        # Done
        address = str(raw_address_soup)
        address_1 = re.search("kHeRng(.+?)<!--", address).group(1)[2:]
        address_2 = re.search("<!-- -->(.+?)</h1>", address).group(1)[9:]
        address_full = address_1 + " " + address_2

        final_data_list.append(
            [address_full, price, count_beds, count_baths, sq_ft, days_on_zillow]
        )  # , count_views, count_saves])

    return final_data_list


@task
def to_df_and_clean(raw_data):
    """Converts list of lists to a dataframe and performs light transformations
    
    Args:
        raw_data (list): A list of lists including a scraped data from homedetails.

    Returns:
        Output CSV ready for upload into database.
    """
    zillow_df = pd.DataFrame(
        raw_data,
        columns=[
            "address_full",
            "price",
            "count_beds",
            "count_baths",
            "sq_ft",
            "days_on_zillow",
        ],
    )

    zillow_df[["address", "city", "state_zip"]] = zillow_df["address_full"].str.split(
        ",", expand=True
    )
    zillow_df["state_zip"] = zillow_df["state_zip"].str.strip()
    zillow_df[["state_abrev", "zip_code"]] = zillow_df["state_zip"].str.split(
        " ", expand=True
    )
    zillow_df["date_scraped"] = date.today()

    zillow_df.to_csv(
        "../data_flows_output/{today}_zillow_scrape_output.csv".format(
            today=date.today()
        ),
        header=True,
    )


@flow
def zillow_scrape_flow():
    """Runs the entire script as a Prefect flow.
    """

    url_bits = get_all_urls()
    urls = get_full_url_branch(url_bits)
    parsed_data = get_request_soup_and_parse(urls)
    to_df_and_clean(parsed_data)


# Run the flow
zillow_scrape_flow()
