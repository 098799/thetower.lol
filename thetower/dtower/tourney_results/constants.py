champ = "Champions"
plat = "Platinum"
gold = "Gold"
silver = "Silver"
copper = "Copper"


data_folder_name_mapping = {
    "data": champ,
    "plat": plat,
    "gold": gold,
    "silver": silver,
    "copper": copper,
}
league_to_folder = {value: key for key, value in data_folder_name_mapping.items()}


leagues_choices = [(league, league) for league in data_folder_name_mapping.values()]
