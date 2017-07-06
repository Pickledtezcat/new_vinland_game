import bge


def get_vehicle_parts():
    vehicle_items = {"1": ["bolted plates", "ARMOR", 0, 2, 2, 2, 1, "RIVETED",
                           "Primitive bolt on plates of untreated steel. The first armored vehicles used it."],
                     "2": ["riveted plates", "ARMOR", 1, 2, 2, 1, 2, "RIVETED",
                           "Cheap and easy to manufacture. Rivets can cause damage inside tank even if not penetrated."],
                     "3": ["extra plates", "ARMOR", 2, 6, 2, 1, 1, "EXTRA_PLATES",
                           "Extra armor plates in vital areas such as the belly, engine deck and sides to protect the crew."],
                     "4": ["spaced armor", "ARMOR", 3, 6, 2, 1, 1, "SPACED_ARMOR",
                           "Adds extra critical protection against small caliber, high velocity weapons."],
                     "5": ["cast armor", "ARMOR", 2, 6, 2, 2, 6, "CAST",
                           "Fairly cheap and easy to make, can have flaws. Not easy to make thin sections."],
                     "6": ["gun mantlet", "ARMOR", 2, 6, 1, 1, 0, "MANTLET",
                           "A thick shield that protects the area where the gun meets the turret or body."],
                     "7": ["rolled steel armor", "ARMOR", 3, 6, 2, 1, 3, "PLATE",
                           "Welded construction. Good protection, but hard to make thick sections."],
                     "8": ["anti-mine coating", "ARMOR", 4, 6, 1, 1, 0, "ANTI-MINE",
                           "Infantry thrown magnetic mines less likely to stick."],
                     "9": ["composite armor", "ARMOR", 5, 6, 2, 1, 2, "COMPOSITE",
                           "An experimental sandwich of steel and glass. Protects well against shaped charge attacks."],
                     "10": ["automobile engine", "ENGINE", 0, 6, 1, 1, 1, "RELIABLE",
                            "A cheap and efficient car engine."],
                     "11": ["truck engine", "ENGINE", 1, 4, 2, 1, 2, "", "A larger, more powerful automobile engine."],
                     "12": ["industrial engine", "ENGINE", 2, 4, 6, 1, 7, "RELIABLE",
                            "An inefficient engine from industrial machinery. Good torque but bad power to weight ratio."],
                     "13": ["performance engine", "ENGINE", 2, 4, 4, 1, 6, "UNRELIABLE",
                            "A high performance engine, designed for power and speed. Needs a lot of maintenance. "],
                     "14": ["radial engine", "ENGINE", 3, 5, 3, 1, 5, "",
                            "A powerful and compact radial engine from a small aircraft."],
                     "15": ["large radial engine", "ENGINE", 4, 6, 4, 1, 9, "",
                            "A larger aircraft engine, very good power to weight ratio."],
                     "16": ["aircraft engine", "ENGINE", 3, 6, 3, 2, 12, "UNRELIABLE",
                            "A powerful aircraft engine, redesigned for vehicles. Somewhat fragile and high maintenance."],
                     "17": ["marine engine", "ENGINE", 4, 6, 6, 2, 20, "RELIABLE",
                            "A huge marine engine for the largest of vehicles."],
                     "18": ["turbo engine", "ENGINE", 4, 6, 1, 1, 2, "UNRELIABLE",
                            "A small automobile with a turbocharger. Increases power without increasing weight."],
                     "19": ["compact engine", "ENGINE", 5, 6, 5, 1, 13, "",
                            "A purpose built tank engine, uses advanced materials to reduce bulk and weight."],
                     "20": ["turboshaft engine", "ENGINE", 5, 6, 6, 1, 20, "PROTOTYPE",
                            "An experimental gas turbine engine. Amazing power to weight ratio, but very unreliable."],
                     "21": ["fuel storage", "ENGINE", 1, 6, 1, 1, 0, "EXTRA_FUEL",
                            "Extra fuel storage, sometimes mounted on the outside in removable tanks. Extends range and reliability."],
                     "22": ["improved transmission", "DRIVE", 3, 6, 2, 1, 0, "TRANSMISSION",
                            "A heavy duty transmission greatly improves reliability. "],
                     "23": ["improved engine filters", "ENGINE", 2, 6, 1, 1, 0, "FILTERS",
                            "Increases reliability by protecting the engine from dust and other particles."],
                     "24": ["improved cooling", "ENGINE", 1, 6, 2, 1, 0, "COOLING",
                            "Increases reliability especially in hot climates. Extra bulk is a drawback."],
                     "25": ["wide tracks/wheels", "DRIVE", 2, 6, 1, 1, 0, "WIDE_TRACKS",
                            "Gives better traction on soft ground. Reduces the chance of getting bogged down."],
                     "26": ["unitized components", "ENGINE", 5, 6, 2, 1, 0, "EXTRA_RELIABILITY",
                            "All drive components can be quickly removed and replaced. Easy to service, much more reliable."],
                     "27": ["engine block heater", "ENGINE", 4, 6, 1, 1, 0, "HEATER",
                            "Combined with specialty engine oil, helps avoid reliability problems in cold climates."],
                     "28": ["all wheel drive", "DRIVE", 2, 6, 2, 1, 0, "ALL_WHEEL",
                            "On wheeled vehicles increases traction and helps avoid bogging down."],
                     "29": ["leaf spring", "DRIVE", 1, 3, 2, 1, 8, "LEAF_SPRING",
                            "A simple and cheap method of suspension."],
                     "30": ["coil spring", "DRIVE", 1, 3, 1, 1, 5, "COIL_SPRING",
                            "Compact suspension with good off road handling but poor stability."],
                     "31": ["conical spring", "DRIVE", 3, 6, 3, 1, 12, "COIL_SPRING",
                            "A great improvement over coil spring suspension, the cone shape allows more compression."],
                     "32": ["bell crank", "DRIVE", 2, 6, 3, 1, 12, "BELL_CRANK",
                            "Great off road handling, a little unstable. Being inside the hull makes it difficult to maintain."],
                     "33": ["torsion bar", "DRIVE", 2, 4, 4, 1, 16, "TORSION_BAR",
                            "Good handling, very stable, not very compact. Expensive and difficult to replace if damaged."],
                     "34": ["twin torsion bar", "DRIVE", 4, 6, 2, 2, 20, "TORSION_BAR",
                            "Doubling the number of bars reduces bulk. Still expensive and hard to maintain."],
                     "35": ["disc spring", "DRIVE", 3, 6, 2, 1, 12, "LEAF_SPRING",
                            "Very cheap and simple. Extremely compact. Performance similar to leaf spring."],
                     "36": ["hydraulic system", "DRIVE", 5, 6, 3, 2, 24, "HYDRAULIC",
                            "A very expensive and complex system, but gives unrivaled performance."],
                     "37": ["bulkhead", "UTILITY", 1, 6, 3, 1, 0, "BULKHEAD",
                            "An armored bulkhead stops internal damage and fires from spreading through the vehicle."],
                     "38": ["extra escape hatches", "UTILITY", 1, 6, 1, 1, 0, "ESCAPE_HATCH",
                            "Extra escape hatches on the floor, sides and rear of turret increase crew survivability."],
                     "39": ["storage space", "UTILITY", 0, 6, 2, 1, 2, "STORAGE",
                            "Can be used to store supplies of to carry extra passengers or troops."],
                     "40": ["extra ammo", "UTILITY", 1, 6, 1, 1, 1, "AMMO",
                            "Increases the number of shots available. Makes special ammo types like smoke, available."],
                     "41": ["safety improvements", "UTILITY", 3, 6, 2, 1, 0, "EXTRA_SAFTEY",
                            "Improvements to engine, fuel lines, ammo storage and other areas increase survivability."],
                     "42": ["analog computer", "UTILITY", 4, 6, 2, 1, 0, "FIRE_CONTROL",
                            "A device for improving the accuracy of artillery or anti-aircraft guns."],
                     "43": ["improved turret control", "UTILITY", 2, 6, 2, 1, 0, "TURRET",
                            "A powerful motor helps traverse large turrets more quickly and smoothly."],
                     "44": ["infra-red equipment", "UTILITY", 5, 6, 2, 1, 0, "NIGHT_VISION",
                            "An infra-red spotlight and gun sights help to spot targets at night or in poor visibility."],
                     "45": ["gyroscopic stabilizer", "UTILITY", 4, 6, 1, 1, 0, "STABILIZER",
                            "Increases stability, improving aim and gun laying time."],
                     "46": ["medical aid station", "UTILITY", 1, 6, 3, 2, 0, "MEDICS",
                            "Medics and medical equipment help to treat nearby troops and crews if injured."],
                     "47": ["radio station", "CREW", 2, 4, 3, 1, 0, "RADIO",
                            "Gives a vehicle improved tactical flexibility."],
                     "48": ["improved radio station", "CREW", 4, 6, 2, 1, 0, "RADIO",
                            "Improvements in technology and vehicle design help this crew station to take up less space."],
                     "49": ["divisional radio", "CREW", 4, 6, 3, 2, 0, "DIVISIONAL_RADIO",
                            "A large radio and antenna give divisional radio support. "],
                     "50": ["gunner's station", "CREW", 0, 2, 2, 1, 2, "GUNNER",
                            "More gun crew mean more manpower to help with reloading and other tasks."],
                     "51": ["improved gunner's station", "CREW", 2, 5, 2, 1, 3, "GUNNER",
                            "Single stage ammunition and design improvements increase reloading speed."],
                     "52": ["advanced gunner's station", "CREW", 5, 6, 2, 1, 4, "ADVANCED_GUNNER",
                            "Improvements include advanced rangefinder, semi-automatic loading equipment and intercom."],
                     "53": ["commander's station", "CREW", 1, 3, 2, 1, 1, "COMMANDER",
                            "A commander gives better viewing range and improved fire control."],
                     "54": ["improved commander's station", "CREW", 3, 5, 2, 1, 2, "IMPROVED_COMMANDER",
                            "An armored cupola with advanced periscopes protects the commander from enemy fire."],
                     "55": ["advanced commander's station", "CREW", 5, 6, 2, 1, 2, "ADVANCED_COMMANDER",
                            "As well as a cupola for observation, a miniature radio set removes the need for a radio operator."],
                     "56": ["driver's station", "CREW", 0, 1, 3, 1, 1, "DRIVER",
                            "A primitive driving station with poor reliability and bulky equipment."],
                     "57": ["improved driver's station", "CREW", 1, 6, 2, 1, 1, "DRIVER",
                            "A compact driving station with better reliability, handling and ease of use."],
                     "58": ["mechanic", "CREW", 1, 6, 2, 1, 0, "MECHANIC",
                            "A dedicated mechanic can help to improve vehicle reliability and range."],
                     "59": ["machine gun", "WEAPON", 0, 2, 1, 1, 1, "QUICK",
                            "A bulky and slow firing machine gun from the last war."],
                     "60": ["improved machine gun", "WEAPON", 2, 6, 1, 1, 1, "RAPID",
                            "A simpler and faster firing machine gun."],
                     "61": ["heavy machine gun", "WEAPON", 3, 6, 1, 1, 2, "",
                            "A heavy duty machine gun good against infantry and light vehicles."],
                     "62": ["auto cannon", "WEAPON", 1, 4, 2, 1, 2, "QUICK",
                            "A up scaled machine gun that fires larger caliber shells. Increased bulk is a disadvantage."],
                     "63": ["improved auto cannon", "WEAPON", 4, 6, 2, 1, 2, "RAPID",
                            "An improved automatic firing cannon, great for use as an anti-aircraft weapon."],
                     "64": ["heavy auto cannon", "WEAPON", 4, 6, 2, 2, 4, "QUICK",
                            "A quick firing large caliber auto cannon, great against light vehicles."],
                     "65": ["small gun", "WEAPON", 0, 2, 2, 1, 2, "IMPROVED_GUN",
                            "A small caliber gun, the equivalent of an infantry carried anti tank rifle."],
                     "66": ["improved small gun", "WEAPON", 2, 6, 2, 1, 2, "ADVANCED_GUN",
                            "Improved penetration and accuracy make this weapon effective against light vehicles."],
                     "67": ["light gun", "WEAPON", 0, 2, 3, 1, 3, "PRIMITIVE_GUN",
                            "A small caliber anti tank gun, slow firing and poor penetration values for its size."],
                     "68": ["improved light gun", "WEAPON", 2, 6, 2, 1, 4, "IMPROVED_GUN",
                            "Improvements include reduced weight, better penetration, accuracy and firing speed."],
                     "69": ["medium gun", "WEAPON", 1, 3, 2, 2, 5, "",
                            "A medium anti tank gun, often converted from naval use."],
                     "70": ["improved medium gun", "WEAPON", 2, 4, 3, 2, 6, "IMPROVED_GUN",
                            "Reduced bulk, better penetration, accuracy and firing speed make for an improved gun."],
                     "71": ["advanced medium gun", "WEAPON", 3, 6, 2, 2, 6, "ADVANCED_GUN",
                            "Excellent penetration values, improved sights and reduced bulk make this a great anti tank gun."],
                     "72": ["heavy gun", "WEAPON", 2, 4, 4, 2, 7, "PRIMITIVE_GUN",
                            "A large caliber gives good armor penetration as well as allowing a large high explosive charge."],
                     "73": ["improved heavy gun", "WEAPON", 4, 5, 6, 2, 8, "IMPROVED_GUN",
                            "A longer barrel, better sights and other improvements make for a brilliant tank gun."],
                     "74": ["advanced heavy gun", "WEAPON", 5, 6, 6, 2, 9, "ADVANCED_GUN",
                            "Almost perfect performance as a tank gun, but needs a large turret ring to be mounted."],
                     "75": ["all purpose gun", "WEAPON", 3, 6, 5, 2, 9, "",
                            "A large caliber gun which can work as anti-tank or short range support."],
                     "76": ["support gun", "WEAPON", 1, 3, 3, 2, 7, "SUPPORT_GUN",
                            "A short barrel makes this gun very portable. Good for short range artillery support."],
                     "77": ["improved support gun", "WEAPON", 3, 6, 2, 2, 8, "SUPPORT_GUN",
                            "Larger caliber and less bulk due to design improvements make this gun good for artillery support."],
                     "78": ["heavy support gun", "WEAPON", 2, 6, 3, 3, 10, "SUPPORT_GUN",
                            "A very large caliber allows this gun to provide powerful short ranged fire support."],
                     "79": ["heavy artillery", "WEAPON", 2, 4, 8, 2, 12, "ARTILLERY",
                            "A simple conversion of a field howitzer. Provides mobile fire support."],
                     "80": ["improved artillery", "WEAPON", 4, 6, 6, 3, 15, "ARTILLERY",
                            "Design improvements allow a larger caliber with very little extra weight."],
                     "81": ["super heavy gun", "WEAPON", 4, 6, 8, 2, 12, "",
                            "A very large caliber gun designed for direct fire. Penetration values are poor for its size."],
                     "82": ["mortar", "WEAPON", 0, 6, 2, 1, 8, "MORTAR",
                            "A light weight fire support weapon. Breech loading is slow and difficult."],
                     "83": ["heavy mortar", "WEAPON", 2, 6, 4, 1, 15, "MORTAR",
                            "A huge but light weight fire support weapon. Breech loading is slow and difficult."],
                     "84": ["flame thrower", "WEAPON", 3, 6, 3, 2, 1, "FLAME_THROWER",
                            "A deadly weapon, but very short ranged."],
                     "85": ["small rockets", "WEAPON", 3, 6, 2, 1, 6, "ROCKETS",
                            "Rockets can deliver an intense barrage in a short space of time. Has a long reload time."],
                     "86": ["large rockets", "WEAPON", 4, 6, 4, 1, 15, "ROCKETS",
                            "Larger rockets have less range but more damage potential."]}

    labels = ["name",
              "part_type",
              "level",
              "obsolete",
              "y_size",
              "x_size",
              "rating",
              "flag",
              "description"]

    new_part_dictionary = {}

    for part_key in vehicle_items:
        part = vehicle_items[part_key]

        new_part_dict = {}

        for e in range(len(part)):
            entry = part[e]
            label = labels[e]
            new_part_dict[label] = entry

        new_part_dictionary[part_key] = new_part_dict

    return new_part_dictionary


