# Browser Automation Task

## Task Description
Retrieve posts from the past few days on Andrej Karpathy's X profile and save them to a file.

1. Open "https://x.com?lang=en".
2. Check whether the current page is the login page. If it is, human interaction is required to complete the login.
3. Enter `/home`, then open "https://x.com/karpathy".
   Note: do not visit "https://x.com/karpathy" while logged out, because the latest posts will not be available.
4. Retrieve each post in reverse chronological order from the "Posts" section lower on the page, until the posts exceed the specified time range. Keep scrolling down to load older posts.
   Note: skip posts marked as "Pinned"; skip ads; correctly distinguish between posts by Andrej Karpathy and reposts. For reposts, be sure to record the original author and do not mistakenly treat them as posted by Andrej Karpathy.
5. Save all retrieved posts to the file `x_posts.md` in Markdown format.

## Expected Output
`x_posts.md`: posts by Andrej Karpathy within the specified time range, in reverse chronological order and Markdown format; Pinned posts and ads are skipped, and reposts correctly record the original author.

## Notes (optional)
- Parameters:
  - The time range (in days) should be a parameter of the generated program, with a default of 7 days.
  - Whether to use a headed browser should also be a parameter of the generated program.
- Output a README file explaining how to use the generated program.
- If the user is not logged in, human intervention is required to complete the login; the program should poll login status at a slow frequency.
