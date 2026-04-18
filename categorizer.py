"""
PaisaSense AI — Categorization Engine
Handles merchant extraction and transaction categorization.
"""

import re


# Banking noise words that add no value for categorization
_NOISE_WORDS = {
    "upi", "dr", "cr", "neft", "imps", "rtgs", "transfer", "payment",
    "bank", "hdfc", "sbi", "pnb", "icici", "axis", "kotak", "paytm",
    "phonepe", "gpay", "googlepay", "bhim", "net", "banking", "txn",
    "trf", "to", "from", "ref", "no", "id", "via", "mob", "ac",
    "account", "debit", "credit", "transaction", "reversal", "chg",
    "charge", "fee", "gst", "tax", "p2p", "p2m", "pay", "mmt", "atm",
    "cash", "withdraw", "deposit", "bal", "balance", "avbl",
}

# Common Indian first/last names — used to detect personal UPI transfers
_PERSONAL_NAME_HINTS = {
    "kumar", "singh", "sharma", "verma", "gupta", "yadav", "mishra",
    "patel", "joshi", "mehta", "shah", "reddy", "nair", "pillai",
    "mahesh", "ravi", "anil", "suresh", "ramesh", "rajesh", "rahul",
    "priya", "neha", "pooja", "anita", "sunita", "sanjay", "amit",
    "vikram", "deepak", "ajay", "vishal", "rohit", "mukesh", "dinesh",
    "santosh", "ashok", "vikas", "nitin", "mohan", "shyam", "ganesh",
    "harish", "girish", "naresh", "umesh", "lokesh", "rupesh",
    "vishesh", "mani", "tripathi", "tiwari", "chauhan", "pandey",
    "dubey", "dwivedi", "kulkarni", "iyer", "hegde", "shetty",
    "chandra", "bose", "mukherjee", "banerjee", "das", "ghosh",
    "thakur", "rawat", "bisht", "rana", "bhat", "kaur", "arora",
    "kapoor", "khanna", "malhotra", "bedi", "sethi", "walia",
    "anand", "saxena", "srivastava", "shukla", "trivedi",
}

# Merchant UPI handles — these are businesses, NOT personal transfers
_MERCHANT_UPI_HANDLES = {
    "olamoney", "paytm", "amazonpay", "swiggypay", "zomatopay",
    "uberindiaapp", "netflixupi", "juspay", "razorpay", "cashfree",
    "phonepe", "gpay", "bharatpe", "mobikwik", "freecharge",
    "icici", "hdfc", "sbi", "axisbank", "okhdfcbank", "apl", "ibl", "pnb", "kotak",
}

# Noise suffixes commonly appended to merchant names in UPI strings
_MERCHANT_SUFFIX_NOISE = re.compile(
    r'(upi|pay|payments?|india|pvt|ltd|app|online|store|services?)$', re.IGNORECASE
)

CATEGORY_KEYWORDS = {
    "Food": [
        "swiggy", "zomato", "mcdonalds", "mcdonald", "kfc", "dominos",
        "domino", "pizza", "burger", "biryani", "restaurant", "cafe",
        "dhaba", "hotel", "eatery", "chai", "tea", "chaayos", "chaipoint",
        "chai point", "subways", "subway", "barbeque", "barbeque nation",
        "box8", "freshmenu", "faasos", "rebel foods", "instacafe",
        "haldiram", "bikaji", "snacks", "canteen", "mess",
    ],
    "Travel": [
        "uber", "ola", "rapido", "metro", "auto", "rickshaw", "cab",
        "irctc", "makemytrip", "goibibo", "cleartrip", "easemytrip",
        "flight", "bus", "redbus", "abhibus", "yatra", "railway",
        "airways", "airlines", "indigo", "spicejet", "airindia",
        "airport", "petrol", "fuel", "diesel", "pump", "parking",
    ],
    "Groceries": [
        "bigbasket", "grofers", "blinkit", "zepto", "instamart",
        "dmart", "jiomart", "vegetables", "fruits", "grocery",
        "supermarket", "nature basket", "spencer", "more supermarket",
        "lulu", "hypermarket",
    ],
    "Shopping": [
        "amazon", "flipkart", "myntra", "ajio", "nykaa", "meesho",
        "shopify", "reliance", "mart", "store", "shop",
        "tatacliq", "cliq", "snapdeal", "paytmmall",
        "bewakoof", "rare rabbit", "uniqlo", "zara", "h&m", "hm",
    ],
    "Bills": [
        "rent", "electricity", "bescom", "msedcl", "bses", "tata power",
        "gas", "water", "wifi", "internet", "broadband", "airtel",
        "jio", "vodafone", "vi", "bsnl", "mobile", "recharge",
        "insurance", "lic", "premium", "postpaid", "prepaid",
        "municipal", "society", "maintenance",
    ],
    "Subscriptions": [
        "netflix", "prime", "amazon prime", "spotify", "hotstar",
        "disney", "youtube", "zee5", "sonyliv", "voot", "jiocinema",
        "apple", "google one", "dropbox", "notion", "slack",
        "subscription", "membership", "annual plan", "monthly plan",
        "coursera", "udemy", "skillshare",
    ],
    "Health": [
        "pharmacy", "chemist", "medplus", "apollo pharmacy", "1mg",
        "netmeds", "practo", "doctor", "hospital", "clinic", "lab",
        "diagnostic", "thyrocare", "lal path", "blood test", "gym",
        "cult fit", "cure fit", "yoga", "fitness",
    ],
    "Personal": [],  # filled dynamically by is_personal_transfer
}


