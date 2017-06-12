squads = {"COMMANDER": [["COMMANDER"], [""], [""]],
          "OBSERVERS": [["OBSERVER", "OBSERVER"], [""], [""]],
          "ENGINEERS": [["ENGINEER", "ENGINEER"], ["ENGINEER", "ENGINEER"], [""]],
          "GUN_CREW": [["GUN CREW", "GUN CREW", "GUN CREW"], [""], [""]],
          "HEAVY_SUPPORT_TEAM": [["MACHINE_GUNNER", "MACHINE_GUNNER", "MACHINE_GUNNER", "MACHINE_GUNNER"], [""], [""]],
          "ANTI-TANK_TEAM": [["ANTI-TANK_RIFLE", "ANTI-TANK_RIFLE"], ["ANTI-TANK_RIFLE", "ANTI-TANK_RIFLE"], [""]],
          "HEAVY_ANTI-TANK_TEAM": [["HEAVY_ANTI-TANK_RIFLE", "HEAVY_ANTI-TANK_RIFLE"], [""], [""]],
          "MARKSMEN": [["MARKSMAN", "MARKSMAN", "MARKSMAN"], [""], [""]],
          "SCOUT": [["MARKSMAN"], [""], [""]],
          "GRENADIERS": [["GRENADIER", "GRENADIER", "GRENADIER", "OFFICER"], [""], [""]],
          "SAPPERS": [["SAPPER", "SAPPER", "SAPPER", "OFFICER"], [""], [""]],
          "RIFLEMEN_36": [["RIFLEMAN", "RIFLEMAN", "OFFICER", "RIFLEMAN", "RIFLEMAN"],
                          ["RIFLEMAN", "RIFLEMAN", "RIFLEMAN", "RIFLEMAN", "RIFLEMAN"],
                          ["RIFLEMAN", "RIFLEMAN", "RIFLEMAN", "RIFLEMAN", "RIFLEMAN"]],
          "SUPPORT_36": [["MEDIC", "MACHINE_GUNNER", "OFFICER", "MACHINE_GUNNER", "LIGHT_ANTI-TANK_RIFLE"],
                         ["RIFLEMAN", "RIFLEMAN", "RIFLEMAN", "RIFLEMAN", "RIFLEMAN"], [""]],
          "RIFLEMEN_39": [["RIFLEMAN", "RIFLEMAN", "COMBAT_OFFICER", "MACHINE_GUNNER", "RIFLEMAN"],
                          ["RIFLEMAN", "MEDIC", "RIFLEMAN", "MEDIC", "RIFLEMAN"],
                          ["RIFLEMAN", "RIFLEMAN", "RIFLEMAN", "RIFLEMAN", "RIFLEMAN"]],
          "SUPPORT_39": [["ANTI-TANK_RIFLE", "MACHINE_GUNNER", "OFFICER", "MACHINE_GUNNER", "ANTI-TANK_RIFLE"],
                         ["RIFLEMAN", "MEDIC", "RIFLEMAN", "RIFLEMAN", "RIFLEMAN"], [""]],
          "RIFLEMEN_41": [
              ["SUB_MACHINE_GUNNER", "ANTI-TANK_RIFLE", "COMBAT_OFFICER", "LIGHT_MACHINE_GUNNER", "SUB_MACHINE_GUNNER"],
              ["RIFLEMAN", "RIFLEMAN", "RIFLEMAN", "RIFLEMAN", "RIFLEMAN"],
              ["RIFLEMAN", "RIFLEMAN", "RIFLEMAN", "RIFLEMAN", "RIFLEMAN"]],
          "SUPPORT_41": [
              ["ANTI-TANK_RIFLE", "LIGHT_MACHINE_GUNNER", "COMBAT_OFFICER", "LIGHT_MACHINE_GUNNER", "ANTI-TANK_RIFLE"],
              ["MARKSMAN", "MEDIC", "MARKSMAN", "MARKSMAN", "MARKSMAN"], [""]],
          "PARATROOPERS": [
              ["SHOCK_TROOPER", "LIGHT_MACHINE_GUNNER", "COMBAT_OFFICER", "LIGHT_ANTI-TANK_RIFLE", "SHOCK_TROOPER"],
              ["SHOCK_TROOPER", "SHOCK_TROOPER", "MEDIC", "SHOCK_TROOPER", "SHOCK_TROOPER"], [""]],
          "COMBAT_SQUAD_43": [
              ["SEMI-AUTO_RIFLE", "ANTI-TANK_RIFLE", "COMBAT_OFFICER", "LIGHT_MACHINE_GUNNER", "SEMI-AUTO_RIFLE"],
              ["SEMI-AUTO_RIFLE", "MEDIC", "SEMI-AUTO_RIFLE", "SEMI-AUTO_RIFLE", "SEMI-AUTO_RIFLE"],
              ["SEMI-AUTO_RIFLE", "RIFLEMAN", "SEMI-AUTO_RIFLE", "RIFLEMAN", "SEMI-AUTO_RIFLE"]],
          "ASSAULT_SQUAD_43": [["SUB_MACHINE_GUNNER", "COMBAT_OFFICER", "MEDIC", "SUB_MACHINE_GUNNER"],
                               ["SUB_MACHINE_GUNNER", "SUB_MACHINE_GUNNER", "SUB_MACHINE_GUNNER", "SUB_MACHINE_GUNNER"],
                               ["SUB_MACHINE_GUNNER", "SUB_MACHINE_GUNNER", "SUB_MACHINE_GUNNER",
                                "SUB_MACHINE_GUNNER"]],
          "CHECKPOINT GUARDS": [["SUB_MACHINE_GUNNER", "COMBAT_OFFICER", "SUB_MACHINE_GUNNER"], [""], [""]]}


