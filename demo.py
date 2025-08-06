from datetime import datetime, timezone

if __name__ == '__main__':
    request_ts = datetime.now().strftime("%m-%d %H:%M:%S")
    print(request_ts)