import requests
import time
import random
from collections import Counter, defaultdict

# ================= COLORS =================
RESET = "\033[0m"
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
CYAN = "\033[96m"
WHITE = "\033[97m"
BOLD = "\033[1m"
# ==========================================

API_URL = "https://draw.ar-lottery01.com/WinGo/WinGo_30S/GetHistoryIssuePage.json?ts={}"

last_prediction_size = None
last_prediction_number = None
last_period = None
last_seen_issue = None


# --------------------------------------------------
# Fetch API
# --------------------------------------------------
def fetch_history():
    ts = int(time.time() * 1000)
    r = requests.get(API_URL.format(ts), timeout=10)
    r.raise_for_status()
    return r.json()["data"]["list"]


# --------------------------------------------------
# Analyze Result
# --------------------------------------------------
def analyze_number(num):
    num = int(num)
    return num, "BIG" if num >= 5 else "SMALL"


# --------------------------------------------------
# Pattern AI Engine
# --------------------------------------------------
def ai_pattern_engine(history):
    seq = ["B" if int(i["number"]) >= 5 else "S" for i in history[:12]]
    s = "".join(seq)

    if s.startswith(("BSBS", "SBSB")):
        return "BIG" if seq[0] == "S" else "SMALL"
    if s.startswith("BBB"):
        return "SMALL"
    if s.startswith("SSS"):
        return "BIG"
    if s.startswith("BBSS"):
        return "BIG"
    if s.startswith("SSBB"):
        return "SMALL"

    return "BIG" if seq.count("B") >= seq.count("S") else "SMALL"


# --------------------------------------------------
# Multi-AI Big/Small Voting
# --------------------------------------------------
def ai_big_small_prediction(history):
    last_10 = history[:10]
    seq = ["BIG" if int(i["number"]) >= 5 else "SMALL" for i in last_10]

    streak = seq[0]
    count = 1
    for i in range(1, len(seq)):
        if seq[i] == streak:
            count += 1
        else:
            break

    ai1 = "SMALL" if count >= 3 and streak == "BIG" else "BIG" if count >= 3 else streak
    ai2 = "BIG" if seq.count("BIG") >= seq.count("SMALL") else "SMALL"
    ai3 = ai_pattern_engine(history)
    ai4 = "BIG" if seq[:5].count("BIG") >= 3 else "SMALL"

    votes = [ai1, ai1, ai2, ai3, ai3, ai3, ai4, ai4]
    final = Counter(votes).most_common(1)[0][0]
    confidence = int(votes.count(final) / len(votes) * 100)

    return final, confidence


# --------------------------------------------------
# Multi-AI Number Voting
# --------------------------------------------------
def ai_number_multi_voting(history, size):
    last_30 = [int(i["number"]) for i in history[:30]]
    last_5 = last_30[:5]
    score = defaultdict(int)

    def valid(n):
        return (size == "BIG" and n >= 5) or (size == "SMALL" and n < 5)

    for n in range(10):
        if not valid(n):
            continue
        score[n] += (last_30.index(n) * 3) if n in last_30 else 40
        score[n] += (30 - last_30.count(n)) * 2
        score[n] -= 20 if n in last_5 else -5
        score[n] += random.randint(-1, 1)

    return max(score, key=score.get)


# --------------------------------------------------
# API Result Status
# --------------------------------------------------
def api_result_status(issue, result_number):
    global last_period, last_prediction_size, last_prediction_number

    if last_period == issue:
        return "PENDING"

    actual_size = "BIG" if result_number >= 5 else "SMALL"

    if actual_size == last_prediction_size:
        if result_number == last_prediction_number:
            return "SURESHOT"
        return "WIN"
    return "LOSE"


# --------------------------------------------------
# Display Result
# --------------------------------------------------
def print_result(status):
    print(f"{BLUE}{'='*52}{RESET}")
    if status == "PENDING":
        print(f"{YELLOW}{BOLD}RESULT  : pending....{RESET}")
    elif status == "WIN":
        print(f"{GREEN}{BOLD}RESULT  : victory ✅️{RESET}")
    elif status == "SURESHOT":
        print(f"{GREEN}{BOLD}RESULT  : victory ✅️  sureshot 🏆{RESET}")
    elif status == "LOSE":
        print(f"{RED}{BOLD}RESULT  : better luck next time ❣️{RESET}")
    print(f"{BLUE}{'='*52}{RESET}")


# --------------------------------------------------
# Display Next Prediction
# --------------------------------------------------
def print_next_prediction(next_period, size, number, confidence):
    print(f"\n{CYAN}{BOLD}⏳ NEXT PREDICTION (After 5 Seconds){RESET}")
    print(f"{BLUE}{'-'*52}{RESET}")
    print(f"{WHITE}Next Period   : {BOLD}{next_period}{RESET}")
    print(f"{WHITE}Prediction    : {GREEN}{number} ({size}){RESET}")
    print(f"{WHITE}Confidence    : {YELLOW}{confidence}%{RESET}")
    print(f"{BLUE}{'-'*52}{RESET}\n")


# --------------------------------------------------
# MAIN LOOP (30s API SYNC)
# --------------------------------------------------
if __name__ == "__main__":
    print(f"{CYAN}{BOLD}🚀 WINGO 30s MULTI-AI SYSTEM STARTED{RESET}\n")

    while True:
        try:
            history = fetch_history()
            latest = history[0]
            issue = latest["issueNumber"]

            if issue != last_seen_issue:
                last_seen_issue = issue

                result_number, result_size = analyze_number(latest["number"])
                status = api_result_status(issue, result_number)

                print(f"{WHITE}-----------------------------------------{RESET}")
                print(f"{WHITE}Period        : {BOLD}{issue}{RESET}")
                print(f"{WHITE}Result        : {BOLD}{result_number} ({result_size}){RESET}")
                print_result(status)

                # Prepare NEXT prediction
                ai_size, confidence = ai_big_small_prediction(history)
                ai_number = ai_number_multi_voting(history, ai_size)
                next_period = str(int(issue) + 1)

                # Save for next round
                last_prediction_size = ai_size
                last_prediction_number = ai_number
                last_period = issue

                # Delay 5 seconds then show next prediction
                time.sleep(5)
                print_next_prediction(next_period, ai_size, ai_number, confidence)

            time.sleep(1.5)

        except Exception as e:
            print(f"{RED}ERROR:{RESET}", e)
            time.sleep(3)