import discord, dotenv, os, json, aiohttp
dotenv.load_dotenv()

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)


@client.event
async def on_ready():
    global client, client_session
    client_session = aiohttp.ClientSession()
    print(f'We have logged in as {client.user}')

async def fetch_remote_json(url):
    async with client_session.get(url) as resp:
        if resp.status == 200:
            text = await resp.text()
            try:
                if text.startswith('{"bug_type":') or text.startswith('{"app_name":'):
                    return json.loads(text.split("\n", 1)[1])
                else:
                    return json.loads(text)
            except:
                return None
        else:
            return None

async def parse_panic(file: discord.Attachment, msg: discord.Message):
    data = await fetch_remote_json(file.url)
    if data is not None:
        string = ""
        build = ""
        product = ""
        if "panicString" in data:
            string = data['panicString'].split("\n")[0]

        if "build" in data:
            build = data['build'].split("\n")[0]

        if "product" in data:
            product = data['product'].split("\n")[0]

        if string == "" or build == "" or product == "":
            return

        await msg.reply(f"`{discord.utils.escape_markdown(build)}` on a `{discord.utils.escape_markdown(product)}`!\n\nPanic string:```{discord.utils.escape_markdown(string)}```")

async def parse_crash(file: discord.Attachment, msg: discord.Message):
    data = await fetch_remote_json(file.url)
    if data is not None:
        err = ""
        triage = "(no triage)"
        product = ""
        build = ""
        if "exception" in data:
            err = f"{data['exception']['codes']} {data['exception']['type']} ({data['exception']['signal']})"

        if "ktriageinfo" in data:
            triage = data['ktriageinfo'].split("\n")[0]

        if "modelCode" in data:
            product = data['modelCode'].split("\n")[0]

        if "osVersion" in data:
            build = data['osVersion']['train'].split("\n")[0]

        if err == "" or build == "" or product == "":
            return
        string = f"{err}\n{triage}"

        await msg.reply(f"`{discord.utils.escape_markdown(build)}` on a `{discord.utils.escape_markdown(product)}`!\n\n```{discord.utils.escape_markdown(string)}```")


async def parse_log(file: discord.Attachment, msg: discord.Message):
    if file.filename.startswith('panic-full'):
        await parse_panic(file, msg)
    elif file.filename.startswith('acceleratortroll'):
        await parse_crash(file, msg)
    else:
        await msg.reply('Only send logs that start with `acceleratortroll` or `panic-full` please!')
        await msg.delete()
    pass

@client.event
async def on_message(message: discord.Message):
    if message.author == client.user:
        return

    for attach in message.attachments:
        if attach.filename.endswith('.ips'):
            await parse_log(attach, message)

    if message.content.startswith('$scan'):
        if message.reference is not None:
            msg = await message.channel.fetch_message(message.reference.message_id)
            await message.delete()
            for attach in msg.attachments:
                if attach.filename.endswith('.ips'):
                    await parse_log(attach, msg)

client.run(os.environ.get('DISCORD_BOT_TOKEN'))
