# Browser Automation Task

## Task Description
Check which articles have been recently published on zhangtielei's blog website, and produce a brief summary of the new articles.
1. Visit https://zhangtielei.com .
2. Click through each blog article newly published within the past specified number of days to view its full content. Note: if there are many new articles, pagination may be required.
3. Finally, generate a `summary.md` that summarizes the general content of these new articles.

## Expected Output
A `summary.md` file summarizing the main content of the newly published articles on zhangtielei's blog within the specified time period.

## Notes
- The time period to check should be an optional parameter of the generated runnable program.
- The final summaries of the articles should be produced using a large language model.
