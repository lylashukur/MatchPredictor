-- Teams Table --
Create Table teams 
(

);

Create Table players
(

);

Create Table playerStats
(
    -- References teamID and playerID
);

Create Table fixtures
(
    -- References away and home team ID
);

Create Table matchEvents
(
    -- will reference player id and fixtures id
);

Create Table playerTeams
(
    -- references players ID and teams ID
    -- Primary key will be season, teamID and playerID
);
-- Indexes for performance optmiziation
