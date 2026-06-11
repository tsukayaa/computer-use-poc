import argparse
import csv
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / "computer-use-preview" / ".env")

os.environ["PLAYWRIGHT_HEADLESS"] = "false"

sys.path.insert(0, str(Path(__file__).parent.parent / "computer-use-preview"))

from agent import BrowserAgent
from computers import PlaywrightComputer

SCREEN_SIZE = (1440, 900)
MODEL = "gemini-2.5-computer-use-preview-10-2025"
TARGET_URL = "https://www.saucedemo.com"


def build_task(user: dict) -> str:
    return f"""Complete a full purchase on saucedemo.com using the credentials and checkout details below.

Credentials:
  Username : {user['username']}
  Password : {user['password']}

Checkout details:
  First Name : {user['first_name']}
  Last Name  : {user['last_name']}
  Zip Code   : {user['zipcode']}

Steps:
1. Navigate to https://www.saucedemo.com
2. Log in with the username and password above
3. On the product listing page, scroll down to find 'Test.allTheThings() T-Shirt (Red)' and add it to the cart
4. Click the cart icon (top right) to open the cart
5. Click 'Checkout'
6. Fill in the checkout form:
   - First Name: {user['first_name']}
   - Last Name: {user['last_name']}
   - Zip/Postal Code: {user['zipcode']}
7. Click 'Continue'
8. Review the order summary, then click 'Finish'
9. Confirm the 'Thank you for your order!' message appears
10. Report success"""


def run_user(user: dict, index: int):
    task = build_task(user)

    print(f"\n{'='*60}")
    print(f"  User {index + 1}: {user['first_name']} {user['last_name']}")
    print(f"  Login: {user['username']}")
    print(f"{'='*60}")
    print(f"\n[QUERY]\n{task}\n")

    computer = PlaywrightComputer(
        screen_size=SCREEN_SIZE,
        initial_url=TARGET_URL,
    )

    with computer as browser:
        agent = BrowserAgent(
            browser_computer=browser,
            query=task,
            model_name=MODEL,
        )
        agent.agent_loop()

    result = getattr(agent, "final_reasoning", "No final message")
    print(f"\n[RESULT] {result}\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--user", type=int, default=None,
                        help="Run only this user (1-indexed). Omit to run all.")
    args = parser.parse_args()

    csv_path = Path(__file__).parent / "users.csv"
    with open(csv_path, newline="", encoding="utf-8") as f:
        users = list(csv.DictReader(f))

    if args.user is not None:
        idx = args.user - 1
        if idx < 0 or idx >= len(users):
            print(f"Invalid --user {args.user}. Valid range: 1-{len(users)}.")
            sys.exit(1)
        targets = [(idx, users[idx])]
    else:
        targets = list(enumerate(users))

    print(f"SauceDemo Purchase POC")
    print(f"Running {len(targets)} user(s)\n")

    for i, (idx, user) in enumerate(targets):
        try:
            run_user(user, idx)
        except Exception as e:
            print(f"\n[User {idx + 1}] FAILED: {e}\n")

        if i < len(targets) - 1:
            print("Waiting 3s before next user...")
            time.sleep(3)

    print(f"\n{'='*60}")
    print(f"Done. {len(targets)} user(s) processed.")


if __name__ == "__main__":
    main()
