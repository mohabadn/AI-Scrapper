import json
import os
from typing import List, Set, Tuple

from crawl4ai import (
    AsyncWebCrawler,
    BrowserConfig,
    CacheMode,
    CrawlerRunConfig,
    LLMExtractionStrategy,
)

from properties import prop
from data_utils import is_complete_prop, is_duplicate_prop
from dotenv import load_dotenv
load_dotenv()

def get_browser_config() -> BrowserConfig:
    return BrowserConfig(
        browser_type="chromium",
        headless=False,
        verbose=True,
    )

def get_llm_strategy() -> LLMExtractionStrategy:
    return LLMExtractionStrategy(
        provider="gemini/gemini-pro",
        api_token=os.getenv("GEMINI_API_KEY"),
        schema=prop.model_json_schema(),
        extraction_type="schema",
        instruction=(
            "Extract property listings with 'location', 'area', and a 'description' "
            "from the HTML content. For location, extract the exact location value. "
            "For area, include the full area with units. For description, extract "
            "the complete property description, removing any translation notices. "
            "Ensure all fields are present and correctly mapped."
        ),
        input_format="markdown",
        verbose=True,
    )

async def check_no_results(
    crawler: AsyncWebCrawler,
    url: str,
    session_id: str,
) -> bool:
    result = await crawler.arun(
        url=url,
        config=CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            session_id=session_id,
        ),
    )

    if result.success:
        if "No Results Found" in result.cleaned_html:
            return True
    else:
        print(
            f"Error fetching page for 'No Results Found' check: {result.error_message}"
        )

    return False

async def fetch_and_process_page(
    crawler: AsyncWebCrawler,
    page_number: int,
    base_url: str,
    css_selector: str,
    llm_strategy: LLMExtractionStrategy,
    session_id: str,
    required_keys: List[str],
    seen_names: Set[str],
) -> Tuple[List[dict], bool]:
    url = f"{base_url}&page={page_number}"
    print(f"Loading page {page_number}...")

    no_results = await check_no_results(crawler, url, session_id)
    if no_results:
        return [], True

    result = await crawler.arun(
        url=url,
        config=CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            extraction_strategy=llm_strategy,
            css_selector=css_selector,
            session_id=session_id,
        ),
    )

    if not (result.success and result.extracted_content):
        print(f"Error fetching page {page_number}: {result.error_message}")
        return [], False

    extracted_data = json.loads(result.extracted_content)
    if not extracted_data:
        print(f"No properties found on page {page_number}.")
        return [], False

    print("Extracted data:", extracted_data)

    complete_properties = []
    for property in extracted_data:
        print("Processing property:", property)

        if property.get("error") is False:
            property.pop("error", None)

        if not is_complete_prop(property, required_keys):
            continue

        if is_duplicate_prop(property["name"], seen_names):
            print(f"Duplicate property '{property['name']}' found. Skipping.")
            continue

        seen_names.add(property["name"])
        complete_properties.append(property)

    if not complete_properties:
        print(f"No complete properties found on page {page_number}.")
        return [], False

    print(f"Extracted {len(complete_properties)} properties from page {page_number}.")
    return complete_properties, False
