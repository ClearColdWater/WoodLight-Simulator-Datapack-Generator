import os
import shutil
import re
from nbt import nbt 

# ================= CONFIGURATION =================
# Path to NBT files
DESIGNS_PATH = r"designs"
# Datapack Name
DATAPACK_NAME = "woodlight_sim"
# Namespace
NAMESPACE = "woodlight"

# Grid Settings
GRID_X = 10
GRID_Y = 10
GRID_Z = 10
SPACING = 11 

# 1. [Transformation Rules]: 
#    Transform to {TRANSFORM_TARGET} after being burnt to air.
#    (If the block is paired, the pairing logic takes over; this list does not apply to paired blocks).
TRANSFORM_AFTER_BURN = [
    "minecraft:white_carpet"
]

# 2. [Self-Restore Rules]: 
#    If it becomes air, it restores itself to the original block.
RESTORE_SELF = [
    "minecraft:oak_planks",
    "minecraft:dark_oak_planks",
    "minecraft:jungle_planks",
    "minecraft:oak_leaves",
    "minecraft:acacia_planks",
    "minecraft:jungle_leaves"
]

# 3. [Fire Trigger - Up]: 
#    If the current position is fire, place {TRANSFORM_TARGET} [Above] it (if above is not fire).
FIRE_TRIGGER_UP = [
    "minecraft:dark_oak_planks"
]

# 4. [Fire Trigger - Down]: 
#    If the current position is fire, place {TRANSFORM_TARGET} [Below] it (if below is not fire).
FIRE_TRIGGER_DOWN = [
    "minecraft:jungle_planks"
]

# 5. [Immediate Restore]: 
#    If it becomes fire, it restores itself to the original block.
IMMEDIATE_RESTORE = [
    "minecraft:acacia_planks",
    "minecraft:jungle_leaves"
]

# 6. [Flood Protection]: 
#    If the above block is lava, remove it.
REMOVE_ABOVE_LAVA = [
    "minecraft:acacia_planks",
    "minecraft:jungle_leaves"
]

# Default block to transform to
TRANSFORM_TARGET = "minecraft:oak_leaves"

# 16 Colors List
COLORS = [
    "white", "orange", "magenta", "light_blue", "yellow", "lime",
    "pink", "gray", "light_gray", "cyan", "purple", "blue",
    "brown", "green", "red", "black"
]
# =================================================

def create_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding='utf-8') as f:
        f.write(content)

def clean_block_name(name):
    if not name.startswith("minecraft:"): return "minecraft:" + name
    return name

def sanitize_filename(name):
    s = re.sub(r'[^a-z0-9_]', '_', name.lower())
    return s[:50]