def get_design_rules():
    design_rules = {"1": ["gun carriage", "GUN_CARRIAGE", 0, "LAYOUT", "This vehicle is actually a gun carriage."],
                    "2": ["primitive drive parts", "PRIMITIVE_DRIVE_PARTS", 0, "",
                          "This vehicle has primitive and unreliable drive."],
                    "3": ["unreliable parts", "UNRELIABLE_PARTS", 0, "",
                          "This vehicle is unreliable because of its poorly manufactured parts."],
                    "4": ["dangerous design", "DANGEROUS_DESIGN", 0, "",
                          "This vehicle is dangerous because of its bad design."],
                    "5": ["wheeled drive", "WHEELED", 0, "DRIVE", "The vehicle has road wheels."],
                    "6": ["open top", "OPEN_TOP", 0, "LAYOUT",
                          "The vehicle has an open top or turret, can be damaged by grenades or artillery."],
                    "7": ["long chassis", "LONG_CHASSIS", 1, "LAYOUT",
                          "The vehicle has a long wheelbase. This gives more room but reduces handling."],
                    "8": ["poor visibility", "POOR_VISIBILITY", 1, "",
                          "The vehicle has bad visibility for the driver and crew."],
                    "9": ["cramped", "CRAMPED", 1, "",
                          "The vehicle has a cramped crew compartment or turret. Rate of fire is reduced."],
                    "10": ["weak spot", "WEAK_SPOT", 0, "",
                           "The vehicle has a bad weak spot. Perhaps a vision slit, hatch or gun mounting."],
                    "11": ["gun sponson", "GUN_SPONSON", 1, "",
                           "This vehicle has a sponson on the body which allows better aiming and accuracy."],
                    "12": ["tracked drive", "TRACKED", 0, "DRIVE",
                           "This vehicle has a tracked trive, which classifies it as a tank."],
                    "13": ["halftrack drive", "HALFTRACK", 1, "DRIVE",
                           "This vehicle has a half track drive, good both on and off road. "],
                    "14": ["super- structure", "SUPER-_STRUCTURE", 0, "LAYOUT",
                           "This vehicle has an enlarged super structure with more room for parts and crew."],
                    "15": ["anti aircraft mount", "ANTI_AIRCRAFT", 1, "TURRET",
                           "This vehicle can be used in an anti-aircraft role."],
                    "16": ["amphibious adaptation", "AMPHIBIOUS", 2, "", "This vehicle can cross rivers and swamps."],
                    "17": ["sloped arrangement", "SLOPED_ARMOR", 3, "",
                           "This vehicle has sloped armor. Much better protection vs nomal anti-tank rounds."],
                    "18": ["compact armor arrangement", "COMPACT_ARMOR", 5, "",
                           "The armor is laid out more effectively, giving more internal space."],
                    "19": ["rocket mount", "ROCKET_MOUNT", 3, "TURRET",
                           "This vehicle has a rocket mount instead of a turret. Needed to mount rockets."]}

    labels = ["name",
              "flag",
              "level",
              "option_type",
              "description"]

    new_rule_dictionary = {}

    for rule_key in design_rules:
        rule = design_rules[rule_key]

        new_rule = {}

        for e in range(len(rule)):
            entry = rule[e]
            label = labels[e]
            new_rule[label] = entry

        new_rule_dictionary[rule_key] = new_rule

    return new_rule_dictionary


