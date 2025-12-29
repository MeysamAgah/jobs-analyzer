from selenium import webdriver
from selenium.webdriver.common.by import By
import time
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from tqdm import tqdm

def web_driver(user_agent_string=None):
    options = Options()
    options.add_argument("--headless")  # optional
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1200")
    options.add_argument("--disable-dev-shm-usage")
    if user_agent_string:
        options.add_argument(f"user-agent={user_agent_string}")

    # Automatically download and use ChromeDriver
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )
    return driver

def make_url(
        countries: list,
        tags: list,
        posted_since: int
):
    """
    Construct a WorkingNomads job search URL based on selected countries, tags, and posting date.

    Parameters
    ----------
    countries : list of str
        List of country names or regions to filter the job search.
    tags : list of str
        List of tags or keywords to filter the job search (e.g., ['python', 'data-science']).
    posted_since : int
        Number of days since the job was posted. Used as the `postedDate` parameter in the URL.

    Returns
    -------
    str
        A formatted URL string for searching jobs on WorkingNomads with the specified filters.
    """

    countries_str = ','.join(countries)
    tags_str = ','.join(tags)
    url = f"https://www.workingnomads.com/jobs?tag={tags_str}&location={countries_str}&postedDate={posted_since}"
    return url

def load_elements(
        driver,
        url: str,
        full_load: bool = True,
        clicks: int = 1,
        sleep_time: float = 4):
    """
    Load elements on a page by clicking the "Show More" button and return all loaded job elements.

    This function navigates to the specified URL, optionally clicks the "Show More" button
    either until no more buttons are present (`full_load=True`) or for a specified number of clicks
    (`full_load=False, clicks=N`), waits between clicks, and finally collects all elements
    matching the job card XPath.

    Parameters
    ----------
    driver : selenium.webdriver.Chrome
        The Selenium WebDriver instance.
    url : str
        The URL of the page to load.
    full_load : bool, default True
        If True, clicks "Show More" repeatedly until no more buttons are found.
    clicks : int, default 1
        Number of times to click "Show More" if `full_load` is False.
    sleep_time : float, default 4
        Number of seconds to wait after each click to allow new elements to load. Can be a
        float for fractional seconds or a random value.

    Returns
    -------
    list of selenium.webdriver.remote.webelement.WebElement
        A list of all loaded job elements matching the XPath `//a[contains(@class,'job-desktop')]`.
        Each element can be further processed to extract text, links, or other attributes.

    Notes
    -----
    - The function assumes the "Show More" button has a class of `show-more`.
    - Use caution if the page loads elements dynamically with infinite scrolling, as
      `full_load=True` may result in a long-running loop.
    """    
    driver.get(url)
    
    if full_load:
        while True:
            try:
                show_more = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.CLASS_NAME, "show-more"))
                )
                show_more.click()
                print("Clicked 'Show More'")
                time.sleep(sleep_time)
            except:
                print("No more 'Show More' button found")
                break
    else:
        for i in range(clicks):
            try:
                show_more = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.CLASS_NAME, "show-more"))
                )
                show_more.click()
                print(f"Clicked 'Show More' ({i+1}/{clicks})")
                time.sleep(sleep_time)
            except:
                print("No more 'Show More' button found before reaching the target clicks")
                break

    elements = driver.find_elements(By.XPATH, "//a[contains(@class,'job-desktop')]")
    return elements

def get_search_jobs(elements):
    """
        Extract job information from a list of Selenium WebElements.

        This function iterates through a list of job card elements (e.g., returned by
        `load_elements`) and extracts relevant metadata such as title, category, location,
        position type, salary, company, date, and the job URL.

        Parameters
        ----------
        driver : selenium.webdriver.Chrome
            The Selenium WebDriver instance. Used to access element attributes like `href`.
        elements : list of selenium.webdriver.remote.webelement.WebElement
            A list of job card elements, typically retrieved with an XPath like
            "//a[contains(@class,'job-desktop')]".

        Returns
        -------
        list of dict
            A list of dictionaries, each containing the following keys:
            - 'title' : str
            - 'category' : str
            - 'location' : str
            - 'position_type' : str
            - 'salary' : str (defaults to "Unknown" if missing)
            - 'company' : str
            - 'date' : str
            - 'url' : str (href of the job element)
    """
    all_outputs = []

    for item in tqdm(elements):
        item_metadata = item.text.split('\n')
        num_fields = len(item_metadata)

        # Skip items with insufficient data
        if num_fields < 6:
            continue

        # Assign values with default for missing salary
        title = item_metadata[0]
        category = item_metadata[1]
        location = item_metadata[2]
        position_type = item_metadata[3]
        salary = item_metadata[4] if num_fields == 7 else "Unknown"
        company = item_metadata[5] if num_fields == 7 else item_metadata[4]
        date = item_metadata[6] if num_fields == 7 else item_metadata[5]
        url_link = item.get_attribute("href")

        output = {
            'title': title,
            'category': category,
            'location': location,
            'position_type': position_type,
            'salary': salary,
            'company': company,
            'date': date,
            'url': url_link
        }

        all_outputs.append(output)

    return all_outputs

def get_job_data(driver, url):
    """
    Extract detailed information from a job posting page on WorkingNomads.

    Parameters
    ----------
    driver : selenium.webdriver.Chrome
        The Selenium WebDriver instance used to navigate and scrape the page.
    url : str
        The URL of the job posting page to extract data from.

    Returns
    -------
    dict
        A dictionary containing:
        - 'url' : str
            The URL of the job posting.
        - 'description' : str
            The full text of the job description, extracted from the element with class 'job-detail'.
        - 'keywords' : list of str
            A list of keywords/tags associated with the job, extracted from elements with class 'tag'.

    """
    driver.get(url)
    
    job_description = driver.find_element(By.CLASS_NAME, 'job-detail').text
    job_keywords = [
        e.text for e in driver.find_elements(By.CLASS_NAME, 'tag') if e.text.strip() != ''
    ]
    
    job_data = {
        'url': url,
        'description': job_description,
        'keywords': job_keywords
    }
    return job_data