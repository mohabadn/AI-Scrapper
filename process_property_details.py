import asyncio
import json
from typing import List, Set, Tuple

from crawl4ai import (
    AsyncWebCrawler,
    BrowserConfig,
    CacheMode,
    CrawlerRunConfig,
    LLMExtractionStrategy,
)

from config import BASE_URL, CSS_SELECTOR, REQUIRED_KEYS
from data_utils import (
    is_complete_prop,
    is_duplicate_prop,
    save_prop_to_csv,
)
from scraper_utils import (
    check_no_results,
    get_browser_config,
    get_llm_strategy,
)
from dotenv import load_dotenv
load_dotenv()

async def process_property_details(
    crawler: AsyncWebCrawler,
    url: str,
    content_selector: str,
    llm_strategy: LLMExtractionStrategy,
    session_id: str,
    required_keys: List[str],
    seen_names: Set[str]
) -> dict:
    """
    Extracts property information using LLM strategy instead of direct HTML parsing.
    """
    try:
        # Fetch page with LLM extraction strategy
        details_result = await crawler.arun(
            url=url,
            config=CrawlerRunConfig(
                cache_mode=CacheMode.BYPASS,
                extraction_strategy=llm_strategy,  # Use the LLM strategy
                css_selector="div.col-lg-8.mx-auto.py-4.px-4",
                session_id=session_id,
            )
        )
        
        if not (details_result.success and details_result.extracted_content):
            print(f"Failed to fetch property details from {url}")
            return None
            
        print("\nProcessing URL:", url)
        
        # Parse the LLM-extracted content
        try:
            extracted_data = json.loads(details_result.extracted_content)
            if isinstance(extracted_data, list):
                # If LLM returns a list, take the first item
                property_data = extracted_data[0] if extracted_data else {}
            else:
                # If LLM returns a single object
                property_data = extracted_data
                
            # Debug: Print raw extracted data
            print("Raw extracted data:", property_data)
            
            # Ensure we only keep the required fields
            cleaned_data = {
                "location": property_data.get("location", ""),
                "area": property_data.get("area", ""),
                "description": property_data.get("description", "")
            }
            
            # Debug output for missing fields
            missing_fields = [key for key in required_keys if not cleaned_data.get(key)]
            if missing_fields:
                print(f"Missing required fields: {missing_fields}")
            
            # Verify all required fields are present and not empty
            if all(cleaned_data.get(key) for key in required_keys):
                print(f"Successfully extracted complete property data!")
                return cleaned_data
            else:
                print("Property data is incomplete")
                return None
                
        except json.JSONDecodeError as e:
            print(f"Error parsing LLM output: {e}")
            print("Raw LLM output:", details_result.extracted_content)
            return None
        
    except Exception as e:
        print(f"Error processing property details: {e}")
        import traceback
        print(traceback.format_exc())
        return None
    
async def process_page_properties(
    crawler: AsyncWebCrawler,
    page_url: str,
    content_selector: str,
    llm_strategy: LLMExtractionStrategy,
    session_id: str,
    required_keys: List[str],
    seen_names: Set[str]
) -> List[dict]:
    """
    Processes all properties on a single page.
    """
    # Load the page to get the list of properties
    list_result = await crawler.arun(
        url=page_url,
        config=CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            session_id=session_id,
            css_selector="[class^='view btn btn-pro d-block mx-auto']",  # Select all Details buttons
        )
    )
    
    if not list_result.success:
        print(f"Failed to load page: {list_result.error_message}")
        return []
    
    # Extract the URLs from Details buttons
    details_urls = []
    if list_result.cleaned_html:
        # Look for links containing "Details" text or href attributes
        for line in list_result.cleaned_html.split('\n'):
            if 'Details' in line and 'href' in line:
                # Extract the URL - you might need to adjust this based on the actual HTML structure
                url_start = line.find('href="') + 6
                url_end = line.find('"', url_start)
                if url_start > 5 and url_end > url_start:
                    url = line[url_start:url_end]
                    if not url.startswith('http'):
                        url = f"https://palestine.io{url}"
                    details_urls.append(url)
    
    if not details_urls:
        print("No property listings found on this page")
        return []
    
    print(f"Found {len(details_urls)} properties on this page")
    
    properties = []
    for url in details_urls:
        # Process each property
        property_data = await process_property_details(
            crawler,
            url,
            content_selector,
            llm_strategy,
            session_id,
            required_keys,
            seen_names
        )
        
        if property_data:
            properties.append(property_data)
        
        await asyncio.sleep(1)  # Small delay between properties
    
    return properties

async def crawl_properties():
    """
    Main function to crawl property data from all pages.
    """
    browser_config = get_browser_config()
    llm_strategy = get_llm_strategy()
    session_id = "property_crawl_session"
    
    # Initialize state
    all_properties = []
    seen_names = set()
    page_number = 1
    
    # CSS selector for property content
    content_selector = "[class^='row align-items-start pt-3 rounded-left  mt-4 ']"
    
    async with AsyncWebCrawler(config=browser_config) as crawler:
        while True:
            page_url = f"{BASE_URL}&page={page_number}"
            print(f"\nProcessing page {page_number}...")
            
            # Check for "No Results Found"
            no_results = await check_no_results(crawler, page_url, session_id)
            if no_results:
                print("No more pages to process")
                break
            
            # Process all properties on the current page
            page_properties = await process_page_properties(
                crawler,
                page_url,
                content_selector,
                llm_strategy,
                session_id,
                REQUIRED_KEYS,
                seen_names
            )
            
            if not page_properties:
                print(f"No properties found on page {page_number}")
                break
            
            all_properties.extend(page_properties)
            print(f"Total properties collected so far: {len(all_properties)}")
            page_number += 1
            await asyncio.sleep(2)  # Delay between pages
    
    # Save results
    if all_properties:
        save_prop_to_csv(all_properties, "complete_properties.csv")
        print(f"Saved {len(all_properties)} properties to 'complete_properties.csv'")
    else:
        print("No properties were found during the crawl")
    
    llm_strategy.show_usage()

async def main():
    """
    Entry point of the script.
    """
    await crawl_properties()

if __name__ == "__main__":
    asyncio.run(main())