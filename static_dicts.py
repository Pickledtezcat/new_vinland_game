squads = {"COMMANDER": [["COMMANDER"], [""], [""]],
          "OBSERVERS": [["OBSERVER", "OBSERVER"], [""], [""]],
          "ENGINEERS": [["ENGINEER", "ENGINEER"], ["ENGINEER", "ENGINEER"], [""]],
          "GUN_CREW": [["GUN CREW", "GUN CREW", "GUN CREW"], [""], [""]],
          "HEAVY_SUPPORT_TEAM": [["MACHINE_GUNNER", "MACHINE_GUNNER", "MACHINE_GUNNER", "MACHINE_GUNNER"], [""], [""]],
          "ANTI-TANK_TEAM": [["ANTI-TANK_RIFLE", "ANTI-TANK_RIFLE"], ["ANTI-TANK_RIFLE", "ANTI-TANK_RIFLE"], [""]],
          "HEAVY_ANTI-TANK_TEAM": [["HEAVY_ANTI-TANK_RIFLE", "HEAVY_ANTI-TANK_RIFLE"], [""], [""]],
          "MARKSMEN": [["MARKSMAN", "MARKSMAN", "MARKSMAN"], [""], [""]],
          "SCOUT": [["MARKSMAN"], [""], [""]],
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
    all_soldiers = {"COMMANDER": ["OFFICER", 2, 2, 4, 0, 2, ""],
                    "OBSERVER": ["OFFICER", 3, 2, 5, 0, 2, ""],
                    "OFFICER": ["OFFICER", 3, 2, 4, 0, 2, ""],
                    "ENGINEER": ["ENGINEER", 2, 2, 3, 0, 3, ""],
                    "GUN CREW": ["ENGINEER", 3, 3, 3, 0, 3, ""],
                    "MEDIC": ["ENGINEER", 3, 2, 3, 0, 3, ""],
                    "MACHINE_GUNNER": ["MG", 2, 4, 3, 2, 3, "RAPID_FIRE"],
                    "LIGHT_MACHINE_GUNNER": ["MG", 3, 4, 3, 1, 4, "RAPID_FIRE"],
                    "ANTI-TANK_RIFLE": ["ANTI_TANK", 3, 4, 3, 2, 1, ""],
                    "HEAVY_ANTI-TANK_RIFLE": ["ANTI_TANK", 2, 4, 3, 3, 1, ""],
                    "LIGHT_ANTI-TANK_RIFLE": ["RIFLE", 3, 3, 3, 2, 1, ""],
                    "RIFLEMAN": ["RIFLE", 3, 3, 3, 1, 1, ""],
                    "SEMI-AUTO_RIFLE": ["RIFLE", 3, 3, 3, 1, 2, ""],
                    "MARKSMAN": ["RIFLE", 3, 3, 4, 1, 1, ""],
                    "SUB_MACHINE_GUNNER": ["SMG", 3, 4, 3, 0, 3, "RAPID_FIRE"],
                    "SHOCK_TROOPER": ["SMG", 4, 5, 3, 0, 3, "RAPID_FIRE"],
                    "COMBAT_OFFICER": ["SMG", 4, 4, 4, 0, 2, ""]}

    label_keys = ["mesh_name", "speed", "toughness", "base_view", "power", "ROF", "special"]

    soldier_dict = {}

    for soldier_key in all_soldiers:
        soldier_entry = all_soldiers[soldier_key]
        new_entry = {}

        for i in range(len(label_keys)):
            new_entry[label_keys[i]] = soldier_entry[i]

        soldier_dict[soldier_key] = new_entry

    return soldier_dict
