'''
Purpose: This file data.py will set up the API keys and begin to collect the data with the API KEY. There is a limit of 100 calls due to subscription limitations, therefore this program will make sure it isn't exceeded, and collect historical data little by little each day. 
'''

from dotenv import load_dotenv
import os
import requests
from datetime import datetime
import json
import logging


#create custom config for logging.
logging.basicConfig(level=logging.INFO, filename="dataCollection.log", filemode="w", format="%(asctime)s - %(levelname)s - %(message)s")


load_dotenv()
print("API Key from .env:", os.getenv("API_KEY"))

class Config:
    def __init__(self):
        self.API_KEY = os.getenv("API_KEY")

        self.baseURL = "https://v3.football.api-sports.io"
        self.authHeader = {"x-rapidapi-key": self.API_KEY} 


class APIClient:

    apiCounter = 0 
    maxDailyCount = 7500 
    lastReset = datetime.now().date() 
    USAGE_FILE = "apiUsage.json"

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

        self.resetLimit()
        if APIClient.apiCounter >= APIClient.maxDailyCount:
            logging.warning("API call limit has been reached.")
            return None
        
        url = f"{self.config.baseURL}/{endpoint}"

        try:
            response = requests.get(url, headers=self.config.authHeader, params=params)  
            response.raise_for_status()
            APIClient.apiCounter += 1
            self.saveUsage()
            logging.info(f"logged data for {endpoint} successfully")
            return response.json()

        except:
            logging.exception(f"failed to collect data at endpoint {endpoint}")
            return None
        
    '''
    Reads from a JSON file (api_usage.json).
    Retrieves the last recorded API call count and the date of the last reset.
    This prevents your API counter from resetting when the script is restarted unexpectedly.
    '''
    #iffy on all the returns... ask for other opinion for this!!!!!
    def loadUsage(self):
        
        #Checks if the persistence file (api_usage.json) exists.
        if not os.path.exists(self.USAGE_FILE):
            return 0, datetime.now().date()

        try:
            #Opens the file in read mode ("r")
            with open(self.USAGE_FILE, 'r') as file:

                #Reads the JSON data from the file and converts it into a Python dictionary.
                data = json.load(file)

                #Converts the stored date string back into a datetime object for comparison.
                lastReset = datetime.strptime(data["lastReset"], "%Y-%m-%d").date()

                #Returns the saved API call count and the date of the last reset.
                return data["apiCounter"],lastReset
        except(json.JSONDecodeError, FileNotFoundError) as e:
            logging.exception(f"Unable to load api usage file: {e}")
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
        params = {"league": leagueID, "season": season}

        try :
            response = self.client.collectData("teams", params)
            if response:
                return response['response']
            else:
                logging.warning(f"API returned no valid data for leage {leagueID}.")
                return None
            
        except (Exception) as e:
            logging.info(f"Error with collecting premier league teams: {e}")
            return None
    
    def teamFixtures(self, teamID, leagueID=39):
        currentSeason = self.currentSeasonCalc()
        params = {"team": teamID, "league": leagueID, "season": currentSeason}

        try:
            response = self.client.collectData("fixtures", params)
            if response:
                return response['response']
            else:
                logging.warning(f"API returned no valid data for team {teamID}, season {currentSeason}.")
                return None  
    
        except (Exception) as e:
            logging.info(f"Unexpected error, could not collect fixtures for {teamID}: {e}")
            return None

        
    def fixtureStats(self, fixtureID, teamID):
        params = {"fixture": fixtureID, "team":teamID}
        try: 
            response = self.client.collectData("fixtures/statistics", params)
            if response:
                return response['response']
            else:
                logging.warning(f"API returned no valid data for fixture {fixtureID}.")
                return None
            
        except (Exception) as e:
            logging.info(f"Unexpected error, could not collect stats for fixture {fixtureID}: {e}")
            return None
    
    def fixtureStatsPlayers(self, fixtureID, teamID):
        params = {"fixture": fixtureID, "team": teamID}

        try:
            response = self.client.collectData("fixtures/players", params)
            if response:
                return response['response']
            else:
                logging.warning("API returned no valid data for fixture players")
                return None
            
        except (Exception) as e:
            logging.info(f"Error, could not collect any data for fixtures players: {e}")
            return None
        
    def matchEvents(self, fixtureID, teamID):
        params = {"fixture": fixtureID, "team":teamID}
        try:
            response = self.client.collectData("fixtures/events", params)
            if response:
                return response['response']
            else:
                logging.info(f"API returned no valid data for match events for fixture {fixtureID} and team {teamID}")
                return None
            
        except (Exception) as e:
            logging.info(f"Error, could not collect any match events for fixture {fixtureID} and team {teamID}: {e}")
            return None
        
    def lineups(self, fixtureID, teamID):
        params = {"fixture": fixtureID, "team":teamID}
        try:
            response = self.client.collectData("fixtures/lineups", params)
            if response:
                return response['response']
            else:
                logging.info(f"API did not return valid data for match lineups for fixture {fixtureID} and team {teamID}.")
                return None

        except (Exception) as e:
            logging.info(f"Error, could not collect any lineups for fixture {fixtureID} and team {teamID}: {e} ")
            return None
    
    def MatchScores(self, fixtureID):
        params = {"fixture": fixtureID}
        try:
            response = self.client.collectData("fixtures/statistics", params)
            if response:
                return response['response']
            else:
                logging.info(f"API did not return valid match scores for fixture {fixtureID}.")
                return None
        except (Exception) as e :
            logging.info(f"Error, unable to collect any match score data for fixture {fixtureID}: {e}")
            return None

    def teamStats(self, teamID, leagueID=39):
        currentSeason = self.currentSeasonCalc()
        params = {"season":currentSeason, "team":teamID, "league": leagueID}

        try:
            response = self.client.collectData("teams/statistics", params)
            if response:
                return response['response']
            else:
                logging.info(f"API unable to collect data statistics for team {teamID}")
                return None
        except (Exception) as e:
            logging.info(f"Error, unable to collect data for team stats: {e}")
            return None


    def getPlayers(self, teamID):
        params = {"team": teamID}

        try:
            response = self.client.collectData("players/squads", params)
            if response:
                return response['response']
            else:
                logging.info(f"API unable to return valid data for players on team {teamID}.")
                return None
        
        except (Exception) as e:
            logging.info(f"Error, cannot collect any data for players on team {teamID}: {e}")
            return None
    
    
    def playerStats(self,season,teamID, playerID, leagueID=39):
        params = {"season": season, "league": leagueID, "team": teamID, "page": 1}
        all_players_data = []

        while True:
            response = self.client.collectData("players", params)  # Fetch from API

            if response and 'response' in response:
                players_data = response['response']
                all_players_data.extend(players_data)  # Store all fetched players

                # Check if the player is in the current response
                for player_entry in players_data:
                    if player_entry['player']['id'] == playerID:
                        print(f" Found player data: {player_entry}")
                        return player_entry  # Return the correct player's stats

                # Handle pagination: Move to the next page if available
                current_page = response['paging']['current']
                total_pages = response['paging']['total']

                if current_page >= total_pages:
                    break  # Stop if we've fetched all pages

                params['page'] += 1  # Move to the next page
            else:
                print(f" Failed to collect statistics for Player {playerID} on page {params['page']}.")
                break  # Stop if API fails

        print(f"Player {playerID} not found after searching {len(all_players_data)} players across all pages.")
        return None  # Return None if player is not found

        
    def getInjuries(self, leagueID=39):
        season = self.currentSeasonCalc()
        params = {"league": leagueID, "season": season}
        try:
            response = self.client.collectData("injuries", params)
            if response:
                return response['response']
            else:
                logging.info(f"API unable to return valid data of injuries for season {season}.")
        except (Exception) as e :
            logging.info(f"Error, unable to collect data for season {season}.")
            return None
        
    def leagueStandings(self, leagueID=39):
        season = self.currentSeasonCalc()
        params = {"league": leagueID, "season": season}

        try:
            response = self.client.collectData("standings", params)
            if response:
                return response['response']
            else:
                logging.info(f"API unable to return any data of standings for league {leagueID}.")
                return None    
        except (Exception) as e:
            logging.info(f"Error, unable to collect any data of standings for league {leagueID}: {e}")
            return None

    def topPerformers(self, leagueID=39):
        season = self.currentSeasonCalc()
        params = {"league": leagueID, "season": season}

        try:
            response = self.client.collectData("players/topscorers", params)
            if response:
                return response['response']
            else:
                logging.info(f"API unable to return data for top performers during season {season}.")
                return None
        except (Exception) as e:
            logging.info(f"Error, unable to collect any data for top performers for season {season}: {e}")
            return None
        
    def teamTransfers(self, teamID):
        params = {"team": teamID}
        response = self.client.collectData("transfers", params)

        try:
            if response:
                return response['response']
            else:
                logging.info(f"API unable to return team transfers for team {teamID}.")
                return None
        except (Exception) as e:
            logging.info(f"Error, unable to colelct data from team transfers for team {teamID}: {e}")
            return None
        

    def collectData(self):
        print("\nStarting Data Collection...")

        teams = self.premierLeagueTeams()
        
        if not teams:
            print(" Failed to fetch teams.")
            return

        currentSeason = self.currentSeasonCalc()
        print(f" Current Season: {currentSeason}")

        cached_player_stats = {}  # Store player stats to prevent duplicate API calls

        for team in teams:
            teamID = team['team']['id']
            teamName = team['team']['name']
            print(f"\n Collecting data for {teamName} (ID: {teamID})...")

            # Fetch Fixtures
            fixtures = self.teamFixtures(teamID)
            fixture_data = {}

            if fixtures:
                for fixture in fixtures:
                    fixtureID = fixture['fixture']['id']
                    score = self.matchScores(fixtureID)
                    if score is not None:
                        fixture_data[fixtureID] = score
                    else:
                        print(f"No match score found for Fixture {fixtureID}.")
            
            print(f"Collected {len(fixture_data)} match scores for {teamName}.")

            # Fetch Players
            players = self.getPlayers(teamID, currentSeason)

            if players:
                for player in players:
                    playerID = player['player']['id']
                    playerName = player['player']['name']

                    # Check if we already fetched this player's stats
                    if playerID not in cached_player_stats:
                        playerStats = self.playerStats(playerID, currentSeason, teamID)
                        if playerStats:
                            cached_player_stats[playerID] = playerStats
                        else:
                            print(f"⚠️ No stats found for Player {playerName} (ID: {playerID}).")
                    else:
                        print(f"⏳ Using cached stats for {playerName} (ID: {playerID}).")

            print(f"Collected stats for {len(cached_player_stats)} players in {teamName}.")

        print("\nData Collection Completed!")


        
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
    currentSeason = collector.currentSeasonCalc()
    print(currentSeason)

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
    players = collector.getPlayers(team_id)
    if players:
        print(f"Fetched {len(players)} players for {team_name}.")
        # Test stats for the first player
        first_player = players[0]
        player_id = first_player['players'][20]['id']
        print(player_id)
        player_name = first_player['players'][20]['name']
        print(player_name)

        stats = collector.playerStats(collector.currentSeasonCalc(), team_id, player_id)
        if stats:
            print(f"Stats successfully fetched for player: {player_name} (ID: {player_id})")
            print(stats)
        else:
            print(f"Failed to fetch stats for player: {player_name}")
    else:
        print(f"Failed to fetch players for {team_name}.")
    
    

if __name__ == "__main__":
    testClient()
    test_data_collection()