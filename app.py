import os
import time

from playwright.sync_api import sync_playwright

# Make sure to have /quotes at the end.
TWEET_URL = "https://x.com/realDonaldTrump/status/1694886846050771321/quotes"

# DO NOT use your own account.
# Make sure you don't have 2fa or etc. For now only basic username, password is supported.
USER_NAME = ""
USER_PASSWORD = ""

# Based on your network speed, you may change these.
QUIT_AFTER = 5  # How many tries to fetch new usernames after there aren't any.
WAIT_TO_LOAD_SECONDS = 2  # How many seconds to wait between two jobs.

PROXY = None
# If you have proxy uncomment and fill necessary fields. If proxy
# PROXY = {
#     "server": ...,
#     "username": ...,
#     "password": ...,
# }

# Do not mess with these settings is you don't know what you are doing.
PROFILE_LINKS_XPATH = "(//*[@data-testid='User-Name']//a[@role='link' and @tabindex='-1'])[position() > {skip}]"
PROFILE_REP_XPATH = "(//*[@data-testid='UserCell']//a[@role='link' and @tabindex='-1'])[position() > {skip}]"
LOGIN_PAGE_URL = "https://x.com/i/flow/login"

# If use change this, make sure to add it to gitignore
CONTEXT_FILE_NAME = "state.json"


# Using set to avoid likely common usernames.
users_who_quoted = set()
users_who_replied = set()


def scroll_to_top(page, wait_time=1):
    page.evaluate("window.scrollTo(0, 0)")
    time.sleep(wait_time)


def scroll_to_end(page, back_scroll_amount=200, wait_time=1):
    page.evaluate(f"window.scrollTo(0, -{back_scroll_amount})")
    time.sleep(wait_time)
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    time.sleep(wait_time)


def get_links(page, xpath, wait_time=1, skip=0):
    time.sleep(wait_time)
    return page.locator(xpath.format(skip=skip)).all()


with sync_playwright() as pr:
    iphone_13 = pr.devices["iPhone 13"]

    browser = pr.chromium.launch(
        headless=True, proxy=PROXY
    )

    # Using context to avoid re-login each time.
    context = None
    if os.path.exists(CONTEXT_FILE_NAME):
        context = browser.new_context(storage_state=CONTEXT_FILE_NAME, **iphone_13)
    else:
        context = browser.new_context(**iphone_13)

        page = context.new_page()
        page.goto(LOGIN_PAGE_URL)

        user_name_input = page.locator(
            '//input[@autocapitalize="sentences"][@autocomplete="username"][@autocorrect="on"][@name="text"]'
        )
        user_name_input.highlight()
        user_name_input.fill(USER_NAME)

        next_button = page.get_by_text("Next")
        next_button.click()

        password_input = page.locator(
            '//input[@autocapitalize="sentences"][@autocomplete="current-password"][@autocorrect="on"][@name="password"]'
        )
        password_input.fill(USER_PASSWORD)

        login_button = page.get_by_text("Log in")
        login_button.click()

        storage = context.storage_state(path=CONTEXT_FILE_NAME)

    page = context.new_page()

    print(f"Visiting {TWEET_URL}...")
    page.goto(TWEET_URL)

    print(f"Waiting {WAIT_TO_LOAD_SECONDS} for content to load...")
    time.sleep(WAIT_TO_LOAD_SECONDS)

    cook = page.get_by_text("Accept all cookies")
    cook.click()

    quit_signal = 0
    last_item = None
    while scroll_to_end(page) or True:
        links = get_links(page, PROFILE_LINKS_XPATH)

        if quit_signal == QUIT_AFTER:
            print("No more accounts. Exiting...")
            break

        for i, l in enumerate(links):
            username = l.get_attribute("href")
            username = username[1:]
            users_who_quoted.add(username)

        if last_item == username:
            quit_signal += 1
        else:
            quit_signal = 0

        last_item = username

    print("-" * 100)

    scroll_to_top(page)

    replies_button = page.get_by_text("Reposts")
    replies_button.click()

    quit_signal = 0
    last_item = None
    while scroll_to_end(page) or True:
        links = get_links(page, PROFILE_REP_XPATH)

        if quit_signal == QUIT_AFTER:
            print("No more accounts. Exiting...")
            break

        for i, l in enumerate(links):
            username = l.get_attribute("href")
            username = username[1:]
            users_who_replied.add(username)


        if last_item == username:
            quit_signal += 1
        else:
            quit_signal = 0

        last_item = username


    print("-" * 100)
    print("Done...")
    print()
    print("User who quoted:")
    for u in users_who_quoted:
        print(f'\t{u}')
    print()
    print("User who replied:")
    for u in users_who_replied:
        print(f'\t{u}')

    # account_menu_button = page.locator("//button[@aria-label='Account menu']")
    # account_menu_button.highlight()
    # account_menu_button.click()
    # logout_button = page.get_by_text("Log out", exact=False)
    # logout_button.highlight()
    # logout_button.click()
