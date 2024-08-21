import discord
from discord import app_commands
import csv
import json
import random
import string
import os
from datetime import datetime, timedelta

class MyClient(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)
        self.admin_id = 1238461591557771355
        self.config_file = r'config.json'
        self.users_csv = r'users.csv'
        
    async def setup_hook(self):
        await self.tree.sync()

client = MyClient()

class ConfirmView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.value = None

    @discord.ui.button(label="확인", style=discord.ButtonStyle.danger)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = True
        self.stop()

    @discord.ui.button(label="취소", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = False
        self.stop()

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

def load_banlist():
    if os.path.exists('banlist.csv'):
        banlist = {}
        with open('banlist.csv', 'r', encoding='utf-8') as f:
            reader = csv.Dictreader(f)
            for row in reader:
                banlist[int(row['user_id'])] = row
    return banlist

def save_banlist(banlist):
    with open('banlist.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['user_id', 'reason'])
        writer.writeheader()

        writer = csv.writer(f)
        for user_id, reason in banlist.items():
            writer.writerow([user_id, reason])

def save_users(users):
    with open(client.users_csv, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['user_id', 'username', 'license', 'plan', 'expiry_date'])
        writer.writeheader()
        for user_id, user_info in users.items():
            writer.writerow(user_info)

def is_admin(user_id):
    config = load_config()
    return user_id in config["admins"]

def is_banned(user_id):
    banlist = load_banlist()
    return user_id in banlist

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

@client.tree.command(name="정보", description="정보를 확인합니다.")
async def my_info(interaction: discord.Interaction, user: discord.User = None):
    if user != None:
        if interaction.user.id != client.admin_id and is_admin(interaction.user.id) != True:
            embed = discord.Embed(title="ERROR", description="당신은 이 명령어를 사용할 권한이 없습니다.", color=discord.Color.red())
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        else:
            user_id = user.id
    else:
        user_id = interaction.user.id

    
    user_info = get_user_info(user_id)
    
    if not user_info:
        embed = discord.Embed(title="ERROR", description="가입되지 않은 사용자입니다.", color=discord.Color.red())
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    banned_status = "차단됨" if user_info.get('banned') == 'True' else "차단되지 않음"
    license_info = user_info.get('license', '라이센스 없음')
    plan = user_info.get('plan', '없음')
    expiry_date = user_info.get('expiry_date', '없음')
    
    embed = discord.Embed(title="내 정보", color=discord.Color.blue())
    embed.add_field(name="**유저 아이디**", value=user_id)
    embed.add_field(name="**유저 닉네임**", value=interaction.user.name)
    embed.add_field(name="**차단 여부**", value=banned_status)
    embed.add_field(name="**라이센스**", value=license_info)
    embed.add_field(name="**플랜**", value=plan)
    embed.add_field(name="**만료일**", value=expiry_date)
    embed.set_thumbnail(url=interaction.user.avatar)

    # info_message = (
    #     f"**유저 아이디:** {user_id}\n"
    #     f"**유저 닉네임:** {interaction.user.name}\n"
    #     f"**차단 여부:** {banned_status}\n"
    #     f"**라이센스:** {license_info}\n"
    #     f"**플랜:** {plan}\n"
    #     f"**만료일:** {expiry_date}"
    # )
    
    await interaction.response.send_message(embed=embed, ephemeral=True)

@client.tree.command(name="총관리자", description="총관리자를 추가하거나 삭제합니다.")
@app_commands.describe(action="추가하거나 삭제할 작업", user="총관리자 상태로 만들거나 삭제할 사용자")
@app_commands.choices(action=[
    app_commands.Choice(name="추가", value="add"),
    app_commands.Choice(name="삭제", value="remove")
])
async def manage_admin(interaction: discord.Interaction, action: str, user: discord.User):
    if interaction.user.id == client.admin_id:
        config = load_config()
        embed = discord.Embed()
        if action == "add":
            if user.id not in config["admins"]:
                config["admins"].append(user.id)
                save_config(config)
                embed.title = "SUCCESS"
                embed.description = f"{user.name}을 총관리자로 추가했습니다."
                embed.color = discord.Color.green()
            else:
                embed.title = "ERROR"
                embed.description = f"{user.name}은 이미 총관리자입니다."
                embed.color = discord.Color.red()
        elif action == "remove":
            if user.id in config["admins"]:
                config["admins"].remove(user.id)
                save_config(config)
                embed.title = "SUCCESS"
                embed.description = f"{user.name}을 총관리자에서 삭제했습니다."
                embed.color = discord.Color.green()
            else:
                embed.title = "ERROR"
                embed.description = f"{user.name}은 총관리자가 아닙니다."
                embed.color = discord.Color.red()
        else:
            embed.title = "ERROR"
            embed.description = "유효하지 않은 액션입니다. '추가' 또는 '삭제'를 선택하세요."
            embed.color = discord.Color.red()
    else:
        embed = discord.Embed(title="ERROR", description="당신은 총관리자를 추가하거나 삭제할 권한이 없습니다.", color=discord.Color.red())
    
    await interaction.response.send_message(embed=embed, ephemeral=True)

@client.tree.command(name="차단", description="사용자를 차단하거나 차단을 해제합니다.")
@app_commands.describe(action="차단하거나 차단 해제할 작업", user="차단하거나 차단 해제할 사용자", reason="차단 사유 (차단 시에만 필요)")
@app_commands.choices(action=[
    app_commands.Choice(name="추가", value="add"),
    app_commands.Choice(name="삭제", value="remove")
])
async def manage_ban(interaction: discord.Interaction, action: str, user: discord.User, reason: str = None):
    if is_admin(interaction.user.id):
        banlist = load_banlist()
        embed = discord.Embed()
        if action == "add":
            if user.id in banlist:
                embed.title = "ERROR"
                embed.description = f"{user.name}은 이미 차단된 사용자입니다."
                embed.color = discord.Color.red()
            else:
                if reason is None:
                    embed.title = "ERROR"
                    embed.description = "차단 사유를 입력해주세요."
                    embed.color = discord.Color.red()
                else:
                    banlist[user.id] = reason
                    save_banlist(banlist)
                    embed.title = "SUCCESS"
                    embed.description = f"{user.name}을 차단했습니다. 사유: {reason}"
                    embed.color = discord.Color.green()
        elif action == "remove":
            if user.id not in banlist:
                embed.title = "ERROR"
                embed.description = f"{user.name}은 차단된 사용자가 아닙니다."
                embed.color = discord.Color.red()
            else:
                del banlist[user.id]
                save_banlist(banlist)
                embed.title = "SUCCESS"
                embed.description = f"{user.name}의 차단을 해제했습니다."
                embed.color = discord.Color.green()
        else:
            embed.title = "ERROR"
            embed.description = "유효하지 않은 액션입니다. '추가' 또는 '삭제'를 선택하세요."
            embed.color = discord.Color.red()
    else:
        embed = discord.Embed(title="ERROR", description="당신은 사용자를 차단하거나 차단 해제할 권한이 없습니다.", color=discord.Color.red())
    
    await interaction.response.send_message(embed=embed, ephemeral=True)

@client.tree.command(name="가입", description="봇 사용을 위한 가입을 합니다.")
async def register(interaction: discord.Interaction):
    user_id = interaction.user.id
    if is_banned(user_id):
        embed = discord.Embed(title="ERROR", description="BOT Service 에서 차단된 유저입니다.", color=discord.Color.red())
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    if get_user_info(user_id):
        embed = discord.Embed(title="ERROR", description="이미 가입된 사용자입니다.", color=discord.Color.red())
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    add_user(user_id, interaction.user.name)
    embed = discord.Embed(title="SUCCESS", description="가입이 완료되었습니다. 이제 명령어를 사용할 수 있습니다.", color=discord.Color.green())
    await interaction.response.send_message(embed=embed, ephemeral=True)

@client.tree.command(name="탈퇴", description="봇 사용을 위한 탈퇴를 합니다.")
async def unregister(interaction: discord.Interaction):
    user_id = interaction.user.id
    if is_banned(user_id):
        embed = discord.Embed(title="ERROR", description="BOT Service에서 차단된 유저입니다.", color=discord.Color.red())
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    if not get_user_info(user_id):
        embed = discord.Embed(title="ERROR", description="가입되지 않은 사용자입니다.", color=discord.Color.red())
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    view = ConfirmView()
    embed = discord.Embed(title="CONFIRM", description="정말로 탈퇴하시겠습니까?", color=discord.Color.orange())
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    timeout = await view.wait()
    if timeout:
        embed.title = "시간 초과"
        embed.description = "시간이 초과되었습니다. 다시 시도해주세요."
        embed.color = discord.Color.red()
    elif view.value:
        remove_user(user_id)
        embed.title = "SUCCESS"
        embed.description = "탈퇴가 완료되었습니다. 모든 라이센스가 삭제되었습니다.\n저희 서비스를 이용해주셔서 감사합니다."
        embed.color = discord.Color.green()
    else:
        embed.title = "취소됨"
        embed.description = "탈퇴가 취소되었습니다."
        embed.color = discord.Color.blue()

    await interaction.edit_original_response(embed=embed, view=None)

@client.tree.command(name="생성", description="새로운 라이센스를 생성합니다.")
async def create_license(interaction: discord.Interaction):
    user_id = interaction.user.id
    if is_banned(user_id):
        embed = discord.Embed(title="ERROR", description="BOT Service 에서 차단된 유저입니다.", color=discord.Color.red())
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    user_info = get_user_info(user_id)
    if not user_info:
        embed = discord.Embed(title="ERROR", description=f"가입되지 않은 사용자입니다.\n /가입 명령어를 사용하여 가입하십시오.", color=discord.Color.red())
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    if user_info.get('license'):
        embed = discord.Embed(title="ERROR", description="이미 라이센스를 발급하셨습니다.", color=discord.Color.red())
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    license_code = generate_license()
    plan = "free"  # 기본 플랜을 deluxe로 변경
    expiry_date = (datetime.now() + timedelta(days=365)).strftime("%Y-%m-%d")
    
    user_info['license'] = license_code
    user_info['plan'] = plan
    user_info['expiry_date'] = expiry_date
    save_users({user_id: user_info})
    
    embed = discord.Embed(title="SUCCESS", description=f"새로운 라이센스가 생성되었습니다\n ```{license_code}```", color=discord.Color.green())
    await interaction.response.send_message(embed=embed, ephemeral=True)

@client.tree.command(name="목록", description="라이센스, 유저, 차단, 총관리자 목록을 표시합니다.")
@app_commands.describe(option="표시할 목록의 종류")
@app_commands.choices(option=[
    app_commands.Choice(name="라이센스", value="licenses"),
    app_commands.Choice(name="유저", value="users"),
    app_commands.Choice(name="차단", value="banned"),
    app_commands.Choice(name="총관리자", value="admins")
])
async def list_info(interaction: discord.Interaction, option: str):
    user_id = interaction.user.id
    if not is_admin(user_id) and user_id != client.admin_id:
        embed = discord.Embed(title="ERROR", description="당신은 이 명령어를 사용할 권한이 없습니다.", color=discord.Color.red())
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    users = load_users()

    if option == "licenses":
        licenses = [info for info in users.values() if info.get('license')]
        if licenses:
            license_list = "\n".join([f"사용자: {info['username']}, 라이센스: {info['license']}" for info in licenses])
            embed = discord.Embed(title="라이센스 목록", description=license_list, color=discord.Color.blue())
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            embed = discord.Embed(title="ERROR", description="생성된 라이센스가 없습니다.", color=discord.Color.red())
            await interaction.response.send_message(embed=embed, ephemeral=True)
    
    elif option == "users":
        user_list = "\n".join([info['username'] for info in users.values()])
        embed = discord.Embed(title="유저 목록", description=user_list, color=discord.Color.blue())
        if user_list:
            await interaction.response.send_message(embed=embed, ephemeral=True, color=discord.Color.blue())    
        else:
            embed = discord.Embed(title="ERROR", description="가입된 유저가 없습니다.", color=discord.Color.red())
            await interaction.response.send_message(embed=embed, ephemeral=True)

    elif option == "banned":
        banned_users = [info['username'] for info in users.values() if info.get('banned') == 'True']
        banned_list = "\n".join(banned_users)
        if banned_list:
            embed = discord.Embed(title="차단된 유저 목록", description=banned_list, color=discord.Color.blue())
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            embed = discord.Embed(title="ERROR", description="차단된 유저가 없습니다.", color=discord.Color.red())
            await interaction.response.send_message(embed=embed, ephemeral=True)

    elif option == "admins":
        admin_users = [interaction.guild.get_member(admin_id) for admin_id in load_config().get("admins", [])]
        admin_list = "\n".join([user.name for user in admin_users if user is not None])
        if admin_list:
            embed = discord.Embed(title="총관리자 목록", description=admin_list, color=discord.Color.blue())
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            embed = discord.Embed(title="ERROR", description="총관리자가 없습니다.", color=discord.Color.red())
            await interaction.response.send_message(embed=embed, ephemeral=True)
    
    else:
        embed = discord.Embed(title="ERROR", description="유효하지 않은 옵션입니다. '라이센스', '유저', '차단', '총관리자' 중 하나를 선택하세요.", color=discord.Color.red())
        await interaction.response.send_message(embed=embed, ephemeral=True)

@client.tree.command(name="관리", description="유저의 라이센스, 플랜, 만료일을 관리합니다.")
@app_commands.describe(user="관리할 유저", action="수행할 작업", action_value="설정할 값")
@app_commands.choices(action=[
    app_commands.Choice(name="라이센스변경", value="license_change"),
    app_commands.Choice(name="라이센스삭제", value="license_delete"),
    app_commands.Choice(name="플랜변경(Free)", value="plan_free"),
    app_commands.Choice(name="플랜변경(Standard)", value="plan_deluxe"),
    app_commands.Choice(name="플랜변경(Premium)", value="plan_premium"),
    app_commands.Choice(name="만료일변경", value="expiry_change")
])
async def manage_user(interaction: discord.Interaction, user: discord.User, action: str, action_value: str = None):
    if not is_admin(interaction.user.id) and interaction.user.id != client.admin_id:
        embed = discord.Embed(title="ERROR", description="당신은 이 명령어를 사용할 권한이 없습니다.", color=discord.Color.red())
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    users = load_users()
    if user.id not in users:
        embed = discord.Embed(title="ERROR", description="해당 유저는 가입되어 있지 않습니다.", color=discord.Color.red())
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    user_info = users[user.id]

    if action == "license_change":
        new_license = generate_license()
        user_info['license'] = new_license
        embed = discord.Embed(title="SUCCESS", description=f"{user.name}의 라이센스가 변경되었습니다: {new_license}", color=discord.Color.green())
        await interaction.response.send_message(embed=embed, ephemeral=True)
    elif action == "license_delete":
        user_info['license'] = ''
        embed = discord.Embed(title="SUCCESS", description=f"{user.name}의 라이센스가 삭제되었습니다.", color=discord.Color.green())
        await interaction.response.send_message(embed=embed, ephemeral=True)
    elif action == "plan_free":
        user_info['plan'] = "free"
        embed = discord.Embed(title="SUCCESS", description=f"{user.name}의 플랜이 Free로 변경되었습니다.", color=discord.Color.green())
        await interaction.response.send_message(embed=embed, ephemeral=True)
    elif action == "plan_standard":
        user_info['plan'] = "standard"
        embed = discord.Embed(title="SUCCESS", description=f"{user.name}의 플랜이 Standard로 변경되었습니다.", color=discord.Color.green())
        await interaction.response.send_message(embed=embed, ephemeral=True)
    elif action == "plan_premium":
        user_info['plan'] = "premium"
        embed = discord.Embed(title="SUCCESS", description=f"{user.name}의 플랜이 Premium로 변경되었습니다.", color=discord.Color.green())
        await interaction.response.send_message(embed=embed, ephemeral=True)
    elif action == "expiry_change":
        try:
            new_expiry = datetime.strptime(action_value, "%Y%m%d").strftime("%Y-%m-%d")
            user_info['expiry_date'] = new_expiry
            embed = discord.Embed(title="SUCCESS", description=f"{user.name}의 만료일이 변경되었습니다: {new_expiry}", color=discord.Color.green())
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except ValueError:
            embed = discord.Embed(title="ERROR", description="유효하지 않은 날짜 형식입니다. 'YYYYMMDD' 형식으로 입력하세요.", color=discord.Color.red())
            await interaction.response.send_message(embed=embed, ephemeral=True)
    else:
        embed = discord.Embed(title="ERROR", description="유효하지 않은 작업입니다.", color=discord.Color.red())
        await interaction.response.send_message(embed=embed, ephemeral=True)

    save_users(users)

class MainView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="가입", style=discord.ButtonStyle.primary)
    async def register_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = interaction.user.id
        if is_banned(user_id):
            embed = discord.Embed(title="ERROR", description="BOT Service 에서 차단된 유저입니다.", color=discord.Color.red())
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        if get_user_info(user_id):
            embed = discord.Embed(title="ERROR", description="이미 가입된 사용자입니다.", color=discord.Color.red())
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        add_user(user_id, interaction.user.name)
        embed = discord.Embed(title="SUCCESS", description="가입이 완료되었습니다. 이제 명령어를 사용할 수 있습니다.", color=discord.Color.green())
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="생성", style=discord.ButtonStyle.primary)
    async def create_license_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = interaction.user.id
        if is_banned(user_id):
            embed = discord.Embed(title="ERROR", description="BOT Service 에서 차단된 유저입니다.", color=discord.Color.red())
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        user_info = get_user_info(user_id)
        if not user_info:
            embed = discord.Embed(title="ERROR", description=f"가입되지 않은 사용자입니다.\n /가입 명령어를 사용하여 가입하십시오.", color=discord.Color.red())
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        if user_info.get('license'):
            embed = discord.Embed(title="ERROR", description="이미 라이센스를 발급하셨습니다.", color=discord.Color.red())
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        license_code = generate_license()
        plan = "free"
        expiry_date = (datetime.now() + timedelta(days=365)).strftime("%Y-%m-%d")
        
        user_info['license'] = license_code
        user_info['plan'] = plan
        user_info['expiry_date'] = expiry_date
        save_users({user_id: user_info})
        
        embed = discord.Embed(title="SUCCESS", description=f"새로운 라이센스가 생성되었습니다\n ```{license_code}```", color=discord.Color.green())
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="내 정보", style=discord.ButtonStyle.primary)
    async def my_info_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = interaction.user.id
        user_info = get_user_info(user_id)
        
        if not user_info:
            embed = discord.Embed(title="ERROR", description="가입되지 않은 사용자입니다.", color=discord.Color.red())
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        banned_status = "차단됨" if user_info.get('banned') == 'True' else "차단되지 않음"
        license_info = user_info.get('license', '라이센스 없음')
        plan = user_info.get('plan', '없음')
        expiry_date = user_info.get('expiry_date', '없음')
        
        embed = discord.Embed(title="내 정보", color=discord.Color.blue())
        embed.add_field(name="**유저 아이디**", value=user_id)
        embed.add_field(name="**유저 닉네임**", value=interaction.user.name)
        embed.add_field(name="**차단 여부**", value=banned_status)
        embed.add_field(name="**라이센스**", value=license_info)
        embed.add_field(name="**플랜**", value=plan)
        embed.add_field(name="**만료일**", value=expiry_date)
        embed.set_thumbnail(url=interaction.user.avatar)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="관리", style=discord.ButtonStyle.primary)
    async def manage_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if is_admin(interaction.user.id) or interaction.user.id == client.admin_id:
            await interaction.response.send_message("관리 옵션을 선택하세요:", view=ManageView(), ephemeral=True)
        else:
            embed = discord.Embed(title="ERROR", description="관리 권한이 없습니다.", color=discord.Color.red())
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="탈퇴", style=discord.ButtonStyle.danger)
    async def unregister_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = interaction.user.id
        if is_banned(user_id):
            embed = discord.Embed(title="ERROR", description="BOT Service에서 차단된 유저입니다.", color=discord.Color.red())
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        if not get_user_info(user_id):
            embed = discord.Embed(title="ERROR", description="가입되지 않은 사용자입니다.", color=discord.Color.red())
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        view = ConfirmView()
        embed = discord.Embed(title="CONFIRM", description="정말로 탈퇴하시겠습니까?", color=discord.Color.orange())
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

        timeout = await view.wait()
        if timeout:
            embed.title = "시간 초과"
            embed.description = "시간이 초과되었습니다. 다시 시도해주세요."
            embed.color = discord.Color.red()
        elif view.value:
            remove_user(user_id)
            embed.title = "SUCCESS"
            embed.description = "탈퇴가 완료되었습니다. 모든 라이센스가 삭제되었습니다.\n저희 서비스를 이용해주셔서 감사합니다."
            embed.color = discord.Color.green()
        else:
            embed.title = "취소됨"
            embed.description = "탈퇴가 취소되었습니다."
            embed.color = discord.Color.blue()

        await interaction.edit_original_response(embed=embed, view=None)