def get_block_regen_commands(nbt_path):
    try: nbt_file = nbt.NBTFile(nbt_path)
    except: return []
    
    commands = []
    palette = []
    
    # 1. Scan Data
    block_map = {} 
    wool_data = {c: {'wool': None, 'concrete': None} for c in COLORS}
    terra_data = {c: {'terra': None, 'glazed': None} for c in COLORS}

    if "palette" in nbt_file:
        for p in nbt_file["palette"]:
            name = p["Name"].value if hasattr(p["Name"], "value") else str(p["Name"])
            palette.append(clean_block_name(name))
            
    if "blocks" in nbt_file:
        for block in nbt_file["blocks"]:
            state_idx = block["state"].value
            if state_idx >= len(palette): continue
            name = palette[state_idx]
            pos = block["pos"]
            coord = (pos[0].value, pos[1].value, pos[2].value)
            
            block_map[coord] = name
            
            # Record Potential Pairs
            for c in COLORS:
                if name == f"minecraft:{c}_wool": wool_data[c]['wool'] = coord
                elif name == f"minecraft:{c}_concrete": wool_data[c]['concrete'] = coord
                elif name == f"minecraft:{c}_terracotta": terra_data[c]['terra'] = coord
                elif name == f"minecraft:{c}_glazed_terracotta": terra_data[c]['glazed'] = coord

    # 2. Identify and Lock Pairs (Paired Coords)
    paired_coords = set()

    # Wool/Concrete Pairs
    valid_wool_pairs = []
    for c, data in wool_data.items():
        if data['wool'] and data['concrete']:
            valid_wool_pairs.append((c, data['wool'], data['concrete']))
            paired_coords.add(data['wool'])
            paired_coords.add(data['concrete'])

    # Terracotta Pairs
    valid_terra_pairs = []
    for c, data in terra_data.items():
        if data['terra'] and data['glazed']:
            valid_terra_pairs.append((c, data['terra'], data['glazed']))
            paired_coords.add(data['terra'])
            paired_coords.add(data['glazed'])

    # 3. Generate commands for all blocks
    for coord, name in block_map.items():
        x, y, z = coord

        # Rule: Air -> Transform
        if name in TRANSFORM_AFTER_BURN:
            commands.append(f"execute if block ~{x} ~{y-1} ~{z} minecraft:air run setblock ~{x} ~{y-1} ~{z} {TRANSFORM_TARGET}")
            
        # Rule: Self-Restore
        elif name in RESTORE_SELF:
            # Rule: Fire -> Immediate Restore
            if name in IMMEDIATE_RESTORE:
                commands.append(f"execute if block ~{x} ~{y-1} ~{z} minecraft:fire run setblock ~{x} ~{y-1} ~{z} {name}")
            commands.append(f"execute if block ~{x} ~{y-1} ~{z} minecraft:air run setblock ~{x} ~{y-1} ~{z} {name}")
        
        # Trigger: Fire -> Generate Above
        if name in FIRE_TRIGGER_UP:
            commands.append(f"execute if block ~{x} ~{y-1} ~{z} minecraft:fire unless block ~{x} ~{y} ~{z} minecraft:fire run setblock ~{x} ~{y} ~{z} {TRANSFORM_TARGET}")

        # Trigger: Fire -> Generate Below
        if name in FIRE_TRIGGER_DOWN:
            commands.append(f"execute if block ~{x} ~{y-1} ~{z} minecraft:fire unless block ~{x} ~{y-2} ~{z} minecraft:fire run setblock ~{x} ~{y-2} ~{z} {TRANSFORM_TARGET}")
        
        # Trigger: Lava Above -> Remove
        if name in REMOVE_ABOVE_LAVA:
            commands.append(f"execute if block ~{x} ~{y} ~{z} minecraft:lava run setblock ~{x} ~{y} ~{z} minecraft:air")


    # 4. Generate Pairing Logic (Independent of standard rules)
    
    # Wool & Concrete (Standard Logic)
    for color, pw, pc in valid_wool_pairs:
        xw, yw, zw = pw
        xc, yc, zc = pc
        yw -= 1; yc -= 1
        
        commands.append(f"execute if block ~{xw} ~{yw} ~{zw} minecraft:{color}_wool run setblock ~{xw} ~{yw} ~{zw} {TRANSFORM_TARGET}")
        commands.append(f"execute if block ~{xc} ~{yc} ~{zc} minecraft:{color}_concrete run setblock ~{xc} ~{yc} ~{zc} minecraft:air")
        commands.append(f"execute if block ~{xw} ~{yw} ~{zw} minecraft:air if block ~{xc} ~{yc} ~{zc} minecraft:air run setblock ~{xw} ~{yw} ~{zw} {TRANSFORM_TARGET}")
        commands.append(f"execute if block ~{xw} ~{yw} ~{zw} minecraft:air if block ~{xc} ~{yc} ~{zc} minecraft:fire run setblock ~{xw} ~{yw} ~{zw} {TRANSFORM_TARGET}")
        commands.append(f"execute if block ~{xw} ~{yw} ~{zw} minecraft:fire if block ~{xc} ~{yc} ~{zc} minecraft:air run setblock ~{xc} ~{yc} ~{zc} {TRANSFORM_TARGET}")
        commands.append(f"execute if block ~{xw} ~{yw} ~{zw} minecraft:fire if block ~{xc} ~{yc} ~{zc} minecraft:fire run setblock ~{xw} ~{yw} ~{zw} {TRANSFORM_TARGET}")

    # Terracotta & Glazed Terracotta (Mutually Exclusive Logic)
    for color, pt, pg in valid_terra_pairs:
        xt, yt, zt = pt
        xg, yg, zg = pg
        yt -= 1; yg -= 1
        
        commands.append(f"execute if block ~{xt} ~{yt} ~{zt} minecraft:{color}_terracotta run setblock ~{xt} ~{yt} ~{zt} minecraft:air")
        commands.append(f"execute if block ~{xg} ~{yg} ~{zg} minecraft:{color}_glazed_terracotta run setblock ~{xg} ~{yg} ~{zg} minecraft:air")
        commands.append(f"execute if block ~{xt} ~{yt} ~{zt} minecraft:fire unless block ~{xg} ~{yg} ~{zg} minecraft:fire run setblock ~{xg} ~{yg} ~{zg} {TRANSFORM_TARGET}")
        commands.append(f"execute if block ~{xg} ~{yg} ~{zg} minecraft:fire unless block ~{xt} ~{yt} ~{zt} minecraft:fire run setblock ~{xt} ~{yt} ~{zt} {TRANSFORM_TARGET}")

    return commands

