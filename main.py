from dotenv import load_dotenv
import os
import requests
from datetime import datetime

class Config:
    def __init__(self):
        load_dotenv()
        self.API_KEY = os.getenv("API-KEY")
        self.baseURL = "https://v3.football.api-sports.io"
        self.authHeader = {"x-apisports-key": self.API_KEY}


class APIClient:

    #static variables in order to maintain daily limit.
    apiCounter = 0
    maxDailyCount = 100
    lastReset = datetime.now().date() #track the last reset date

    def __init__(self):
        self.config = Config()
    
    @classmethod
    def resetLimit(cls):
        currentDate = datetime.now().date()
        if currentDate != cls.lastReset:
            cls.apiCounter = 0
            cls.lastReset = currentDate
            print("daily reset done.")

    def collectData(self, endpoint, params):
        #check if api call count needs to be reset for new day.
        self.resetLimit()

        if APIClient.apiCounter >= APIClient.maxDailyCount:
            print("Call limit has been hit.")
            return None
        
        url = f"{self.config.baseURL}/{endpoint}"
        response = requests.get(url, headers=self.config.authHeader, params=params)
        
        if response.status_code == 200:
            return response.json
        else:
            print(f"failed to collect data at endpoint {endpoint}")
            return None
        
def testClient():
    client = APIClient()

    print("Testing config...")
    print("API Key:", client.config.API_KEY)  # Should print your API key (or masked)
    print("Base URL:", client.config.baseURL)  # Should print: https://v3.football.api-sports.io
    print("Auth Header:", client.config.authHeader)  # Should include 'x-apisports-key'

    # Make a test API call to verify the connection works
    test_endpoint = "status"  # Simple endpoint that should work without params
    test_response = client.collectData(test_endpoint, params=None)

    # Check if API call was successful
    if test_response:
        print("API Client is working successfully!")
        print("API Response:", test_response)  # Should return a status message from API-Football
    else:
        print("API Client failed. Check API key or connection.")

# ✅ CALL TEST FUNCTION ONLY IF FILE IS RUN DIRECTLY
if __name__ == "__main__":
    testClient()