class ManageView(discord.ui.View):
    def __init__(self):
        super().__init__()

    @discord.ui.button(label="라이센스 변경", style=discord.ButtonStyle.secondary)
    async def change_license_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(UserInputModal("라이센스 변경", "license_change"))

    @discord.ui.button(label="라이센스 삭제", style=discord.ButtonStyle.secondary)
    async def delete_license_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(UserInputModal("라이센스 삭제", "license_delete"))

    @discord.ui.button(label="플랜 변경", style=discord.ButtonStyle.secondary)
    async def change_plan_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("플랜을 선택하세요:", view=PlanView(), ephemeral=True)

    @discord.ui.button(label="만료일 변경", style=discord.ButtonStyle.secondary)
    async def change_expiry_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(UserInputModal("만료일 변경", "expiry_change"))

class PlanView(discord.ui.View):
    def __init__(self):
        super().__init__()

    @discord.ui.button(label="Free", style=discord.ButtonStyle.secondary)
    async def free_plan_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(UserInputModal("플랜 변경 (Free)", "plan_free"))

    @discord.ui.button(label="Standard", style=discord.ButtonStyle.secondary)
    async def standard_plan_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(UserInputModal("플랜 변경 (Standard)", "plan_standard"))

    @discord.ui.button(label="Premium", style=discord.ButtonStyle.secondary)
    async def premium_plan_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(UserInputModal("플랜 변경 (Premium)", "plan_premium"))

