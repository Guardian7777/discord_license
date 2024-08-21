import discord
from discord import app_commands
import json
import random
import string
import os

class MyClient(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)
        self.admin_id = 1238461591557771355 # 본인 아이디 넣으셈
        self.config_file = r'config.json' # 콘픽 경로 복사한 다음 config.json 지우고 붙여넣기 ㄱㄱ

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
    config = {"licenses": [], "banned_users": [], "admins": [], "registered_users": []}
    save_config(config)
    return config

def save_config(config):
    with open(client.config_file, 'w') as f:
        json.dump(config, f, indent=4)

def is_admin(user_id):
    config = load_config()
    return user_id in config["admins"]

def is_banned(user_id):
    config = load_config()
    return user_id in config["banned_users"]

def is_registered(user_id):
    config = load_config()
    return user_id in config["registered_users"]

def generate_license():
    chars = ''.join(random.choices(string.ascii_uppercase + string.digits, k=16))
    return '-'.join([chars[i:i+4] for i in range(0, 16, 4)])

@client.event
async def on_ready():
    print(f'봇이 {client.user}로 로그인했습니다.')

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
        config = load_config()
        if action == "add":
            if user.id not in config["banned_users"]:
                config["banned_users"].append(user.id)
                save_config(config)
                await interaction.response.send_message(f"{user.name}을 차단했습니다.")
            else:
                await interaction.response.send_message(f"{user.name}은 이미 차단된 사용자입니다.")
        elif action == "remove":
            if user.id in config["banned_users"]:
                config["banned_users"].remove(user.id)
                save_config(config)
                await interaction.response.send_message(f"{user.name}의 차단을 해제했습니다.")
            else:
                await interaction.response.send_message(f"{user.name}은 차단된 사용자가 아닙니다.")
        else:
            await interaction.response.send_message("유효하지 않은 액션입니다. '추가' 또는 '삭제'를 선택하세요.")
    else:
        await interaction.response.send_message("당신은 사용자를 차단하거나 차단 해제할 권한이 없습니다.")

@client.tree.command(name="가입", description="봇 사용을 위한 가입을 합니다.")
async def register(interaction: discord.Interaction):
    if is_banned(interaction.user.id):
        await interaction.response.send_message("당신은 차단되어 있어서 가입할 수 없습니다.")
        return

    if is_registered(interaction.user.id):
        await interaction.response.send_message("이미 가입된 사용자입니다.")
        return

    config = load_config()
    config["registered_users"].append(interaction.user.id)
    save_config(config)
    await interaction.response.send_message("가입이 완료되었습니다. 이제 명령어를 사용할 수 있습니다.")

@client.tree.command(name="탈퇴", description="서비스에서 탈퇴를 합니다. 라이센스는 복구 불가능하니 신중하게 선택해주세요.")
async def unregister(interaction: discord.Interaction):
    if is_banned(interaction.user.id):
        await interaction.response.send_message("당신은 차단되어 있어서 탈퇴할 수 없습니다.")
        return

    if not is_registered(interaction.user.id):
        await interaction.response.send_message("가입되지 않은 사용자입니다.")
        return

    config = load_config()
    config["registered_users"].remove(interaction.user.id)
    config["licenses"] = [lic for lic in config["licenses"] if lic["user_id"] != interaction.user.id]
    save_config(config)
    await interaction.response.send_message("탈퇴가 완료되었습니다. 모든 라이센스가 삭제되었습니다.")

@client.tree.command(name="생성", description="새로운 라이센스를 생성합니다.")
async def create_license(interaction: discord.Interaction):
    if is_banned(interaction.user.id):
        await interaction.response.send_message("당신은 차단되어 있어서 봇 사용이 금지되어 있습니다.")
        return

    if not is_registered(interaction.user.id):
        await interaction.response.send_message("가입되지 않은 사용자입니다. /가입 명령어를 사용하여 가입하십시오.")
        return

    config = load_config()
    if any(lic['user_id'] == interaction.user.id for lic in config["licenses"]):
        await interaction.response.send_message("각 사용자는 하나의 라이센스만 가질 수 있습니다.")
        return

    license = generate_license()
    license_info = {
        "user_id": interaction.user.id,
        "username": interaction.user.name,
        "license": license
    }
    
    config["licenses"].append(license_info)
    save_config(config)
    
    await interaction.response.send_message(f"새로운 라이센스가 생성되었습니다: {license}")

@client.tree.command(name="목록", description="라이센스, 유저, 차단, 총관리자 목록을 표시합니다.")
@app_commands.describe(option="표시할 목록의 종류")
@app_commands.choices(option=[
    app_commands.Choice(name="라이센스", value="licenses"),
    app_commands.Choice(name="유저", value="users"),
    app_commands.Choice(name="차단", value="banned"),
    app_commands.Choice(name="총관리자", value="admins")
])
async def list_info(interaction: discord.Interaction, option: str):
    if is_banned(interaction.user.id):
        await interaction.response.send_message("당신은 차단되어 있어서 봇 사용이 금지되어 있습니다.")
        return

    if not is_registered(interaction.user.id):
        await interaction.response.send_message("가입되지 않은 사용자입니다. /가입 명령어를 사용하여 가입하십시오.")
        return

    config = load_config()

    if option == "licenses":
        licenses = config.get("licenses", [])
        if licenses:
            license_list = "\n".join([f"사용자: {lic['username']}, 라이센스: {lic['license']}" for lic in licenses])
            await interaction.response.send_message(f"라이센스 목록:\n{license_list}")
        else:
            await interaction.response.send_message("생성된 라이센스가 없습니다.")
    
    elif option == "users":
        registered_users = [interaction.guild.get_member(user_id) for user_id in config.get("registered_users", [])]
        user_list = "\n".join([user.name for user in registered_users if user is not None])
        await interaction.response.send_message(f"가입된 유저 목록:\n{user_list}" if user_list else "가입된 유저가 없습니다.")

    elif option == "banned":
        banned_users = [interaction.guild.get_member(user_id) for user_id in config.get("banned_users", [])]
        banned_list = "\n".join([user.name for user in banned_users if user is not None])
        await interaction.response.send_message(f"차단된 유저 목록:\n{banned_list}" if banned_list else "차단된 유저가 없습니다.")

    elif option == "admins":
        admin_users = [interaction.guild.get_member(user_id) for user_id in config.get("admins", [])]
        admin_list = "\n".join([user.name for user in admin_users if user is not None])
        await interaction.response.send_message(f"총관리자 목록:\n{admin_list}" if admin_list else "총관리자가 없습니다.")
    
    else:
        await interaction.response.send_message("유효하지 않은 옵션입니다. '라이센스', '유저', '차단', '총관리자' 중 하나를 선택하세요.")
# 봇토큰 넣으셈
client.run('토큰')