color_dict = {"engine": [0.0, 1.0, 0.2, 1.0],
              "drive": [0.0, 0.1, 1.0, 1.0],
              "utility": [0.1, 0.8, 0.8, 1.0],
              "armor": [0.9, 1.0, 0.0, 1.0],
              "weapon": [1.0, 0.1, 0.0, 1.0],
              "crew": [1.0, 0.0, 0.6, 1.0],
              "empty": [0.8, 0.8, 0.8, 1.0],
              "design": [0.5, 0.5, 0.5, 1.0],
              "cancel": [1.0, 0.0, 0.0, 1.0]}

chassis_dict = {1: {"x": 2, "y": 5, "name": "mini_chassis", "front": 1, "armor_scale": 1.6},
                2: {"x": 4, "y": 6, "name": "small_chassis", "front": 2, "armor_scale": 1.4},
                3: {"x": 6, "y": 8, "name": "medium_chassis", "front": 3, "armor_scale": 1.2},
                4: {"x": 8, "y": 10, "name": "large_chassis", "front": 4, "armor_scale": 1.0}}

turret_dict = {0: {"x": 0, "y": 0, "name": "no_turret", "block_x": 0, "block_y": 0, "armor_scale": 0},
               1: {"x": 2, "y": 2, "name": "mini_turret", "block_x": 2, "block_y": 1, "armor_scale": 1.6},
               2: {"x": 2, "y": 4, "name": "small_turret", "block_x": 2, "block_y": 2, "armor_scale": 1.4},
               3: {"x": 4, "y": 4, "name": "medium_turret", "block_x": 4, "block_y": 2, "armor_scale": 1.2},
               4: {"x": 4, "y": 7, "name": "large_turret", "block_x": 4, "block_y": 4, "armor_scale": 1.0},
               5: {"x": 6, "y": 8, "name": "huge_turret", "block_x": 6, "block_y": 4, "armor_scale": 0.8}}

