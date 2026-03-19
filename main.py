# Importing Libraries
from nicegui import ui
import requests
import cloudscraper
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
import platform
from functools import cache
import re
import datetime
import time
import json
from typing import Any
DEBUG_LOG_PATH: str = "/Users/kevinlin/Documents/GitHub/supremebot/.cursor/debug-003a64.log"


# #region agent log
def _agent_log(*, hypothesisId: str, location: str, message: str, data: dict) -> None:
    try:
        payload = {
            "sessionId": "003a64",
            "runId": "pre-fix",
            "hypothesisId": hypothesisId,
            "location": location,
            "message": message,
            "data": data,
            "timestamp": int(time.time() * 1000),
        }
        with open(DEBUG_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")
    except Exception:
        pass


# #endregion

from bot import Bot

# Nation and zones codes dictionary constants
NATIONS: dict = {
    "United States": "US",
    "Austria": "AT",
    "Belgium": "BE",
    "Bulgaria": "BG",
    "Croatia": "HR",
    "Cyprus": "CY",
    "Czechia": "CZ",
    "Denmark": "DK",
    "Estonia": "EE",
    "Finland": "FI",
    "France": "FR",
    "Germany": "DE",
    "Greece": "GR",
    "Hungary": "HU",
    "Iceland": "IS",
    "Ireland": "IE",
    "Italy": "IT",
    "Latvia": "LV",
    "Lithuania": "LT",
    "Luxembourg": "LU",
    "Malta": "MT",
    "Monaco": "MC",
    "Netherlands": "NL",
    "Norway": "NO",
    "Poland": "PL",
    "Portugal": "PT",
    "Romania": "RO",
    "Slovakia": "SK",
    "Slovenia": "SI",
    "Spain": "ES",
    "Sweden": "SE",
    "Switzerland": "CH",
    "Turkey": "TR",
}
ZONES: dict = {
    "United States": {
        "Alabama": "AL",
        "Alaska": "AK",
        "Arizona": "AZ",
        "Arkansas": "AR",
        "California": "CA",
        "Colorado": "CO",
        "Connecticut": "CT",
        "Delaware": "DE",
        "District of Columbia": "DC",
        "Florida": "FL",
        "Georgia": "GA",
        "Hawaii": "HI",
        "Idaho": "ID",
        "Illinois": "IL",
        "Indiana": "IN",
        "Iowa": "IA",
        "Kansas": "KS",
        "Kentucky": "KY",
        "Louisiana": "LA",
        "Maine": "ME",
        "Maryland": "MD",
        "Massachusetts": "MA",
        "Michigan": "MI",
        "Minnesota": "MN",
        "Mississippi": "MS",
        "Missouri": "MO",
        "Montana": "MT",
        "Nebraska": "NE",
        "Nevada": "NV",
        "New Hampshire": "NH",
        "New Jersey": "NJ",
        "New Mexico": "NM",
        "New York": "NY",
        "North Carolina": "NC",
        "North Dakota": "ND",
        "Ohio": "OH",
        "Oklahoma": "OK",
        "Oregon": "OR",
        "Pennsylvania": "PA",
        "Rhode Island": "RI",
        "South Carolina": "SC",
        "South Dakota": "SD",
        "Tennessee": "TN",
        "Texas": "TX",
        "Utah": "UT",
        "Vermont": "VT",
        "Virginia": "VA",
        "Washington": "WA",
        "West Virginia": "WV",
        "Wisconsin": "WI",
        "Wyoming": "WY",
    },
    "Ireland": {
        "Carlow": "CW",
        "Cavan": "CN",
        "Clare": "CE",
        "Cork": "CO",
        "Donegal": "DL",
        "Dublin": "D",
        "Galway": "G",
        "Kerry": "KY",
        "Kildare": "KE",
        "Kilkenny": "KK",
        "Laois": "LS",
        "Leitrim": "LM",
        "Limerik": "LK",
        "Longford": "LD",
        "Louth": "LH",
        "Mayo": "MO",
        "Meath": "MH",
        "Monaghan": "MN",
        "Offaly": "OY",
        "Roscommon": "RN",
        "Sligo": "SO",
        "Tipperary": "TA",
        "Waterford": "WD",
        "Westmeath": "WH",
        "Wexford": "WX",
        "Wicklow": "WW",
    },
    "Italy": {
        "Agrigento": "AG",
        "Alessandria": "AL",
        "Ancona": "AN",
        "Aosta": "AO",
        "Arezzo": "AR",
        "Ascoli Piceno": "AP",
        "Asti": "AT",
        "Avellino": "AV",
        "Bari": "BA",
        "Barletta-Andria-Trani": "BT",
        "Belluno": "BL",
        "Benevento": "BN",
        "Bergamo": "BG",
        "Biella": "BI",
        "Bologna": "BO",
        "Bolzano": "BZ",
        "Brescia": "BS",
        "Brindisi": "BR",
        "Cagliari": "CA",
        "Caltanissetta": "CL",
        "Campobasso": "CB",
        "Carbonia-Iglesias": "CI",
        "Caserta": "CE",
        "Catania": "CT",
        "Catanzaro": "CZ",
        "Chieti": "CH",
        "Como": "CO",
        "Cosenza": "CS",
        "Cremona": "CR",
        "Crotone": "KR",
        "Cuneo": "CN",
        "Enna": "EN",
        "Fermo": "FM",
        "Ferrara": "FE",
        "Firenze": "FI",
        "Foggia": "FG",
        "Forlì-Cesena": "FC",
        "Frosinone": "FR",
        "Genova": "GE",
        "Gorizia": "GO",
        "Grosseto": "GR",
        "Imperia": "IM",
        "Isernia": "IS",
        "La Spezia": "SP",
        "L'Aquila": "AQ",
        "Latina": "LT",
        "Lecce": "LE",
        "Lecco": "LC",
        "Livorno": "LI",
        "Lodi": "LO",
        "Lucca": "LU",
        "Macerata": "MC",
        "Mantova": "MN",
        "Massa-Carrara": "MS",
        "Matera": "MT",
        "Medio Campidano": "VS",
        "Messina": "ME",
        "Milano": "MI",
        "Modena": "MO",
        "Monza E Brianza": "MB",
        "Napoli": "NA",
        "Novara": "NO",
        "Nuoro": "NU",
        "Ogliastra": "OG",
        "Olbia-Tempio": "OT",
        "Oristano": "OR",
        "Padova": "PD",
        "Palermo": "PA",
        "Parma": "PR",
        "Pavia": "PV",
        "Perugia": "PG",
        "Pesaro E Urbino": "PU",
        "Pescara": "PE",
        "Piacenza": "PC",
        "Pisa": "PI",
        "Pistoia": "PT",
        "Pordenone": "PN",
        "Potenza": "PZ",
        "Prato": "PO",
        "Ragusa": "RG",
        "Ravenna": "RA",
        "Reggio Calabria": "RC",
        "Reggio Emilia": "RE",
        "Rieti": "RI",
        "Rimini": "RN",
        "Roma": "RM",
        "Rovigo": "RO",
        "Salerno": "SA",
        "Sassari": "SS",
        "Savona": "SV",
        "Siena": "SI",
        "Siracusa": "SR",
        "Sondrio": "SO",
        "Taranto": "TA",
        "Teramo": "TE",
        "Terni": "TR",
        "Torino": "TO",
        "Trapani": "TP",
        "Trento": "TN",
        "Treviso": "TV",
        "Trieste": "TS",
        "Udine": "UD",
        "Varese": "VA",
        "Venezia": "VE",
        "Verbano-Cusio-Ossola": "VB",
        "Vercelli": "VC",
        "Verona": "VR",
        "Vibo Valentia": "VV",
        "Vicenza": "VI",
        "Viterbo": "VT",
    },
    "Portugal": {
        "Azores": "PT-20",
        "Aveiro": "PT-01",
        "Beja": "PT-02",
        "Braga": "PT-03",
        "Bragança": "PT-04",
        "Castelo Branco": "PT-05",
        "Coimbra": "PT-06",
        "Évora": "PT-07",
        "Faro": "PT-08",
        "Guarda": "PT-09",
        "Leiria": "PT-10",
        "Lisbon": "PT-11",
        "Madeira": "PT-30",
        "Portalegre": "PT-12",
        "Porto": "PT-13",
        "Santarém": "PT-14",
        "Setúbal": "PT-15",
        "Viana do Castelo": "PT-16",
        "Vila Real": "PT-17",
        "Viseu": "PT-18",
    },
    "Romania": {
        "Alba": "AB",
        "Arad": "AR",
        "Argeș": "AG",
        "Bacău": "BC",
        "Bihor": "BH",
        "Bistrița-Năsăud": "BN",
        "Botoșani": "BT",
        "Brăila": "BR",
        "Brașov": "BV",
        "București": "B",
        "Buzău": "BZ",
        "Călărași": "CL",
        "Caraș-Severin": "CS",
        "Cluj": "CJ",
        "Constanța": "CT",
        "Covasna": "CV",
        "Dâmbovița": "DB",
        "Dolj": "DJ",
        "Galați": "GL",
        "Giurgiu": "GR",
        "Gorj": "GJ",
        "Harghita": "HR",
        "Hunedoara": "HD",
        "Ialomița": "IL",
        "Iași": "IS",
        "Ilfov": "IF",
        "Maramureș": "MM",
        "Mehedinți": "MH",
        "Mureș": "MS",
        "Neamț": "NT",
        "Olt": "OT",
        "Prahova": "PH",
        "Sălaj": "SJ",
        "Satu Mare": "SM",
        "Sibiu": "SB",
        "Suceava": "SV",
        "Teleorman": "TR",
        "Timiș": "TM",
        "Tulcea": "TL",
        "Vâlcea": "VL",
    },
    "Spain": {
        "A Coruña": "C",
        "Álava": "VI",
        "Albacete": "AB",
        "Alicante": "A",
        "Almería": "AL",
        "Asturias": "O",
        "Ávila": "AV",
        "Badajoz": "BA",
        "Barcelona": "B",
        "Burgos": "BU",
        "Cáceres": "CC",
        "Cádiz": "CA",
        "Cantabria": "S",
        "Castellón": "CS",
        "Ciudad Real": "CR",
        "Córdoba": "CO",
        "Cuenca": "CU",
        "Gerona": "GI",
        "Granada": "GR",
        "Guadalajara": "GU",
        "Guipúzcoa": "SS",
        "Huelva": "H",
        "Huesca": "HU",
        "Islas Balears": "PM",
        "Jaén": "J",
        "La Coruña": "C",
        "La Rioja": "LO",
        "Las Palmas": "GC",
        "León": "LE",
        "Lérida": "L",
        "Lugo": "LU",
        "Madrid": "M",
        "Málaga": "MA",
        "Murcia": "MU",
        "Navarra": "NA",
        "Orense": "OR",
        "Palencia": "P",
        "Pontevedra": "PO",
        "Salamanca": "SA",
        "Santa Cruz de Tenerife": "TF",
        "Segovia": "SG",
        "Sevilla": "SE",
        "Soria": "SO",
        "Tarragona": "T",
        "Teruel": "TE",
        "Toledo": "TO",
        "Valencia": "V",
        "Valladolid": "VA",
        "Vizcaya": "BI",
        "Zamora": "ZA",
        "Zaragoza": "Z",
    },
}

# Setting a user-agent to avoid 403 forbidden error
headers: dict[str, str] = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/58.0.3029.110 Safari/537.3"
}


