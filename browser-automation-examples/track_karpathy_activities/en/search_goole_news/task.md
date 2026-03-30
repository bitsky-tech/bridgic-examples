# Translate the following task into Python code.

## Task Objective
Search Google for news about Andrej Karpathy, browse the first few pages, and save the search results to a file.

## Task Steps
1. Open "https://www.google.com/search?q=Andrej+Karpathy".
2. Click the "News" tab below the search box.
3. Read every search result on the page, including the title, original link, snippet, and time (e.g., xx days/weeks ago). Note: you do not need to click the search results.
4. Click "Next" at the bottom of the page and repeat Step 3 until you have browsed all results for the specified number of pages.
5. Save all search results to the file `../tracking_results/google_search_results.json` in JSON format.

## Other Requirements
 - The number of pages to browse should be an optional parameter of the generated runnable program.
 - Whether to use browser in headed mode should also be an optional parameter of the generated runnable program.
 - Output a README file explaining how to use the generated program.