def main():
    if not os.path.exists(DESIGNS_PATH): 
        print(f"Error: Path not found {DESIGNS_PATH}")
        return
    if os.path.exists(DATAPACK_NAME): shutil.rmtree(DATAPACK_NAME)
    
    base_dir = f"{DATAPACK_NAME}/data/{NAMESPACE}/functions"
    struct_dir = f"{DATAPACK_NAME}/data/{NAMESPACE}/structures"
    os.makedirs(struct_dir, exist_ok=True)

    create_file(f"{DATAPACK_NAME}/pack.mcmeta", '{"pack":{"pack_format":5,"description":"WoodLight Local Timer Sim"}}')
    
    # --- Setup ---
    create_file(f"{base_dir}/setup.mcfunction", '''scoreboard objectives add f_global_timer dummy
scoreboard objectives add f_local_timer dummy
scoreboard objectives add f_success dummy
scoreboard objectives add f_cooldown dummy
scoreboard objectives add f_config dummy
gamerule maxCommandChainLength 2000000
difficulty hard
fill 8 127 8 8 1 8 minecraft:glass
tp @a 8.5 128 8.5
tellraw @a {"text":"[WoodLight Sim] Ready. Colors logic updated."}
''')

    # --- Stop ---
    create_file(f"{base_dir}/stop.mcfunction", '''scoreboard players set global f_config 1
tellraw @a {"text":"[WoodLight Sim] Stopping gracefully...","color":"gold"}
''')

    files = [f for f in os.listdir(DESIGNS_PATH) if f.endswith(".nbt")]

    for f in files:
        safe_name = sanitize_filename(f[:-4])
        shutil.copy(os.path.join(DESIGNS_PATH, f), os.path.join(struct_dir, f"{safe_name}.nbt"))
        
        # --- Load Structure ---
        struct_block_nbt = f'{{mode:"LOAD",name:"{NAMESPACE}:{safe_name}",posX:0,posY:0,posZ:0}}'
        load_cmds = [
            "fill ~ ~-1 ~ ~10 ~7 ~10 minecraft:air",
            f'setblock ~ ~-1 ~ minecraft:structure_block{struct_block_nbt}',
            'setblock ~ ~-2 ~ minecraft:redstone_block',
            'scoreboard players set @s f_cooldown 0',
            'scoreboard players set @s f_local_timer 0' 
        ]
        create_file(f"{base_dir}/load_{safe_name}.mcfunction", "\n".join(load_cmds))

        # --- Start ---
        start_cmds = [
            "kill @e[tag=f_marker]",
            "kill @e[type=item]",
            "scoreboard players set global f_global_timer 0",
            "scoreboard players set global f_config 0", 
            f'tellraw @a {{"text":"Starting simulation: {safe_name}"}}',
            f'data modify storage woodlight:ram current_design set value "{safe_name}"'
        ]
        
        for x in range(GRID_X):
            for y in range(GRID_Y):
                for z in range(GRID_Z):
                    px = (x - GRID_X // 2) * SPACING
                    py = (y - GRID_Y // 2) * SPACING
                    pz = (z - GRID_Z // 2) * SPACING
                    start_cmds.append(f'summon armor_stand ~{px} ~{py} ~{pz} {{Tags:["f_marker"],Invisible:1b,Marker:1b,NoGravity:1b}}')

        start_cmds.append(f"execute as @e[tag=f_marker] at @s run function {NAMESPACE}:load_{safe_name}")
        start_cmds.append(f"schedule function {NAMESPACE}:tick_{safe_name} 1t")
        
        create_file(f"{base_dir}/start_{safe_name}.mcfunction", "\n".join(start_cmds))

        # --- Regen (Calls the modified function) ---
        regen_cmds = get_block_regen_commands(os.path.join(DESIGNS_PATH, f))
        create_file(f"{base_dir}/regen_{safe_name}.mcfunction", "\n".join(regen_cmds))
        
        # --- Tick ---
        tick_cmds = f'''scoreboard players add global f_global_timer 1
execute as @e[tag=f_marker] if score @s f_cooldown matches 0 at @s if block ~ ~-2 ~ minecraft:redstone_block run setblock ~ ~-2 ~ minecraft:air
execute as @e[tag=f_marker] if score @s f_cooldown matches 0 at @s if block ~ ~-1 ~ minecraft:structure_block run setblock ~ ~-1 ~ minecraft:air
execute as @e[tag=f_marker] if score @s f_cooldown matches 1.. run scoreboard players remove @s f_cooldown 1
execute if score global f_config matches 1 as @e[tag=f_marker] if score @s f_cooldown matches 1 run kill @s
execute as @e[tag=f_marker] at @s if score @s f_cooldown matches 1 run function {NAMESPACE}:load_{safe_name}

# Simulation
execute as @e[tag=f_marker] if score @s f_cooldown matches 0 run scoreboard players add @s f_local_timer 1
execute as @e[tag=f_marker] if score @s f_cooldown matches 0 at @s run function {NAMESPACE}:regen_{safe_name}
execute as @e[tag=f_marker] if score @s f_cooldown matches 0 at @s run function {NAMESPACE}:check_instance

execute if entity @e[tag=f_marker] run schedule function {NAMESPACE}:tick_{safe_name} 1t
'''
        create_file(f"{base_dir}/tick_{safe_name}.mcfunction", tick_cmds)
        print(f"Generated: {safe_name}")

    # --- Helpers ---
    create_file(f"{base_dir}/check_instance.mcfunction", '''execute store result score @s f_success run fill ~ ~-1 ~ ~10 ~9 ~10 purple_concrete replace nether_portal
execute if score @s f_success matches 1.. run function woodlight:on_success
''')
    
    create_file(f"{base_dir}/on_success.mcfunction", '''tellraw @a ["LOG_DATA::", {"text":"{","color":"white"}, "\\"design\\":\\"", {"nbt":"current_design","storage":"woodlight:ram"}, "\\",\\"tick\\":", {"score":{"name":"@s","objective":"f_local_timer"}}, "}"]
fill ~ ~-1 ~ ~10 ~7 ~10 air
scoreboard players set @s f_cooldown 82
''')

    print("Done.")

if __name__ == "__main__":
    main()