drive_dict = {'WHEELED': {'on_road': 1.3, 'off_road': 0.5, 'stability': 0, 'handling': [5, 1]},
              'HALFTRACK': {'on_road': 1.15, 'off_road': 0.8, 'stability': 1, 'handling': [4, 2]},
              'TRACKED': {'on_road': 1.0, 'off_road': 1.0, 'stability': 1, 'handling': [3, 3]}}

suspension_dict = {'LEAF_SPRING': {'on_road': 2.8, 'off_road': 1.9, 'stability': 2, 'handling': [2, 2]},
                   'COIL_SPRING': {'on_road': 2.0, 'off_road': 2.0, 'stability': 2, 'handling': [4, 4]},
                   'BELL_CRANK': {'on_road': 2.7, 'off_road': 2.0, 'stability': 1, 'handling': [3, 3]},
                   'TORSION_BAR': {'on_road': 3.0, 'off_road': 2.2, 'stability': 3, 'handling': [3, 2]},
                   'HYDRAULIC': {'on_road': 3.0, 'off_road': 2.2, 'stability': 4, 'handling': [4, 4]},
                   'UNSPRUNG': {'on_road': 0.8, 'off_road': 0.56, 'stability': 0, 'handling': [0, 0]}}

cammo_dict = {"0": [0.3921568989753723, 0.8313725590705872, 0.2666667103767395, 1.0],
              "1": [0.6666666865348816, 0.729411780834198, 0.32156866788864136, 1.0],
              "2": [0.47058820724487305, 0.501960813999176, 0.47058820724487305, 1.0],
              "3": [0.5960784554481506, 0.8627452850341797, 0.9098039269447327, 1.0],
              "4": [0.729411780834198, 0.572549045085907, 0.41568630933761597, 1.0],
              "5": [0.5176470875740051, 0.21960783004760742, 0.18823528289794922, 1.0],
              "6": [1.0, 0.8749999403953552, 0.6406248807907104, 1.0],
              "7": [1.0, 0.5857142210006714, 0.5428570508956909, 1.0],
              "8": [1.0, 0.9119496941566467, 0.45911943912506104, 1.0],
              "9": [0.3215685784816742, 0.729411780834198, 0.14901959896087646, 1.0],
              "10": [0.40784314274787903, 0.42352941632270813, 0.3607843220233917, 1.0],
              "11": [0.9631901979446411, 1.0, 0.9386503100395203, 1.0], "12": [0.9890109896659851, 1.0, 1.0, 1.0],
              "13": [0.9589040875434875, 1.0, 0.9452055096626282, 1.0],
              "14": [0.501960813999176, 0.6745098829269409, 0.7058823704719543, 1.0],
              "15": [0.10196077823638916, 0.11764708161354065, 0.13333334028720856, 1.0]}