# Function to fetch Supreme Community pages with a browser-like client
def get(url: str) -> requests.models.Response:
    """
    Fetch a web page using a browser-like client with a requests fallback.

    Parameters
    ----------
    url : str
        The URL of the web page to fetch.

    Returns
    -------
    requests.models.Response
        The HTTP response object resulting from the GET request.
    """
    try:
        scraper: cloudscraper.CloudScraper = cloudscraper.create_scraper(
            browser={
                "browser": "chrome",
                "platform": platform.system().lower(),
            },
        )
        return scraper.get(
            url,
            headers={
                **headers,
                "Cache-Control": "no-cache",
                "Pragma": "no-cache",
            },
            timeout=15,
        )
    except Exception:
        return requests.get(
            url,
            headers={
                **headers,
                "Cache-Control": "no-cache",
                "Pragma": "no-cache",
            },
            timeout=15,
        )


def get_rendered_html(url: str) -> str:
    """
    Render a page in headless Chromium and return the resulting HTML.

    This is used as a fallback when Supreme Community serves content
    client-side and the plain HTTP response does not include item data.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            page = browser.new_page()
            try:
                page.goto(url, wait_until="networkidle", timeout=45000)
            except Exception:
                page.goto(url, wait_until="domcontentloaded", timeout=45000)

            # Give client-side filters and item grids time to hydrate.
            page.wait_for_timeout(4000)
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(1000)
            return page.content()
        finally:
            browser.close()


# Util function to convert a date to a certain format
@cache
def convert_date(date_str: str) -> str:
    """
    Convert a date string between ISO format and human-readable format.

    If the input date is in ISO format (`YYYY-MM-DD`), it is converted to a
    human-readable format with an ordinal day suffix (e.g. `5th March 2026`).
    If the input date is already in human-readable format with an ordinal
    suffix, it is converted back to ISO format.

    The result is cached to avoid repeated parsing of the same date strings.

    Parameters
    ----------
    date_str : str
        The date string to convert. Supported formats are:
        - ISO format: `YYYY-MM-DD`
        - Human-readable format: `5th March 2026`

    Returns
    -------
    str
        The converted date string in the opposite format.
    """
    # Case 1: ISO format -> Human readable
    if re.match(r"\d{4}-\d{2}-\d{2}$", date_str):
        date: datetime.datetime = datetime.datetime.strptime(date_str, "%Y-%m-%d")
        day: int = date.day
        month: str = date.strftime("%B")
        year: int = date.year

        if 10 <= day % 100 <= 20:
            suffix: str = "th"
        else:
            suffix: str = {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")

        return f"{day}{suffix} {month} {year}"

    # Case 2: Human readable -> ISO format
    else:
        cleaned = re.sub(r"(\d+)(st|nd|rd|th)", r"\1", date_str)
        date = datetime.datetime.strptime(cleaned, "%d %B %Y")
        return date.strftime("%Y-%m-%d")


def parse_human_date(date_str: str) -> datetime.datetime:
    """
    Parse a human-readable date with an ordinal suffix into a datetime object.

    Parameters
    ----------
    date_str : str
        Date string such as `19th March 2026`.

    Returns
    -------
    datetime.datetime
        Parsed datetime for sorting and comparisons.
    """
    cleaned = re.sub(r"(\d+)(st|nd|rd|th)", r"\1", date_str)
    return datetime.datetime.strptime(cleaned, "%d %B %Y")


def extract_drop_dates_from_html(html: str) -> list[str]:
    """
    Extract available droplist dates from a Supreme Community season page.
    """
    soup: BeautifulSoup = BeautifulSoup(html, "html.parser")
    dates_href: list = soup.find_all("a", {"class": "droplist-row"})
    dates: list[str] = [a["href"].split("/")[-2] for a in dates_href]
    return sorted(
        {convert_date(date) for date in dates},
        key=parse_human_date,
        reverse=True,
    )


# Util function to get all the drop dates for the current release
def get_drop_dates() -> list:
    """
    Retrieve all drop dates for the current Supreme release season.

    This function fetches the HTML content from the SupremeCommunity droplists
    page for the Spring/Summer 2026 season and parses it to extract all release
    dates.

    Returns
    -------
    list of str
        A list of drop dates as strings. Returns an empty list if the page
        could not be fetched successfully.
    """

    # Drops Site
    url: str = "https://www.supremecommunity.com/season/spring-summer2026/droplists/"

    # Fetching the source code
    response: requests.models.Response = get(url)
    if response.status_code == 200:
        formatted_dates: list[str] = extract_drop_dates_from_html(response.text)
        if formatted_dates:
            return formatted_dates

    try:
        rendered_html: str = get_rendered_html(url)
        return extract_drop_dates_from_html(rendered_html)
    except Exception:
        pass

    return list()


def get_item_divs(html: str, item_category: str) -> list:
    """
    Extract droplist item containers for the selected category.
    """
    soup: BeautifulSoup = BeautifulSoup(html, "html.parser")
    return [
        item
        for item in soup.select(f'[data-category="{item_category.lower()}"]')
        if item.find("h3", {"class": "item-name"})
    ]


def get_available_categories(html: str) -> list[str]:
    """
    Extract the distinct category keys present in a droplist page.
    """
    soup: BeautifulSoup = BeautifulSoup(html, "html.parser")
    return sorted(
        {
            item["data-category"].strip()
            for item in soup.select("[data-category]")
            if item.get("data-category")
        }
    )


def append_debug_message(debug_info: dict, message: str) -> None:
    """
    Append a concise debug message while keeping the panel readable.
    """
    debug_info.setdefault("messages", []).append(message)
    debug_info["messages"] = debug_info["messages"][-8:]


# Util function to fetch all information based on drop date and item category
def fetch_items(drop_date: str, item_category: str) -> tuple[dict, dict]:
    """
    Fetch all item information for a specific drop date and category from SupremeCommunity.

    This function retrieves items released on a given drop date and belonging to a
    specific category. It collects the item's name, price, image URL, available
    colors, product link, and votes (likes/dislikes). The "Tops" category is
    internally converted to "tops-sweaters".

    Parameters
    ----------
    drop_date : str
        The drop date of the items, expected in a format compatible with `convert_date`.
    item_category : str
        The category of items to fetch (e.g., "Tops", "Accessories").

    Returns
    -------
    tuple[dict, dict]
        The fetched items and a debug payload describing how the scrape behaved.
    """

    # Converting the tops-sweater option
    if item_category == "Tops":
        item_category: str = "tops-sweaters"

    # Constructing URL based on the Drop Date
    url: str = (
        f"https://www.supremecommunity.com/season/spring-summer2026/droplist/{convert_date(drop_date)}/"
    )

    # Creating an Object to store the fetched items
    items_dict: dict = dict()
    debug_info: dict = {
        "selected_date": drop_date,
        "selected_category": item_category,
        "url": url,
        "http_status": "not-requested",
        "http_matches": 0,
        "rendered_matches": 0,
        "source": "none",
        "items_built": 0,
        "detail_pages_ok": 0,
        "detail_pages_failed": 0,
        "available_categories": [],
        "messages": [],
    }

    # Initializing item_divs to an empty list
    item_divs: list = list()

    # Fetching all items of a certain type
    try:
        response: requests.models.Response = get(url)
        debug_info["http_status"] = response.status_code
        if response.status_code == 200:
            item_divs = get_item_divs(response.text, item_category)
            debug_info["http_matches"] = len(item_divs)
            debug_info["available_categories"] = get_available_categories(response.text)
            if item_divs:
                debug_info["source"] = "http"
    except Exception as e:
        append_debug_message(debug_info, f"http fetch failed: {type(e).__name__}: {e}")

    # Fallback to a rendered browser page for unreleased drops that are injected with JS
    if not item_divs:
        try:
            rendered_html: str = get_rendered_html(url)
            item_divs = get_item_divs(rendered_html, item_category)
            debug_info["rendered_matches"] = len(item_divs)
            if not debug_info["available_categories"]:
                debug_info["available_categories"] = get_available_categories(
                    rendered_html
                )
            if item_divs:
                debug_info["source"] = "rendered"
            else:
                append_debug_message(
                    debug_info, "rendered fallback found 0 matching category nodes"
                )
        except Exception:
            append_debug_message(debug_info, "rendered fallback failed")

    # Storing Items' Infos
    for item in item_divs:
        try:
            name_tag = item.find("h3", {"class": "item-name"})
            link_tag = item.find("a", href=True)
            image_tag = item.find("img")
            item_name: str = (
                name_tag.text.replace("\n", "").strip() if name_tag else "Unknown Item"
            )
            item_price_tag = item.find("span", {"class": "item-price"})
            item_price: str = (
                item_price_tag.text.replace("\n", "").split("/")[0].strip()
                if item_price_tag
                else "None"
            )
            item_image: str = image_tag["src"] if image_tag and image_tag.get("src") else ""
            item_full_link: str = (
                f'https://www.supremecommunity.com{link_tag["href"]}'
                if link_tag
                else url
            )
            item_type: str = item.get("data-category", item_category).strip()

            item_colors: list[str] = []
            item_votes: tuple[str, str] = ("0", "0")

            try:
                detail_response: requests.models.Response = get(item_full_link)
                if detail_response.status_code == 200:
                    debug_info["detail_pages_ok"] += 1
                    detail_soup: BeautifulSoup = BeautifulSoup(
                        detail_response.text, "html.parser"
                    )
                    color_div = detail_soup.find("div", {"class": "colorway-list"})
                    if color_div:
                        item_colors = [
                            color.text.replace("\n", "").strip()
                            for color in color_div.find_all(
                                "span", {"class": "colorway-tag"}
                            )
                            if color.text
                        ]
                    upvote = detail_soup.find("span", {"id": "upvote-count"})
                    downvote = detail_soup.find("span", {"id": "downvote-count"})
                    item_votes = (
                        upvote.text.strip() if upvote else "0",
                        downvote.text.strip() if downvote else "0",
                    )
                else:
                    debug_info["detail_pages_failed"] += 1
                    append_debug_message(
                        debug_info,
                        f"detail page {detail_response.status_code} for {item_name[:40]}",
                    )
            except Exception as e:
                debug_info["detail_pages_failed"] += 1
                append_debug_message(
                    debug_info,
                    f"detail parse failed for {item_name[:40]}: {type(e).__name__}",
                )

            items_dict[item_name] = {
                "category": item_type,
                "price": item_price,
                "image": item_image,
                "colors": [color for color in item_colors if isinstance(color, str)],
                "link": item_full_link,
                "votes": item_votes,
            }
            debug_info["items_built"] += 1
        except Exception as e:
            append_debug_message(
                debug_info, f"item build failed: {type(e).__name__}: {e}"
            )

    if not items_dict:
        append_debug_message(debug_info, "no items built for current filter")

    return items_dict, debug_info


# Function to get the number of items in the basket
def get_number_of_items() -> None:
    """
    Get the number of items stored in the local 'items.json' basket file.

    Returns
    -------
    int
        The total number of items in the JSON file.
    str
        Error message if the file is missing or contains invalid JSON.
    """

    # Get the absolute path to the JSON file
    json_file_path: str = "items.json"
    n: int = 0
    try:
        with open(json_file_path, "r") as json_file:
            data: str = json.load(json_file)
            for _ in data:
                n += 1
            return n
    except FileNotFoundError:
        return "JSON file not found"
    except json.JSONDecodeError:
        return "Invalid JSON data"


# Return a customized input component (with app desing guidlines)
def custom_input(placeholder: str | None = None, on_change=None) -> ui.input:
    """
    Create a customized NiceGUI input component following app design guidelines.

    Parameters
    ----------
    placeholder : str | None
        Placeholder text for the input field.
    on_change : callable | None
        Function to call when the input value changes.

    Returns
    -------
    ui.input
        A styled NiceGUI input component.
    """
    return (
        ui.input(None, placeholder=placeholder, on_change=on_change)
        .props("square outlined color=black")
        .classes("font-mono")
    )


# Return a customized select component (with app desing guidlines)
def custom_select(
    options: list | dict = [], *, label: Any = None, value: Any = None, on_change=None
) -> ui.select:
    """
    Create a customized NiceGUI select component following app design guidelines.

    Parameters
    ----------
    options : list | dict
        Options to display in the select component.
    label : Any
        Label for the select field.
    value : Any
        Default selected value.
    on_change : Callable | None
        Function to call when the selected value changes.

    Returns
    -------
    ui.select
        A styled NiceGUI select component.
    """
    return (
        ui.select(options=options, label=label, value=value, on_change=on_change)
        .props("square outlined color=black")
        .classes("font-mono")
    )


# Creating the Basket object and its UI
class BasketCheckout:
    def __init__(self, notifier: ui.badge, container: ui.grid) -> None:
        """
        Manages the shopping basket UI and checkout flow.

        This class is responsible for:
        - Rendering the basket recap (items, prices, total)
        - Rendering the checkout form
        - Managing basket state persistence via a JSON file
        - Updating the UI badge that displays the number of items
        - Binding checkout inputs to the automation Bot

        The basket data is stored locally in a JSON file and rendered dynamically
        using NiceGUI components.

        Args:
            notifier (ui.badge): Badge used to display the number of items in the basket.
            container (ui.grid): Parent container used to render recap and checkout columns.
        """

        # Objects properties
        self.items_number: int = get_number_of_items()
        self.notifier: ui.badge = notifier
        with container:
            self.recap_container: ui.column = ui.column(align_items="stretch").classes(
                "pr-4"
            )
            self.checkout_container: ui.column = ui.column(
                align_items="stretch"
            ).classes("pl-4")
        self.file_path: str = "items.json"
        self.checkout_already_rendered: bool = False
        self.bot: Bot = Bot(NATIONS, ZONES)

        # #region agent log
        _agent_log(
            hypothesisId="H1",
            location="main.py:BasketCheckout.__init__",
            message="BasketCheckout initialized",
            data={
                "basket_id": id(self),
                "bot_id": id(self.bot),
                "items_number": int(self.items_number)
                if isinstance(self.items_number, int)
                else str(self.items_number),
            },
        )
        # #endregion

        # Rendering the basket
        self.render()

    # Utility to check if the basket is empty
    def is_empty(self) -> bool:
        """
        Checks whether the basket is empty.

        Returns:
            bool: True if the basket file does not exist, is invalid,
            or contains no items. False otherwise.
        """
        try:
            with open(self.file_path, "r") as file:
                data: str = json.load(file)
                if not data:
                    return True  # JSON file is empty
                else:
                    return False  # JSON file is not empty
        except (FileNotFoundError, json.JSONDecodeError):
            return True  # Error occurred or file doesn't exist

    # Function to check if an item is inside the basket
    def item_in(self, item_name: str) -> None:
        """
        Checks if a specific item is present in the basket.

        Args:
            item_name (str): Name of the item to search for.

        Returns:
            bool: True if the item is in the basket, False otherwise.
        """
        try:
            # Load existing items from the JSON file if it exists
            with open(self.file_path, "r") as json_file:
                basket: list = json.load(json_file)
        except FileNotFoundError:
            # If the file doesn't exist, the item is not in the basket
            return False

        # Check if the item_name exists in any of the items
        for item in basket:
            if item.get("name") == item_name:
                return True

        # If the item_name is not found in any item, return False
        return False

    # Function to update the number of item
    def update_number_of_item(self) -> None:
        """
        Updates the internal item count and refreshes the UI badge.

        This method:
        - Recomputes the number of items in the basket
        - Updates badge text
        - Toggles badge visibility
        """

        # Updating the internal number state
        self.items_number: int = get_number_of_items()

        # Updating the badge on the icon
        n: int = get_number_of_items()
        self.notifier.set_text(str(n))
        self.notifier.set_visibility(n >= 1)
        self.notifier.update()

    # Function to render only the recap
    @ui.refreshable_method
    def render_recap(self) -> None:
        """
        Renders the basket recap section.

        Displays:
        - Item names
        - Selected color and size (if available)
        - Individual prices
        - Basket total
        """

        # Checking frist if the basket isn't empty
        if not self.is_empty():

            # Loading the basket data from the json file
            with open(self.file_path, "r") as json_file:
                data: str = json.load(json_file)

            # Using the column wrapped in the passed constructor container
            total: int = 0
            ui.label("Basket").classes("font-mono font-bold text-xl")
            for i, item in enumerate(data):
                with ui.row(align_items="stretch").classes("pb-4"):
                    with ui.column():
                        ui.label(item["name"]).classes("font-mono font-bold text-base")
                        if item["color"] != "None":
                            ui.label(item["color"]).classes("font-mono")
                        elif item.get("color_keywords"):
                            ui.label(
                                "Keywords: " + ", ".join(item["color_keywords"])
                            ).classes("font-mono")
                        if item["size"] != "None":
                            ui.label(item["size"]).classes("font-mono")
                    ui.space()
                    if item["price"] != "None":
                        total += int(float(item["price"].replace("$", "")))
                        if i == len(data) - 1:
                            with ui.column(align_items="stretch"):
                                with ui.row():
                                    ui.space()
                                    ui.label(item["price"]).classes(
                                        "font-mono font-bold text-base"
                                    )
                                ui.space()
                                ui.label(f"Total: ${total}").classes(
                                    "font-mono font-bold text-base"
                                )
                        else:
                            ui.label(item["price"]).classes(
                                "font-mono font-bold text-base"
                            )

    # Function to render only the row for zones options if possible
    @ui.refreshable_method
    def render_zone(self) -> None:
        """
        Renders country-specific address and zone inputs.

        Some countries require zone selection (e.g. Italy, Spain),
        while others use a simplified address form.
        """

        # #region agent log
        _agent_log(
            hypothesisId="H3",
            location="main.py:BasketCheckout.render_zone",
            message="render_zone called",
            data={
                "basket_id": id(self),
                "bot_id": id(self.bot),
                "country": self.bot.COUNTRY,
                "postal_len": len(self.bot.POSTAL_CODE or ""),
                "city_len": len(self.bot.CITY or ""),
                "name_on_card_len": len(self.bot.NAME_ON_CARD or ""),
            },
        )
        # #endregion

        # Checking if the selected country falls inside the country zones options
        if self.bot.COUNTRY in [
            "United States",
            "Ireland",
            "Italy",
            "Portugal",
            "Romania",
            "Spain",
        ]:
            zones: list[str] = [zone for zone in ZONES[self.bot.COUNTRY].keys()]
            with ui.grid(columns="1fr 1fr"):
                custom_input("Postal Code").bind_value_to(self.bot, "POSTAL_CODE")
                custom_select(zones, value=zones[0]).bind_value_to(self.bot, "ZONE")
            with ui.grid(columns="1fr 1fr"):
                custom_input("City").bind_value_to(self.bot, "CITY")
                custom_input("Name on Card").bind_value_to(self.bot, "NAME_ON_CARD")
        else:
            with ui.grid(columns="1fr 1fr"):
                custom_input("Postal Code").bind_value_to(self.bot, "POSTAL_CODE")
                custom_input("City").bind_value_to(self.bot, "CITY")
            custom_input("Name on Card").bind_value_to(self.bot, "NAME_ON_CARD")

    # Function to render only the checkout
    def render_checkout(self) -> None:
        """
        Renders the checkout form.

        Includes:
        - Personal details
        - Payment information
        - Address and shipping details
        - Country-dependent zone selection
        """

        # Checking frist if the basket isn't empty
        if not self.is_empty():

            # #region agent log
            _agent_log(
                hypothesisId="H2",
                location="main.py:BasketCheckout.render_checkout",
                message="render_checkout called",
                data={
                    "basket_id": id(self),
                    "bot_id": id(self.bot),
                    "checkout_already_rendered": bool(self.checkout_already_rendered),
                    "email_len": len(self.bot.EMAIL or ""),
                    "first_name_len": len(self.bot.FIRST_NAME or ""),
                    "last_name_len": len(self.bot.LAST_NAME or ""),
                    "address_len": len(self.bot.ADDRESS or ""),
                    "phone_len": len(self.bot.PHONE or ""),
                },
            )
            # #endregion

            # Setting the first rendering to true
            self.checkout_already_rendered: bool = True

            # Using the column wrapped in the passed constructor container
            with self.checkout_container:
                ui.label("Checkout").classes("font-mono font-bold text-xl")
                custom_input("Email").bind_value_to(self.bot, "EMAIL")
                nations_card_grid: ui.grid = ui.grid(columns="1fr 1fr")
                details_exp_grid: ui.grid = ui.grid(columns="1fr 1fr 1fr 1fr")
                address_cvv_grid: ui.grid = ui.grid(columns="1fr 1fr")
                zones_grid: ui.grid = ui.grid(columns="1fr 1fr")
                phone_checkout_grid: ui.grid = ui.grid(columns="2fr 1fr 1fr")
                with nations_card_grid:
                    custom_select(
                        [nation for nation in NATIONS.keys()],
                        value="United States",
                        on_change=lambda _: self.reload(),
                    ).bind_value_to(self.bot, "COUNTRY")
                    custom_input("Card Number").bind_value_to(self.bot, "CARD_NUMBER")
                with details_exp_grid:
                    custom_input("Name").bind_value_to(self.bot, "FIRST_NAME")
                    custom_input("Surname").bind_value_to(self.bot, "LAST_NAME")
                    custom_input("Exp. Year").bind_value_to(self.bot, "YEAR_EXP")
                    custom_input("Exp. Month").bind_value_to(self.bot, "MONTH_EXP")
                with address_cvv_grid:
                    custom_input("Address").bind_value_to(self.bot, "ADDRESS")
                    custom_input("CVV").bind_value_to(self.bot, "CVV")
                with zones_grid:
                    self.render_zone()
                with phone_checkout_grid:
                    custom_input("Phone").bind_value_to(self.bot, "PHONE")
                    ui.button(
                        "Dry Run", on_click=lambda _: self.bot.dry_run()
                    ).props("square outline color=black").classes("font-mono")
                    ui.button(
                        "Start Supremebot", on_click=lambda _: self.bot.start()
                    ).props(f"square fill color=red-600").classes("font-mono")

    # Util fucntion to reload the checkout based on conutry zone relationships
    def reload(self) -> None:
        """
        Reloads the zone selection UI when the country changes.
        """
        # #region agent log
        _agent_log(
            hypothesisId="H3",
            location="main.py:BasketCheckout.reload",
            message="Country changed -> render_zone.refresh",
            data={
                "basket_id": id(self),
                "bot_id": id(self.bot),
                "country": self.bot.COUNTRY,
            },
        )
        # #endregion
        self.render_zone.refresh()

    # Function to render the basket recap
    def render(self) -> None:
        """
        Renders the entire basket UI.

        This includes:
        - Basket recap
        - Checkout form
        """
        with self.recap_container:
            self.render_recap()
        self.render_checkout()


# Creating the Item UI and logic blueprint
class Item(ui.grid):
    def __init__(self, name: str, info: dict, basket: BasketCheckout) -> None:
        """
        UI component representing a single product item.

        This class is responsible for rendering a product card, handling
        customization options (color, size), and managing add/remove
        interactions with the basket.

        It extends `ui.grid` and tightly integrates with a `BasketCheckout`
        instance to keep UI state and persisted basket data in sync.

        Args:
            name (str): Product name.
            info (dict): Product metadata (image, price, category, colors, votes, link).
            basket (BasketCheckout): Shared basket controller instance.
        """

        # Initializing the basic grid
        super().__init__(columns="2fr 4fr 1fr")
        self.classes("pt-4")

        # Assigning passed parameters to self variables
        self.name: str = name
        self.info: str = info
        self.selected_color = "None"
        self.selected_color_keywords = ""
        self.selected_size = "None"
        self.basket: BasketCheckout = basket

        # Rendering the item — must be called inside `with self:` so the
        # refreshable slot is registered *inside* the grid, not in the outer context
        with self:
            self.render()

    # Renders the item UI inside the grid
    @ui.refreshable_method
    def render(self) -> None:
        """
        Render the item UI.

        This method:
        - Displays product image, name, price, and trend indicator
        - Shows either "add to basket" or "remove from basket" CTA
        - Conditionally renders customization controls (color, size)
        - Re-renders entirely on state changes
        """

        # Using the grid to place the items, in two states: "in" or "not in" basket

        # Render the item image
        with ui.element("div").style(
            "border-width: 1px; border-color: rgb(194, 194, 194);"
        ).classes("p-4 w-fit"):
            ui.image(self.info["image"]).style("width: 11.7rem;")

        # Name, price and trend (if founded)
        with ui.column():
            with ui.row(align_items="center").classes("pt-2"):
                ui.markdown("**Product**").classes("font-mono text-lg")
                ui.link(self.name, self.info["link"]).classes(
                    "font-mono font-bold text-black text-lg"
                )
                self.trend()
            with ui.row(align_items="center").classes("pt-2"):
                ui.markdown(f"**Price**").classes("font-mono text-lg")
                ui.label(self.info["price"]).classes("font-mono text-lg")

            # Render the cta (call to action) "add to basket" or "remove from basket"
            if not self.basket.item_in(self.name):
                ui.button("add to", on_click=lambda _: self.add_to_basket()).props(
                    f"square fill color=red-600 icon-right=shopping_cart"
                ).classes("font-mono mt-2")
            else:
                ui.button(
                    "remove from", on_click=lambda _: self.remove_from_basket()
                ).props(
                    f"square outline color=red-600 icon-right=shopping_cart"
                ).classes(
                    "font-mono mt-2"
                )

        # Render the customize buttons area
        with ui.column(align_items="stretch").classes("pt-2"):

            # Filtering the sizes' options
            size_options: list[str] = (
                "None"
                if self.info["category"]
                not in [
                    "t-shirts",
                    "sweatshirts",
                    "jackets",
                    "tops-sweaters",
                    "pants",
                    "shirts",
                ]
                else ["Small", "Medium", "Large", "XLarge", "XXLarge"]
            )
            if not self.basket.item_in(self.name):

                # Creating the title (if the customize options are availbale)
                if self.info["colors"] or size_options != "None" or not self.info["colors"]:
                    ui.label("Customize").classes("text-lg text-bold font-mono pt-2")

                if self.info["colors"]:
                    ui.select(
                        options=self.info["colors"],
                        label="Select a color",
                        value=self.info["colors"][0],
                    ).props("square outlined color=black").classes(
                        "font-mono pt-2"
                    ).bind_value_to(
                        self, "selected_color"
                    )
                else:
                    ui.label("Preferred color keywords").classes(
                        "font-mono pt-2 text-sm"
                    )
                    custom_input("navy, blue").classes("pt-2").bind_value_to(
                        self, "selected_color_keywords"
                    )
                    ui.label(
                        "Used only when SupremeCommunity does not list exact colorways."
                    ).classes("font-mono text-xs text-grey-7 pt-1")

                if size_options != "None":
                    ui.select(
                        options=size_options,
                        label="Select a size",
                        value=size_options[0],
                    ).props("square outlined color=black").classes(
                        "font-mono pt-2"
                    ).bind_value_to(
                        self, "selected_size"
                    )

    # Function to add the item to the basket
    def add_to_basket(self) -> None:
        """
        Add the current item to the basket.

        This method:
        - Serializes item data into `items.json`
        - Updates basket counters and UI
        - Triggers checkout rendering if necessary
        - Re-renders the item UI to reflect state change
        """

        # Creating the item dict to convert in json format
        color_keywords: list[str] = [
            keyword.strip()
            for keyword in self.selected_color_keywords.split(",")
            if keyword.strip()
        ]
        item_object: dict = {
            "name": self.name,
            "color": self.selected_color,
            "color_keywords": color_keywords,
            "size": self.selected_size,
            "price": self.info["price"],
            "category": self.info["category"],
        }

        try:
            # Load existing items from the JSON file if it exists
            with open(self.basket.file_path, "r") as json_file:
                basket: list = json.load(json_file)
        except FileNotFoundError:
            # If the file doesn't exist, start with an empty basket
            basket: list = list()

        # Append the new item to the basket
        basket.append(item_object)

        # Write the updated basket to the JSON file
        with open(self.basket.file_path, "w") as json_file:
            json.dump(basket, json_file, indent=4)

        # Updating the basket
        self.basket.update_number_of_item()
        self.basket.render_recap.refresh()
        if not self.basket.checkout_already_rendered:
            self.basket.render_checkout()
        if self.basket.is_empty():
            self.basket.checkout_container.clear()
            self.basket.checkout_already_rendered = False

        # Refreshing the item UI
        self.render.refresh()

    # Function to remove the item from the baskt
    def remove_from_basket(self) -> None:
        """
        Remove the item from the basket.

        This method:
        - Removes the item from `items.json`
        - Updates basket counters and UI
        - Clears checkout UI if basket becomes empty
        - Re-renders the item UI
        """
        try:
            # Load existing items from the JSON file if it exists
            with open(self.basket.file_path, "r") as json_file:
                basket: list = json.load(json_file)
        except FileNotFoundError:
            # If the file doesn't exist, there are no items to delete
            return False

        # Create a flag to check if the item was found and deleted
        item_deleted: bool = False

        # Create a copy of the basket to avoid modifying it during iteration
        basket_copy: list = basket.copy()

        # Iterate through items in the basket
        for item in basket_copy:
            if item.get("name") == self.name:
                basket.remove(item)  # Remove the item from the basket
                item_deleted: bool = True
                break

        if item_deleted:
            # Write the updated basket to the JSON file
            with open(self.basket.file_path, "w") as json_file:
                json.dump(basket, json_file, indent=4)

        # Updating the basket
        self.basket.update_number_of_item()
        self.basket.render_recap.refresh()
        if not self.basket.checkout_already_rendered:
            self.basket.render_checkout()
        if self.basket.is_empty():
            self.basket.checkout_container.clear()
            self.basket.checkout_already_rendered = False

        # Refreshing the item UI
        self.render.refresh()

    # Function to generate the trend UI for the item
    def trend(self) -> None:
        """
        Render the trending indicator for the item.

        Uses a likes/dislikes ratio to determine if the item
        is trending. Displays:
        - 🔥 icon if trending
        - ℹ️ icon if vote data is unavailable
        """

        # Calculate the ratio, ensure 'dislikes' is non-zero by adding 1
        try:
            ratio: float = int(self.info["votes"][0]) / (
                int(self.info["votes"][1]) + 1
            )  # Prevents division by zero

            # Display trending status based on the ratio
            if ratio >= 3:
                with ui.icon("local_fire_department").classes("text-2xl text-red-600"):
                    ui.tooltip("Trending").classes("bg-red-600 font-mono").props(
                        "delay=700"
                    )
        except:
            with ui.icon("info").classes("text-2xl text-grey"):
                ui.tooltip("No info yet").classes("bg-grey font-mono").props(
                    "delay=700"
                )


# Creating the Items List UI and logic blueprint
class ItemsList:
    def __init__(self, basket: BasketCheckout, container: ui.column) -> None:
        """
        Controller class responsible for rendering a list of product items.

        This class fetches product data based on a selected drop date
        and category, then instantiates and renders `Item` components
        inside a provided UI container.

        It acts as a bridge between data retrieval and UI composition,
        while sharing a common `BasketCheckout` instance across items.

        Args:
            basket (BasketCheckout): Shared basket controller instance.
            container (ui.column): UI column used to render item components.
        """

        # Creating a date and category parameter to use to show items
        self.drop_dates: list[str] = get_drop_dates()
        self.date: str = (
            self.drop_dates[0]
            if self.drop_dates
            else convert_date(datetime.date.today().isoformat())
        )
        self.category: str = "T-Shirts"
        self.basket: BasketCheckout = basket
        self.container: ui.column = container

    def refresh_drop_dates(self) -> list[str]:
        """
        Refresh available drop dates from Supreme Community.

        Returns
        -------
        list[str]
            Refreshed list of drop dates, newest first.
        """
        previous_date: str = self.date
        self.drop_dates = get_drop_dates()
        if self.drop_dates and previous_date not in self.drop_dates:
            self.date = self.drop_dates[0]
        return self.drop_dates

    def set_date(self, drop_date: str) -> None:
        """
        Update the selected drop date and rerender the list.
        """
        self.date = drop_date
        self.render()

    def set_category(self, category: str) -> None:
        """
        Update the selected category and rerender the list.
        """
        self.category = category
        self.render()

    # Render all the Items object inside the column, with the specified date and category
    def render(self) -> None:
        """
        Render all items for the selected date and category.

        This method:
        - Fetches items using the current date and category
        - Clears the container before rendering
        - Instantiates an `Item` UI component for each product
        """

        self.container.clear()
        try:
            items, _ = fetch_items(self.date, self.category)
        except Exception as e:
            with self.container:
                ui.label(
                    f"Error loading items for {self.category} on {self.date}."
                ).classes("font-mono text-base text-red-700 pt-4")
            return

        if not items:
            with self.container:
                ui.label(f"No items found for {self.category} on {self.date}.").classes(
                    "font-mono text-base text-grey-7 pt-4"
                )
            return

        for item_name, item_info in items.items():
            with self.container:
                Item(item_name, item_info, self.basket)


# Main app logic
with ui.element("div").classes("w-full p-8"):

    # Creating the main heading
    header: ui.row = ui.row(align_items="center")
    with header:
        with ui.element("div").classes("w-fit bg-red-600"):
            ui.label("Supremebot").classes(
                "text-white text-4xl text-bold italic font-mono"
            )

    # Creating the grid for the date and category selectors
    selectors_container: ui.grid = ui.grid(columns="1fr 5fr").classes("py-8")

    # The container for the items list
    list_container: ui.column = ui.column(align_items="stretch")

    # The container for the basket recap UI
    with ui.link_target("basket"):
        footer_container: ui.grid = ui.grid(columns="1.5fr 2fr").classes("pt-10 w-full")

    # Creating the basket with its notifier
    with header:
        ui.space()
        with ui.link(target="https://www.buymeacoffee.com/saccofrancesco"):
            ui.image(
                "https://img.buymeacoffee.com/button-api/?text=Buy me a coffee&emoji=☕&slug=saccofrancesco&button_colour=FFDD00&font_colour=000000&font_family=Cookie&outline_colour=000000&coffee_colour=ffffff"
            ).classes("w-[200px]")
        items_number: int = get_number_of_items()
        basket_link: ui.link = ui.link(target="#basket").classes("text-black")
        with basket_link:
            basket_icon: ui.icon = ui.icon("shopping_cart", size="2.5rem")
        with basket_icon:
            basket_notifier: ui.badge = (
                ui.badge(items_number, color="red-600")
                .props("floating")
                .classes("font-mono")
            )
        basket_notifier.set_visibility(items_number >= 1)
        basket_notifier.update()

    # Creating the basket object to store basket state
    basket: BasketCheckout = BasketCheckout(basket_notifier, footer_container)

    # Creating the items list section
    items_list: ItemsList = ItemsList(basket, list_container)

    def refresh_drop_dates(_: Any = None) -> None:
        """
        Refresh the drop-date selector and rerender items.
        """
        date.options = items_list.refresh_drop_dates()
        date.value = items_list.date
        date.update()
        items_list.render()

    # Creating the select and tabs widgets
    with selectors_container:
        with ui.row(align_items="center").classes("w-full gap-2 no-wrap"):
            date: ui.select = (
                ui.select(
                    options=items_list.drop_dates,
                    label="Select a drop date",
                    value=items_list.date,
                    on_change=lambda e: items_list.set_date(e.value),
                )
                .props("square outlined color=black")
                .classes("font-mono flex-1")
            )
            ui.button(icon="refresh", on_click=refresh_drop_dates).props(
                "square outline color=black"
            ).classes("font-mono")
        with ui.tabs(
            value="T-Shirts",
            on_change=lambda e: items_list.set_category(e.value),
        ).props(
            "indicator-color=red-600 align=justify"
        ).classes("font-mono") as tabs:
            ui.tab("T-Shirts")
            ui.tab("Accessories")
            ui.tab("Sweatshirts")
            ui.tab("Hats")
            ui.tab("Jackets")
            ui.tab("Tops")
            ui.tab("Pants")
            ui.tab("Skate")
            ui.tab("Bags")
            ui.tab("Shirts")

    # Rendering the list (after NiceGUI event loop starts)
    ui.timer(
        0.0,
        items_list.render,
        once=True,
    )

# #region agent log
def _log_connect_event(event: str) -> None:
    try:
        client = ui.context.client
        _agent_log(
            hypothesisId="H1",
            location="main.py:_log_connect_event",
            message=event,
            data={
                "client_id": getattr(client, "id", None),
                "has_client": client is not None,
            },
        )
    except Exception:
        _agent_log(
            hypothesisId="H1",
            location="main.py:_log_connect_event",
            message=event,
            data={"client_id": None, "has_client": False},
        )


try:
    # NiceGUI exposes connect hooks on some versions via `app`, not `ui`
    from nicegui import app  # type: ignore

    if hasattr(app, "on_connect"):
        app.on_connect(lambda: _log_connect_event("client_connect"))  # type: ignore
    if hasattr(app, "on_disconnect"):
        app.on_disconnect(lambda: _log_connect_event("client_disconnect"))  # type: ignore
    _agent_log(
        hypothesisId="H1",
        location="main.py:connect_hooks",
        message="connect hooks registered",
        data={
            "has_app_on_connect": bool(hasattr(app, "on_connect")),
            "has_app_on_disconnect": bool(hasattr(app, "on_disconnect")),
        },
    )
except Exception as e:
    _agent_log(
        hypothesisId="H1",
        location="main.py:connect_hooks",
        message="connect hooks registration failed",
        data={"error": type(e).__name__},
    )
# #endregion

# Running the app
ui.run(title="Supremebot", favicon="img/icon.png")
