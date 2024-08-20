import discord
from discord import app_commands
import csv
import json
import random
import string
import os
from datetime import datetime, timedelta
from discord.ui import Button, View
import asyncio

class MyClient(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)
        self.admin_id = 아이디
        self.config_file = r'콘픽'
        self.users_csv = r'csv'
        
    async def setup_hook(self):
        await self.tree.sync()

client = MyClient()

def load_config():
    if os.path.exists(client.config_file):
        try:
            with open(client.config_file, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            print("JSON 파일이 잘못된 형식입니다. 기본값을 사용합니다.")
            return initialize_config()
    else:
        return initialize_config()

def initialize_config():
    config = {"admins": []}
    save_config(config)
    return config

def save_config(config):
    with open(client.config_file, 'w') as f:
        json.dump(config, f, indent=4)

def load_users():
    if os.path.exists(client.users_csv):
        users = {}
        with open(client.users_csv, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                users[int(row['user_id'])] = row
        return users
    return {}

def save_users(users):
    with open(client.users_csv, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['user_id', 'username', 'banned', 'license', 'plan', 'expiry_date'])
        writer.writeheader()
        for user_id, user_info in users.items():
            writer.writerow(user_info)

def is_admin(user_id):
    config = load_config()
    return user_id in config["admins"]

def is_banned(user_id):
    users = load_users()
    return users.get(user_id, {}).get('banned') == 'True'

def get_user_info(user_id):
    users = load_users()
    return users.get(user_id, {})

def add_user(user_id, username):
    users = load_users()
    if user_id not in users:
        users[user_id] = {
            'user_id': user_id,
            'username': username,
            'banned': 'False',
            'license': '',
            'plan': 'None',
            'expiry_date': ''
        }
        save_users(users)

def remove_user(user_id):
    users = load_users()
    if user_id in users:
        del users[user_id]
        save_users(users)

def generate_license():
    chars = ''.join(random.choices(string.ascii_uppercase + string.digits, k=16))
    return '-'.join([chars[i:i+4] for i in range(0, 16, 4)])

@client.event
async def on_ready():
    print(f'봇이 {client.user}로 로그인했습니다.')

async def register_function(interaction: discord.Interaction):
    user_id = interaction.user.id
    if is_banned(user_id):
        await interaction.response.send_message("당신은 차단되어 있어서 가입할 수 없습니다.", ephemeral=True)
        return

    if get_user_info(user_id):
        await interaction.response.send_message("이미 가입된 사용자입니다.", ephemeral=True)
        return

    add_user(user_id, interaction.user.name)
    await interaction.response.send_message("가입이 완료되었습니다. 이제 명령어를 사용할 수 있습니다.", ephemeral=True)

async def unregister_function(interaction: discord.Interaction):
    user_id = interaction.user.id
    if is_banned(user_id):
        await interaction.response.send_message("당신은 차단되어 있어서 탈퇴할 수 없습니다.", ephemeral=True)
        return

    if not get_user_info(user_id):
        await interaction.response.send_message("가입되지 않은 사용자입니다.", ephemeral=True)
        return

    remove_user(user_id)
    await interaction.response.send_message("탈퇴가 완료되었습니다. 모든 라이센스가 삭제되었습니다.", ephemeral=True)

async def my_info_function(interaction: discord.Interaction):
    user_id = interaction.user.id
    user_info = get_user_info(user_id)
    
    if not user_info:
        await interaction.response.send_message("등록된 정보가 없습니다. /가입 명령어를 사용하여 가입하십시오.", ephemeral=True)
        return
    
    banned_status = "차단됨" if user_info.get('banned') == 'True' else "차단되지 않음"
    license_info = user_info.get('license', '라이센스 없음')
    plan = user_info.get('plan', '없음')
    expiry_date = user_info.get('expiry_date', '없음')
    
    info_message = (
        f"**유저 아이디:** {user_id}\n"
        f"**유저 닉네임:** {interaction.user.name}\n"
        f"**차단 여부:** {banned_status}\n"
        f"**라이센스:** {license_info}\n"
        f"**플랜:** {plan}\n"
        f"**만료일:** {expiry_date}"
    )
    
    await interaction.response.send_message(info_message, ephemeral=True)

@client.tree.command(name="가입", description="봇 사용을 위한 가입을 합니다.")
async def register(interaction: discord.Interaction):
    await register_function(interaction)

@client.tree.command(name="탈퇴", description=탈퇴를 합니다. 모든 라이센스는 삭제되니 신중히 선택해주세요.")
async def unregister(interaction: discord.Interaction):
    await unregister_function(interaction)

@client.tree.command(name="내정보", description="자신의 정보를 확인합니다.")
async def my_info(interaction: discord.Interaction):
    await my_info_function(interaction)

@client.tree.command(name="총관리자", description="총관리자를 추가하거나 삭제합니다.")
@app_commands.describe(action="추가하거나 삭제할 작업", user="총관리자 상태로 만들거나 삭제할 사용자")
@app_commands.choices(action=[
    app_commands.Choice(name="추가", value="add"),
    app_commands.Choice(name="삭제", value="remove")
])
async def manage_admin(interaction: discord.Interaction, action: str, user: discord.User):
    if interaction.user.id == client.admin_id:
        config = load_config()
        if action == "add":
            if user.id not in config["admins"]:
                config["admins"].append(user.id)
                save_config(config)
                await interaction.response.send_message(f"{user.name}을 총관리자로 추가했습니다.")
            else:
                await interaction.response.send_message(f"{user.name}은 이미 총관리자입니다.")
        elif action == "remove":
            if user.id in config["admins"]:
                config["admins"].remove(user.id)
                save_config(config)
                await interaction.response.send_message(f"{user.name}을 총관리자에서 삭제했습니다.")
            else:
                await interaction.response.send_message(f"{user.name}은 총관리자가 아닙니다.")
        else:
            await interaction.response.send_message("유효하지 않은 액션입니다. '추가' 또는 '삭제'를 선택하세요.")
    else:
        await interaction.response.send_message("당신은 총관리자를 추가하거나 삭제할 권한이 없습니다.")

@client.tree.command(name="차단", description="사용자를 차단하거나 차단을 해제합니다.")
@app_commands.describe(action="차단하거나 차단 해제할 작업", user="차단하거나 차단 해제할 사용자")
@app_commands.choices(action=[
    app_commands.Choice(name="추가", value="add"),
    app_commands.Choice(name="삭제", value="remove")
])
async def manage_ban(interaction: discord.Interaction, action: str, user: discord.User):
    if is_admin(interaction.user.id):
        users = load_users()
        if action == "add":
            if users.get(user.id, {}).get('banned') == 'True':
                await interaction.response.send_message(f"{user.name}은 이미 차단된 사용자입니다.")
            else:
                users[user.id]['banned'] = 'True'
                save_users(users)
                await interaction.response.send_message(f"{user.name}을 차단했습니다.")
        elif action == "remove":
            if users.get(user.id, {}).get('banned') == 'False':
                await interaction.response.send_message(f"{user.name}은 차단된 사용자가 아닙니다.")
            else:
                users[user.id]['banned'] = 'False'
                save_users(users)
                await interaction.response.send_message(f"{user.name}의 차단을 해제했습니다.")
        else:
            await interaction.response.send_message("유효하지 않은 액션입니다. '추가' 또는 '삭제'를 선택하세요.")
    else:
        await interaction.response.send_message("당신은 사용자를 차단하거나 차단 해제할 권한이 없습니다.")

@client.tree.command(name="생성", description="새로운 라이센스를 생성합니다.")
async def create_license(interaction: discord.Interaction):
    user_id = interaction.user.id
    if is_banned(user_id):
        await interaction.response.send_message("당신은 차단되어 있어서 봇 사용이 금지되어 있습니다.")
        return

    user_info = get_user_info(user_id)
    if not user_info:
        await interaction.response.send_message("가입되지 않은 사용자입니다. /가입 명령어를 사용하여 가입하십시오.")
        return

    if user_info.get('license'):
        await interaction.response.send_message("각 사용자는 하나의 라이센스만 가질 수 있습니다.")
        return

    license_code = generate_license()
    plan = "deluxe"  # 기본 플랜을 deluxe로 변경
    expiry_date = (datetime.now() + timedelta(days=365)).strftime("%Y-%m-%d")
    
    user_info['license'] = license_code
    user_info['plan'] = plan
    user_info['expiry_date'] = expiry_date
    save_users({user_id: user_info})
    
    await interaction.response.send_message(f"새로운 라이센스가 생성되었습니다: {license_code}", ephemeral=True)

async def list_info_function(interaction: discord.Interaction, option: str):
    user_id = interaction.user.id
    if not is_admin(user_id) and user_id != client.admin_id:
        await interaction.response.send_message("당신은 이 명령어를 사용할 권한이 없습니다.")
        return

    users = load_users()

    if option == "라이센스":
        licenses = [info for info in users.values() if info.get('license')]
        if licenses:
            license_list = "\n".join([f"사용자: {info['username']}, 라이센스: {info['license']}" for info in licenses])
            await interaction.response.send_message(f"라이센스 목록:\n{license_list}", ephemeral=True)
        else:
            await interaction.response.send_message("생성된 라이센스가 없습니다.", ephemeral=True)
    
    elif option == "유저":
        user_list = "\n".join([info['username'] for info in users.values()])
        await interaction.response.send_message(f"가입된 유저 목록:\n{user_list}" if user_list else "가입된 유저가 없습니다.", ephemeral=True)

    elif option == "차단":
        banned_users = [info['username'] for info in users.values() if info.get('banned') == 'True']
        banned_list = "\n".join(banned_users)
        await interaction.response.send_message(f"차단된 유저 목록:\n{banned_list}" if banned_list else "차단된 유저가 없습니다.", ephemeral=True)

    elif option == "총관리자":
        admin_users = [interaction.guild.get_member(admin_id) for admin_id in load_config().get("admins", [])]
        admin_list = "\n".join([user.name for user in admin_users if user is not None])
        await interaction.response.send_message(f"총관리자 목록:\n{admin_list}" if admin_list else "총관리자가 없습니다.", ephemeral=True)
    
    else:
        await interaction.response.send_message("유효하지 않은 옵션입니다. '라이센스', '유저', '차단', '총관리자' 중 하나를 선택하세요.", ephemeral=True)

@client.tree.command(name="목록", description="라이센스, 유저, 차단, 총관리자 목록을 표시합니다.")
@app_commands.describe(option="표시할 목록의 종류")
@app_commands.choices(option=[
    app_commands.Choice(name="라이센스", value="라이센스"),
    app_commands.Choice(name="유저", value="유저"),
    app_commands.Choice(name="차단", value="차단"),
    app_commands.Choice(name="총관리자", value="총관리자")
])
async def list_info(interaction: discord.Interaction, option: str):
    await list_info_function(interaction, option)

async def manage_user_function(interaction: discord.Interaction, user: discord.User, action: str, action_value: str = None):
    if not is_admin(interaction.user.id) and interaction.user.id != client.admin_id:
        await interaction.followup.send("당신은 이 명령어를 사용할 권한이 없습니다.")
        return

    users = load_users()
    if user.id not in users:
        await interaction.followup.send("해당 유저는 가입되어 있지 않습니다.")
        return

    user_info = users[user.id]

    if action == "라이센스변경":
        new_license = generate_license()
        user_info['license'] = new_license
        await interaction.followup.send(f"{user.name}의 라이센스가 변경되었습니다: {new_license}")
    elif action == "라이센스삭제":
        user_info['license'] = ''
        await interaction.followup.send(f"{user.name}의 라이센스가 삭제되었습니다.")
    elif action == "플랜변경(Deluxe)":
        user_info['plan'] = "deluxe"
        await interaction.followup.send(f"{user.name}의 플랜이 deluxe로 변경되었습니다.")
    elif action == "플랜변경(Standard)":
        user_info['plan'] = "standard"
        await interaction.followup.send(f"{user.name}의 플랜이 standard로 변경되었습니다.")
    elif action == "플랜변경(Premium)":
        user_info['plan'] = "premium"
        await interaction.followup.send(f"{user.name}의 플랜이 premium으로 변경되었습니다.")
    elif action == "만료일변경":
        try:
            new_expiry = datetime.strptime(action_value, "%Y%m%d").strftime("%Y-%m-%d")
            user_info['expiry_date'] = new_expiry
            await interaction.followup.send(f"{user.name}의 만료일이 {new_expiry}로 변경되었습니다.")
        except ValueError:
            await interaction.followup.send("유효하지 않은 날짜 형식입니다. 'YYYYMMDD' 형식으로 입력하세요.")
    else:
        await interaction.followup.send("유효하지 않은 작업입니다.")

    save_users(users)

@client.tree.command(name="관리", description="유저의 라이센스, 플랜, 만료일을 관리합니다.")
@app_commands.describe(user="관리할 유저", action="수행할 작업", action_value="설정할 값")
@app_commands.choices(action=[
    app_commands.Choice(name="라이센스변경", value="라이센스변경"),
    app_commands.Choice(name="라이센스삭제", value="라이센스삭제"),
    app_commands.Choice(name="플랜변경(Deluxe)", value="플랜변경(Deluxe)"),
    app_commands.Choice(name="플랜변경(Standard)", value="플랜변경(Standard)"),
    app_commands.Choice(name="플랜변경(Premium)", value="플랜변경(Premium)"),
    app_commands.Choice(name="만료일변경", value="만료일변경")
])
async def manage_user(interaction: discord.Interaction, user: discord.User, action: str, action_value: str = None):
    await manage_user_function(interaction, user, action, action_value)

@client.tree.command(name="버튼", description="버튼을 통해 다양한 기능을 이용합니다.")
async def button_menu(interaction: discord.Interaction):
    if not (is_admin(interaction.user.id) or interaction.user.id == client.admin_id):
        await interaction.response.send_message("이 명령어를 사용할 권한이 없습니다.", ephemeral=True)
        return

    embed = discord.Embed(title="기능 선택", description="원하는 기능을 선택해주세요.", color=discord.Color.blue())
    
    view = View()
    buttons = [
        Button(style=discord.ButtonStyle.primary, label="가입", custom_id="register"),
        Button(style=discord.ButtonStyle.primary, label="탈퇴", custom_id="unregister"),
        Button(style=discord.ButtonStyle.primary, label="내정보", custom_id="my_info"),
        Button(style=discord.ButtonStyle.primary, label="목록 확인", custom_id="list_info"),
        Button(style=discord.ButtonStyle.primary, label="관리", custom_id="manage")
    ]
    
    for button in buttons:
        view.add_item(button)
    
    async def button_callback(interaction: discord.Interaction):
        if not (is_admin(interaction.user.id) or interaction.user.id == client.admin_id):
            await interaction.response.send_message("이 기능을 사용할 권한이 없습니다.", ephemeral=True)
            return

        custom_id = interaction.data['custom_id']
        if custom_id == "register":
            await register_function(interaction)
        elif custom_id == "unregister":
            await unregister_function(interaction)
        elif custom_id == "my_info":
            await my_info_function(interaction)
        elif custom_id == "list_info":
            await list_info_menu(interaction)
        elif custom_id == "manage":
            await manage_menu(interaction)
    
    for button in view.children:
        button.callback = button_callback
    
    await interaction.response.send_message(embed=embed, view=view)

async def list_info_menu(interaction: discord.Interaction):
    embed = discord.Embed(title="목록 확인", description="확인할 목록을 선택해주세요.", color=discord.Color.green())
    
    view = View()
    options = ["라이센스", "유저", "차단", "총관리자"]
    
    for option in options:
        button = Button(style=discord.ButtonStyle.secondary, label=option, custom_id=f"list_{option}")
        view.add_item(button)
    
    async def list_button_callback(interaction: discord.Interaction):
        option = interaction.data['custom_id'].split("_")[1]
        await list_info_function(interaction, option)
    
    for button in view.children:
        button.callback = list_button_callback
    
    await interaction.response.send_message(embed=embed, view=view)

async def manage_menu(interaction: discord.Interaction):
    embed = discord.Embed(title="관리", description="수행할 작업을 선택해주세요.", color=discord.Color.orange())
    
    view = View()
    actions = [
        "라이센스변경", "라이센스삭제", "플랜변경(Deluxe)",
        "플랜변경(Standard)", "플랜변경(Premium)", "만료일변경"
    ]
    
    for action in actions:
        button = Button(style=discord.ButtonStyle.secondary, label=action, custom_id=f"manage_{action}")
        view.add_item(button)
    
    async def manage_button_callback(interaction: discord.Interaction):
        action = interaction.data['custom_id'].split("_", 1)[1]
        await interaction.response.send_message("관리할 유저의 ID를 입력해주세요.")
        
        def check(m):
            return m.author.id == interaction.user.id and m.channel.id == interaction.channel.id
        
        try:
            user_message = await client.wait_for('message', check=check, timeout=30.0)
            user_id = int(user_message.content)
            user = await client.fetch_user(user_id)
            
            if action == "만료일변경":
                await interaction.channel.send("변경할 만료일을 YYYYMMDD 형식으로 입력해주세요.")
                date_message = await client.wait_for('message', check=check, timeout=30.0)
                action_value = date_message.content
            else:
                action_value = None
            
            await manage_user_function(interaction, user, action, action_value)
        except ValueError:
            await interaction.channel.send("올바른 유저 ID를 입력해주세요.")
        except discord.NotFound:
            await interaction.channel.send("해당 ID의 유저를 찾을 수 없습니다.")
        except asyncio.TimeoutError:
            await interaction.channel.send("시간이 초과되었습니다. 다시 시도해주세요.")
    
    for button in view.children:
        button.callback = manage_button_callback
    
    await interaction.response.send_message(embed=embed, view=view)

client.run('토큰')