tech_levels = {1: {"aircraft": [0, 0.088],
                   "artillery": [0, 0.144],
                   "design": [2, 0.04],
                   "infantry": [2, 0.04],
                   "espionage": [1, 0.08],
                   "engine": [0, 0.144],
                   "suspension": [0, 0.12],
                   "crew": [1, 0.088],
                   "utility": [0, 0.152],
                   "weapon": [0, 0.104],
                   "armor": [1, 0.12]},
               2: {"aircraft": [0, 0.144],
                   "artillery": [1, 0.112],
                   "design": [2, 0.06],
                   "infantry": [1, 0.08],
                   "espionage": [1, 0.08],
                   "engine": [0, 0.104],
                   "suspension": [0, 0.144],
                   "crew": [1, 0.104],
                   "utility": [0, 0.12],
                   "weapon": [0, 0.104],
                   "armor": [0, 0.088]},
               3: {"aircraft": [1, 0.12],
                   "artillery": [2, 0.0448],
                   "design": [3, 0.02],
                   "infantry": [2, 0.08],
                   "espionage": [1, 0.08],
                   "engine": [2, 0.04],
                   "suspension": [2, 0.04],
                   "crew": [2, 0.04],
                   "utility": [2, 0.064],
                   "weapon": [1, 0.12],
                   "armor": [1, 0.088]},
               4: {"aircraft": [2, 0.064],
                   "artillery": [1, 0.096],
                   "design": [2, 0.064],
                   "infantry": [2, 0.096],
                   "espionage": [2, 0.064],
                   "engine": [1, 0.088],
                   "suspension": [0, 0.12],
                   "crew": [0, 0.152],
                   "utility": [0, 0.12],
                   "weapon": [1, 0.088],
                   "armor": [1, 0.096]},
               5: {"aircraft": [1, 0.12],
                   "artillery": [1, 0.08],
                   "design": [3, 0.024],
                   "infantry": [1, 0.12],
                   "espionage": [2, 0.04],
                   "engine": [1, 0.08],
                   "suspension": [1, 0.08],
                   "crew": [3, 0.068],
                   "utility": [3, 0.016],
                   "weapon": [2, 0.0464],
                   "armor": [1, 0.12]},
               6: {"aircraft": [0, 0.096],
                   "artillery": [0, 0.08],
                   "design": [0, 0.096],
                   "infantry": [0, 0.104],
                   "espionage": [0, 0.072],
                   "engine": [0, 0.064],
                   "suspension": [0, 0.08],
                   "crew": [0, 0.08],
                   "utility": [0, 0.112],
                   "weapon": [0, 0.108],
                   "armor": [0, 0.096]}}

faction_dict = {1: "VINLAND",
                2: "AMORICA",
                3: "HRE",
                4: "JAPAN",
                5: "TURKS",
                6: "MINOR"}
