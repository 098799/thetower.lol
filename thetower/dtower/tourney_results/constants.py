champ = "Champions"
plat = "Platinum"
gold = "Gold"
silver = "Silver"
copper = "Copper"


leagues = [champ, plat, gold, silver, copper]


data_folder_name_mapping = {
    "data": champ,
    "plat": plat,
    "gold": gold,
    "silver": silver,
    "copper": copper,
}
league_to_folder = {value: key for key, value in data_folder_name_mapping.items()}


leagues_choices = [(league, league) for league in data_folder_name_mapping.values()]


us_to_jim = {
    champ: "Champion",
    plat: plat,
    gold: gold,
    silver: silver,
    copper: copper,
}


wave_border_choices = [0, 250, 500, 750, 1000, 1250, 1500, 1750, 2000, 2250, 2500, 2750, 3000, 3500, 4000, 100000]
