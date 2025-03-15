import argparse
from io import BytesIO
import json
import os
import boto3

from footgraph.download import APIDownloader



def main(date: str):
    url = "https://api-football-v1.p.rapidapi.com/v3/fixtures"
    querystring = {"date": date}
    api_key = os.environ.get("API_FOOTBALL_KEY")
    headers = {
        "x-rapidapi-key": api_key,
        "x-rapidapi-host": "api-football-v1.p.rapidapi.com"
    }
    downloader = APIDownloader(request_limit=100)
    response = downloader.download(url, headers=headers, params=querystring)
    response_json = response.json()

    s3 = boto3.resource('s3', 
        endpoint_url='https://localhost:9000',
        aws_access_key_id=os.environ.get("ACCESS_KEY"),
        aws_secret_access_key=os.environ.get("ACCESS_KEY"),
    )
    json_bytes = json.dumps(response_json).encode('utf-8')
    s3.put_object(Bucket="raw-data", Key=f"{date}/schedule.json", Body=BytesIO(json_bytes), ContentType='application/json')



if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('date')
    args = parser.parse_args()
    main(args.date)