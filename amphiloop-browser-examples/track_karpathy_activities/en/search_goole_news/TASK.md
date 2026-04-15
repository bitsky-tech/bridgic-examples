# Browser Automation Task

## Task Description
Search Google News for news about Andrej Karpathy, browse the first few pages, and save the search results to a file.

1. Open "https://www.google.com/search?q=Andrej+Karpathy".
2. Click the "News" tab below the search box.
3. Read every search result on the page, including the title, original link, snippet, and time (e.g., xx days/weeks ago).
   Note: there is no need to click into the search results.
4. Click "Next" at the bottom of the page and repeat step 3 until the specified number of pages have been browsed.
5. Save all search results to the file `google_search_results.json` in JSON format.

## Expected Output
`google_search_results.json`: all Google News search results across the specified number of pages, each entry containing title, original link, snippet, and time, saved in JSON format.

## Notes
- Parameters:
  - The number of pages to browse should be a parameter of the generated program.
  - Whether to use a headed browser should also be a parameter of the generated program.
- Output a README file explaining how to use the generated program.