def soldiers():
    all_soldiers = {"COMMANDER": ["OFFICER", 3, 3, 8, 5, 0, "PISTOL", "COMMANDER"],
                    "OBSERVER": ["OFFICER", 5, 4, 8, 5, 0, "PISTOL", "OBSERVER"],
                    "OFFICER": ["OFFICER", 5, 6, 8, 5, 0, "PISTOL", "OFFICER"],
                    "ENGINEER": ["ENGINEER", 4, 3, 9, 4, 0, "PISTOL", ""],
                    "GUN CREW": ["ENGINEER", 4, 4, 9, 4, 0, "PISTOL", ""],
                    "MEDIC": ["ENGINEER", 5, 4, 9, 4, 0, "PISTOL", ""],
                    "SAPPER": ["ENGINEER", 5, 4, 9, 4, 1, "PISTOL", "SATCHEL_CHARGE"],
                    "MACHINE_GUNNER": ["MG", 3, 6, 16, 4, 0, "MG", "RAPID_FIRE"],
                    "LIGHT_MACHINE_GUNNER": ["MG", 4, 6, 12, 5, 0, "LIGHT_MG", "RAPID_FIRE"],
                    "ANTI-TANK_RIFLE": ["ANTI_TANK", 5, 6, 18, 3, 0, "HEAVY_RIFLE", "ANTI_TANK"],
                    "HEAVY_ANTI-TANK_RIFLE": ["ANTI_TANK", 3, 6, 25, 3, 0, "ANTI_TANK", "ANTI_TANK"],
                    "LIGHT_ANTI-TANK_RIFLE": ["RIFLE", 4, 6, 12, 3, 0, "HEAVY_RIFLE", "ANTI_TANK"],
                    "RIFLEMAN": ["RIFLE", 5, 5, 15, 3, 2, "RIFLE", ""],
                    "GRENADIER": ["RIFLE", 4, 5, 15, 3, 3, "RIFLE", "RIFLE_GRENADE"],
                    "SEMI-AUTO_RIFLE": ["RIFLE", 5, 5, 12, 4, 2, "PISTOL", ""],
                    "MARKSMAN": ["RIFLE", 4, 4, 15, 3, 0, "HEAVY_RIFLE", ""],
                    "SUB_MACHINE_GUNNER": ["SMG", 5, 5, 8, 4, 3, "SMG", "RAPID_FIRE"],
                    "SHOCK_TROOPER": ["SMG", 6, 6, 9, 4, 3, "SMG", "RAPID_FIRE"],
                    "COMBAT_OFFICER": ["SMG", 6, 6, 9, 5, 1, "PISTOL", "OFFICER"]}

    label_keys = ["mesh_name", "speed", "toughness", "power", "ROF", "grenades", "sound", "special"]

    soldier_dict = {}

    for soldier_key in all_soldiers:
        soldier_entry = all_soldiers[soldier_key]
        new_entry = {}

        for i in range(len(label_keys)):
            new_entry[label_keys[i]] = soldier_entry[i]

        soldier_dict[soldier_key] = new_entry

    return soldier_dict