def clean_description(text: str) -> str:
    """Lowercase, strip banking noise words, numbers, and special chars."""
    if not isinstance(text, str):
        return ""
    text = text.replace("\n", " ").replace("\r", " ").lower()
    text = re.sub(r'[^a-z\s]', ' ', text)
    tokens = [t for t in text.split() if t not in _NOISE_WORDS and len(t) > 1]
    return " ".join(tokens).strip()


def is_personal_transfer(text: str) -> bool:
    """
    Returns True if the narration looks like a person-to-person transfer.
    Distinguishes personal UPI IDs from merchant/bank handles.
    """
    if not isinstance(text, str):
        return False
    lower = text.lower()

    upi_match = re.search(r'([a-z0-9.\-_]+)@([a-z]+)', lower)
    if upi_match:
        prefix = upi_match.group(1)
        suffix = upi_match.group(2)
        if suffix in _MERCHANT_UPI_HANDLES or prefix in _MERCHANT_UPI_HANDLES:
            return False
        return True

    if re.search(r'\b[6-9]\d{9}\b', text):
        return True

    tokens = set(re.sub(r'[^a-z\s]', ' ', lower).split())
    if tokens & _PERSONAL_NAME_HINTS:
        return True

    return False


def _clean_merchant_token(token: str) -> str:
    """Strip trailing UPI/pay/india noise from a merchant token."""
    token = token.strip()
    for _ in range(3):
        cleaned = _MERCHANT_SUFFIX_NOISE.sub("", token).strip()
        if cleaned == token or len(cleaned) < 3:
            break
        token = cleaned
    return token


def extract_merchant(description: str) -> str:
    """
    Pull the most meaningful merchant token from a raw bank narration.
    Handles HDFC (slash-separated) and PNB (dash-separated) formats.
    """
    if not isinstance(description, str):
        return "Unknown"

    raw = description.strip().replace("\n", " ").replace("\r", " ")

    def best_candidate(parts: list) -> str | None:
        candidates = []
        for part in parts:
            part = part.strip()
            if not part or re.match(r'^\d+$', part):
                continue
            pl = part.lower()
            if pl in _NOISE_WORDS or len(part) < 3:
                continue
            if re.match(r'^[A-Z]{2,6}$', part):
                continue
            candidates.append(part)
        if not candidates:
            return None
        best = max(candidates, key=len)
        return _clean_merchant_token(best)

    if "/" in raw:
        result = best_candidate(raw.split("/"))
        if result:
            return result

    if "-" in raw:
        result = best_candidate(raw.split("-"))
        if result:
            return result

    cleaned = clean_description(raw)
    return cleaned.title() if cleaned else "Unknown"


def categorize_transaction(description: str) -> str:
    """Categorize a raw bank narration into a spending category."""
    if not isinstance(description, str):
        return "Others"

    if is_personal_transfer(description):
        return "Personal"

    merchant = extract_merchant(description).lower()
    cleaned  = clean_description(description)
    combined = f"{merchant} {cleaned}"

    for category, keywords in CATEGORY_KEYWORDS.items():
        if category == "Personal":
            continue
        if any(kw in combined for kw in keywords):
            return category

    return "Others"


# Alias for backward compatibility
def categorize(merchant: str) -> str:
    return categorize_transaction(merchant)
