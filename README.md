# AI Property Scraper

A sophisticated web scraper that uses AI (Gemini Pro) to extract property listings data with high accuracy.

## Features

- AI-powered content extraction using Google's Gemini Pro
- Asynchronous web crawling
- Automatic data cleaning and validation
- CSV export functionality
- Duplicate detection
- Rate limiting and polite crawling

## Prerequisites

- Python 3.9+
- Google API Key for Gemini Pro

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/AI-Scrapper.git
cd AI-Scrapper
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
Create a `.env` file in the project root and add:
```
GEMINI_API_KEY=your_api_key_here
```

## Usage

Run the scraper:
```bash
python process_property_details.py
```

The script will:
1. Crawl property listings pages
2. Extract property details using AI
3. Save results to `complete_properties.csv`

## Data Structure

Each property record contains:
- Location
- Area
- Description

## Configuration

Adjust settings in `config.py`:
- `BASE_URL`: Target website URL
- `CSS_SELECTOR`: HTML selectors for content
- `REQUIRED_KEYS`: Required fields for validation

## License

MIT License

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request
