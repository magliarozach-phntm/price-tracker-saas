import time
import schedule
from app.main import check_prices

schedule.every(6).hours.do(check_prices)

def run():
    print("Price tracker running...")
    check_prices()

    while True:
        schedule.run_pending()
        time.sleep(60)