class UserInputModal(discord.ui.Modal):
    def __init__(self, title: str, action: str):
        super().__init__(title=title)
        self.action = action
        
        if action == "expiry_change":
            self.user_id = discord.ui.TextInput(
                label="유저 ID",
                placeholder="변경할 유저의 ID를 입력하세요",
                style=discord.TextStyle.short,
                required=True
            )
            self.expiry_date = discord.ui.TextInput(
                label="새 만료일",
                placeholder="YYYYMMDD 형식으로 입력하세요",
                style=discord.TextStyle.short,
                required=True
            )
            self.add_item(self.user_id)
            self.add_item(self.expiry_date)
        else:
            self.user_input = discord.ui.TextInput(
                label="유저 ID",
                placeholder="유저 ID를 입력하세요",
                style=discord.TextStyle.short,
                required=True
            )
            self.add_item(self.user_input)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            if self.action == "expiry_change":
                user_id = int(self.user_id.value)
                new_expiry = self.expiry_date.value
            else:
                user_id = int(self.user_input.value)
            
            user = await interaction.client.fetch_user(user_id)
            users = load_users()
            
            if user.id not in users:
                embed = discord.Embed(title="ERROR", description="해당 유저는 가입되어 있지 않습니다.", color=discord.Color.red())
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

            user_info = users[user.id]

            if self.action == "license_change":
                new_license = generate_license()
                user_info['license'] = new_license
                embed = discord.Embed(title="SUCCESS", description=f"{user.name}의 라이센스가 변경되었습니다: {new_license}", color=discord.Color.green())
            elif self.action == "license_delete":
                user_info['license'] = ''
                embed = discord.Embed(title="SUCCESS", description=f"{user.name}의 라이센스가 삭제되었습니다.", color=discord.Color.green())
            elif self.action.startswith("plan_"):
                plan = self.action.split("_")[1]
                user_info['plan'] = plan
                embed = discord.Embed(title="SUCCESS", description=f"{user.name}의 플랜이 {plan.capitalize()}로 변경되었습니다.", color=discord.Color.green())
            elif self.action == "expiry_change":
                new_expiry_date = datetime.strptime(new_expiry, "%Y%m%d").strftime("%Y-%m-%d")
                user_info['expiry_date'] = new_expiry_date
                embed = discord.Embed(title="SUCCESS", description=f"{user.name}의 만료일이 변경되었습니다: {new_expiry_date}", color=discord.Color.green())

            save_users(users)
            await interaction.response.send_message(embed=embed, ephemeral=True)

        except ValueError:
            if self.action == "expiry_change":
                error_message = "유효하지 않은 입력 형식입니다. 유저 ID는 숫자여야 하고, 만료일은 YYYYMMDD 형식이어야 합니다."
            else:
                error_message = "유효하지 않은 유저 ID입니다."
            embed = discord.Embed(title="ERROR", description=error_message, color=discord.Color.red())
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
@client.tree.command(name="패널", description="관리 패널을 표시합니다.")
async def show_panel(interaction: discord.Interaction):
    embed = discord.Embed(title="관리 패널", description="원하는 작업을 선택하세요.", color=discord.Color.blue())
    await interaction.response.send_message(embed=embed, view=MainView())

client.run('토큰')
