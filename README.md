# epitome

A janky webpage for Netrunner TOs to share leaderboards and match results/pairings. It reads the JSON part of a TOME export to generate the aforementioned leaderboard and results/pairings. *Warning: it is very much a kludge at the moment.*

### Creating a tournament page

Create a new tournament at:  
`https://anr-epitome.appspot.com/_to/new`

Standings and pairings will be available at:  
`https://anr-epitome.appspot.com/[tournament-name]/`

### Updating the tournament page

Each round, after you generate pairings in TOME, export the tournament in TOME and update epiTOME with the new JSON.

If you have the tournament's codeword, you can update an existing tournament at:  
```https://anr-epitome.appspot.com/[tournament-name]/manage```
