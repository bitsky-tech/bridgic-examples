# Translate the following task into Python code.

## Task Objective
Retrieve posts from the past few days on Andrej Karpathy’s X profile and save them to files.

## Task Steps
1. Open "https://x.com?lang=en".
2. Check whether the user is currently logged out. If the page remains on the login screen, prompt the user to log in and slowly poll to see whether login has succeeded. Once login success is detected, automatically proceed to the next step.
3. Ensure that you are currently on the home page (i.e., x.com/home). Otherwise, go back to Step 1.
4. Only after visiting the home page should you open "https://x.com/karpathy".
5. Retrieve each post in reverse chronological order from the "Posts" section lower on the page until the posts exceed the specified time range. Continuously scroll down the page to load older posts.
Important notes during retrieval: skip posts marked as "Pinned"; skip ads; correctly distinguish between posts by Andrej Karpathy and reposts. For reposts, be sure to record the original author and do not mistakenly treat them as posted by Andrej Karpathy.
6. Save all retrieved posts to the file `../tracking_results/x_posts.json` in JSON format.

## Other Requirements
 - The time range to check should be an optional parameter of the generated runnable program.
 - Whether to use browser in headed mode should also be an optional parameter of the generated runnable program.
 - Output a README file explaining how to use the generated program.
 