'''
Purpose: This file data.py will set up the API keys and begin to collect the data with the API KEY. There is a limit of 100 calls due to subscription limitations, therefore this program will make sure it isn't exceeded, and collect historical data little by little each day. 
'''

from dotenv import load_dotenv
import os
import requests
from datetime import datetime
import json

load_dotenv()
print("API Key from .env:", os.getenv("API_KEY"))

class Config:
    def __init__(self):
        self.API_KEY = os.getenv("API_KEY")

        self.baseURL = "https://v3.football.api-sports.io"
        self.authHeader = {"x-rapidapi-key": self.API_KEY}


class APIClient:

    #static variables in order to maintain daily limit.
    apiCounter = 0 # Tracker of how many I have used.
    maxDailyCount = 100 # Daily limit that api key gave me.
    lastReset = datetime.now().date() # Track the last reset date
    USAGE_FILE = "apiUsage.json"

    def __init__(self):
        self.config = Config()
    
    @classmethod
    def resetLimit(cls):
        currentDate = datetime.now().date() # Obtain the current date.
        if currentDate != cls.lastReset:
            cls.apiCounter = 0
            cls.lastReset = currentDate
            print("daily reset done.")

    def collectData(self, endpoint, params):
        # Check if api call count needs to be reset for new day.
        self.resetLimit()

        if APIClient.apiCounter >= APIClient.maxDailyCount:
            print("Call limit has been hit.")
            return None
        
        # Create url.
        url = f"{self.config.baseURL}/{endpoint}"
        response = requests.get(url, headers=self.config.authHeader, params=params)
        
        if response.status_code == 200:
            APIClient.apiCounter += 1
            self.saveUsage() # ☆ update the usage ☆
            return response.json()
        else:
            print(f"failed to collect data at endpoint {endpoint}")
            return None
        
    '''
    Reads from a JSON file (api_usage.json).
    Retrieves the last recorded API call count and the date of the last reset.
    This prevents your API counter from resetting when the script is restarted unexpectedly.
    '''
    def loadUsage(self):
        
        #Checks if the persistence file (api_usage.json) exists.
        if os.path.exists(self.USAGE_FILE):

            #Opens the file in read mode ("r")
            with open(self.USAGE_FILE, 'r') as file:

                #Reads the JSON data from the file and converts it into a Python dictionary.
                data = json.load(file)

                #Converts the stored date string back into a datetime object for comparison.
                lastReset = datetime.strptime(data["lastReset"], "%Y-%m-%d").date()

                #Returns the saved API call count and the date of the last reset.
                return data["apiCounter"],lastReset
            
        return 0, datetime.now().date()

    '''
    Saves the current API call count and reset date into the JSON file after each successful API call. This ensures that any progress made is not lost between restarts.
    '''
    def saveUsage(self):
        #Opens the file in write mode ("w"), which creates a new file or overwrites an existing one.
        with open (self.USAGE_FILE, 'w') as file:

            #Converts the current API call count and last reset date into a JSON format and writes it to the file.
            json.dump({
                "apiCounter": self.apiCounter,
                "lastReset": self.lastReset.strftime("%Y-%m-%d")}, file)

#============== Actively collect the data with seasons ranging from 1992- present=============#

class DataCollector:

    def __init__(self):
        self.client = APIClient()

    def seasonList(self):
        currentSeason = datetime.now().year
        startYear = 1992
        return list(range(startYear, currentSeason))


    def currentSeasonCalc(self):
        today = datetime.now()
        return today.year if today.month >= 8 else today.year -1
            
    def premierLeagueTeams(self, leagueID=39):
        season = self.currentSeasonCalc()
        params = {
            "league": leagueID,
            "season": season
        }
        response = self.client.collectData("teams", params)
        
        if response:
            return response['response']
        else:
            
            print("fetching teams failed")
            return None
    

    def teamFixtures(self, teamID, leagueID=39):
        currentSeason = self.currentSeasonCalc()

        params = {
            "team": teamID,
            "league": leagueID,
            "season": currentSeason
        }
        response = self.client.collectData("fixtures", params)

        if response:
            return response['response']
        else:
            print(f"failed collected fixtures for team {teamID}")
            return None
        
    def matchScores(self, fixtureID):
        params = {"id": fixtureID}
        response = self.client.collectData("fixtures", params)

        if response:
            return response['response']
        else:
            print(f"failure to collect scores from fixture {fixtureID}")

    def getPlayers(self, teamID, season, leagueID=39):
        params = {
            "team": teamID,
            "season": season
        }
        response = self.client.collectData("players", params)

        if response:
            return response['response']
        else:
            print(f"failure to collect players from team {teamID}")
    
    def playerStats(self, playerID, season, leagueID=39):
        params = {
            "player": playerID,
            "season": season,
            "league": leagueID
        }
        response = self.client.collectData("players", params)

        if response:
            if 'errors' in response and response['errors']:
                print(f"API Error for player {playerID}: {response['errors']}")
            print(f"API Response for player {playerID}:", response)
            
            return response['response']
        else:
            print(f"failure to collect player statistics for player {playerID}")
            return None

    def collectData(self):

        # Get all the teams in the league.
        teams = self.premierLeagueTeams()

        if not teams:
            return 
        
        currentSeason = self.currentSeasonCalc()
        
        for team in teams:
            teamID = team['team']['id']
            print(f"collecting data for team {team['team']['id']}")

            # Get the fixtures
            fixtures = self.teamFixtures(teamID)

            if fixtures:
                for fixture in fixtures:
                    fixtureID = fixture['fixture']['id']
                    score = self.matchScores(fixtureID)
            
            # Get the players
            players = self.getPlayers(teamID, currentSeason)

            if players:
                for player in players:
                    playerID = player['player']['id']
                    playerStats = self.playerStats(playerID, currentSeason)







        
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

def test_data_collection():
    print("\nStarting Data Collection Test...")
    collector = DataCollector()

    # Fetch teams
    teams = collector.premierLeagueTeams()
    if teams:
        print(f"Successfully fetched {len(teams)} teams.")
    else:
        print("Failed to fetch teams.")

    # Fetch fixtures for the first team as a sample
    first_team = teams[0]
    team_id = first_team['team']['id']
    team_name = first_team['team']['name']
    print(f"Testing fixture collection for team: {team_name} (ID: {team_id})")

    fixtures = collector.teamFixtures(team_id)
    if fixtures:
        print(f"Fetched {len(fixtures)} fixtures for {team_name}.")
    else:
        print(f"Failed to fetch fixtures for {team_name}.")

    # Fetch player data for the first team
    players = collector.getPlayers(team_id, collector.currentSeasonCalc())
    if players:
        print(f"Fetched {len(players)} players for {team_name}.")
        # Test stats for the first player
        first_player = players[0]
        player_id = first_player['player']['id']
        player_name = first_player['player']['name']
        stats = collector.playerStats(player_id, collector.currentSeasonCalc())
        if stats:
            print(f"Stats successfully fetched for player: {player_name} (ID: {player_id})")
        else:
            print(f"Failed to fetch stats for player: {player_name}")
    else:
        print(f"Failed to fetch players for {team_name}.")
    
    




# ✅ CALL TEST FUNCTION ONLY IF FILE IS RUN DIRECTLY
if __name__ == "__main__":
    testClient()
    test_data_collection()