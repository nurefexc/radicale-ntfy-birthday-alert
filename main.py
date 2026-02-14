import requests
import vobject
import datetime
import os
import logging
import time
import xml.etree.ElementTree as ET
import re
import random
from typing import List, Tuple, Optional
from urllib.parse import urljoin

# --- Configuration ---
RADICALE_URL = os.getenv("RADICALE_URL")
RADICALE_USER = os.getenv("RADICALE_USER")
RADICALE_PASS = os.getenv("RADICALE_PASS")
NTFY_URL = os.getenv("NTFY_URL")
NTFY_TOKEN = os.getenv("NTFY_TOKEN")
TZ = os.getenv("TZ", "UTC")
ICON_URL = "https://img.icons8.com/liquid-glass/48/birthday.png"

# Set timezone for the process
os.environ["TZ"] = TZ
if hasattr(time, 'tzset'):
    time.tzset()

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - [%(levelname)s] - %(message)s')
logger = logging.getLogger(__name__)


def get_vcf_urls() -> List[str]:
    """
    Fetches the list of .vcf (vCard) URLs from the Radicale server using PROPFIND.

    Returns:
        List[str]: A list of absolute URLs for the discovered vCard files.
    """
    headers = {"Depth": "1", "Content-Type": "application/xml; charset=utf-8"}
    body = '<?xml version="1.0" encoding="utf-8" ?><D:propfind xmlns:D="DAV:"><D:prop><D:getcontenttype/></D:prop></D:propfind>'
    try:
        r = requests.request(
            "PROPFIND",
            RADICALE_URL,
            auth=(RADICALE_USER, RADICALE_PASS),
            data=body,
            headers=headers,
            timeout=30
        )
        if r.status_code != 207:
            logger.error(f"Discovery failed: Status {r.status_code}")
            return []

        root = ET.fromstring(r.text)
        namespaces = {'d': 'DAV:'}
        urls = []
        for href in root.findall('.//d:href', namespaces):
            link = href.text
            if link and link.endswith('.vcf'):
                urls.append(urljoin(RADICALE_URL, link))
        return list(set(urls))
    except Exception as e:
        logger.error(f"CardDAV Discovery failure: {e}")
        return []


def parse_bday(bday_str: str) -> Tuple[bool, Optional[int]]:
    """
    Parses a birthday string from a vCard and checks if it is today.

    Args:
        bday_str (str): The BDAY value from the vCard.

    Returns:
        Tuple[bool, Optional[int]]: A tuple containing (is_birthday_today, age).
    """
    raw = str(bday_str).split('T')[0].strip().upper()
    today = datetime.date.today()
    month, day, birth_year = None, None, None
    try:
        if raw.startswith('--'):
            # Handle format like --MMDD
            digits = raw.replace('-', '')[2:]
            month, day = int(digits[0:2]), int(digits[2:4])
        elif re.match(r'^(XXXX|0000)', raw):
            # Handle format like XXXX-MM-DD or 0000-MM-DD
            digits = raw.replace('-', '')[4:]
            month, day = int(digits[0:2]), int(digits[2:4])
        elif '-' in raw and len(raw) >= 10 and raw[0:4].isdigit():
            # Handle YYYY-MM-DD
            dt = datetime.datetime.strptime(raw[0:10], '%Y-%m-%d').date()
            month, day, birth_year = dt.month, dt.day, dt.year
        elif len(raw) == 8 and raw.isdigit():
            # Handle YYYYMMDD
            dt = datetime.datetime.strptime(raw, '%Y%m%d').date()
            month, day, birth_year = dt.month, dt.day, dt.year

        if month == today.month and day == today.day:
            # Calculate age if birth year is known and reasonable
            age = (today.year - birth_year) if birth_year and birth_year > 1604 else None
            return True, age
    except Exception as e:
        logger.debug(f"Failed to parse birthday '{bday_str}': {e}")
        pass
    return False, None


def send_ntfy_alert(name: str, age: Optional[int], vcard: vobject.base.Component):
    """
    Sends a notification via ntfy about a birthday.

    Args:
        name (str): Name of the person.
        age (Optional[int]): Age of the person (if known).
        vcard (vobject.base.Component): The parsed vCard object to extract extra info.
    """
    actions = []
    phone = getattr(vcard, 'tel', None).value if hasattr(vcard, 'tel') else None

    matrix_id = None
    if hasattr(vcard, 'note'):
        for line in vcard.note.value.splitlines():
            if line.lower().startswith('matrix:'):
                matrix_id = line.split(':', 1)[1].strip()

    if matrix_id:
        actions.append(f"view, Matrix, https://matrix.to/#/{matrix_id.strip()}, clear=true")
    if phone:
        p = ''.join(filter(lambda x: x.isdigit() or x == '+', phone))
        actions.append(f"view, Call, tel:{p}, clear=true")

    headers = {
        "Title": f"🎂 Birthday: {name}".encode('utf-8'),
        "Tags": "birthday,cake",
        "Icon": ICON_URL,
        "Priority": "4",
        "Actions": "; ".join(actions) if actions else ""
    }
    if NTFY_TOKEN:
        headers["Authorization"] = f"Bearer {NTFY_TOKEN}"

    msg = f"Today is {name}'s birthday!{f' ({age} years old)' if age else ''}"
    try:
        requests.post(NTFY_URL, data=msg.encode('utf-8'), headers=headers, timeout=20)
    except Exception as e:
        logger.error(f"Failed to send ntfy alert: {e}")


def check_birthdays():
    """
    Main logic to sync with Radicale and trigger notifications for birthdays today.
    """
    if not all([RADICALE_URL, RADICALE_USER, RADICALE_PASS, NTFY_URL]):
        logger.error("Missing configuration. Check your environment variables.")
        return

    urls = get_vcf_urls()
    logger.info(f"Radicale sync. {len(urls)} contacts found.")
    for url in urls:
        try:
            res = requests.get(url, auth=(RADICALE_USER, RADICALE_PASS), timeout=20)
            if not res.ok:
                continue
            for vcard in vobject.readComponents(res.text):
                if hasattr(vcard, 'bday'):
                    is_today, age = parse_bday(vcard.bday.value)
                    if is_today:
                        name = vcard.fn.value if hasattr(vcard, 'fn') else "Unknown"
                        send_ntfy_alert(name, age, vcard)
                        logger.info(f"Notification sent: {name}")
        except Exception as e:
            logger.error(f"Error during processing ({url}): {e}")


if __name__ == "__main__":
    logger.info("Birthday monitor service started. Waiting for the midnight window (00:00 - 01:00).")

    while True:
        now = datetime.datetime.now()
        # Calculate next midnight
        target = (now + datetime.timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)

        # If we are currently between 00:00 and 01:00, run it now!
        if now.hour == 0:
            logger.info("Current time is within the execution window. Starting sync...")
            check_birthdays()
            # After run, wait until next day's midnight to avoid double execution
            now = datetime.datetime.now()
            target = (now + datetime.timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)

        # Random jitter between 0 and 59 minutes within the 00:00-01:00 window
        jitter = random.randint(0, 3540)
        sleep_secs = (target - now).total_seconds() + jitter

        logger.info(
            f"Next sync scheduled for: {target + datetime.timedelta(seconds=jitter)}. Sleeping for {sleep_secs / 3600:.2f} hours."
        )
        time.sleep(sleep_secs)
