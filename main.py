
import os, re, discord, asyncio, psycopg2, time, random, json
from discord.ext.commands.cooldowns import BucketType
from dateutil.relativedelta import relativedelta as rd
from datetime import datetime as dt
from discord.ext import commands
from discord.utils import get
from io import BytesIO
from PIL import Image

bot = commands.Bot(command_prefix = '+', intents = discord.Intents.all())
bot.remove_command('help')

database = psycopg2.connect(' '.join(['%s=%s' % (i, os.environ[i]) for i in ('host', 'port', 'dbname', 'user', 'password')]))
db = database.cursor()
database.autocommit = True

@bot.command()
async def say(ctx, *, message):
    db.execute("SELECT id FROM admins")
    if ctx.message.author.id in [i[0] for i in db.fetchall()]:
        await ctx.message.delete()
        await ctx.send(message)

@bot.command()
async def status(ctx, availability, *, activity):
    db.execute("SELECT id FROM admins")
    if ctx.message.author.id in [i[0] for i in db.fetchall()]:
        availabilities = {
            'invisible' : ('0', discord.Status.invisible),
            'online' : ('1', discord.Status.online),
            'idle' : ('2', discord.Status.idle),
            'dnd' : ('3', discord.Status.dnd),
        }
        await bot.change_presence(status = availabilities[availability.lower()][1], activity = discord.Game(name = activity))
        db.execute("UPDATE status SET availability = %s, activity = '%s'" % (availabilities[availability.lower()][0], re.sub("'", "''", activity)))
        await ctx.message.add_reaction(emoji = '✅')

@bot.command()
async def admin(ctx, option, member : discord.Member):
    if ctx.message.author.id in (264028228925128704, 589045072587128842, 333742519122788372):
        if option.lower() == 'add':
            db.execute("INSERT INTO admins VALUES (%s)" % str(member.id))
            await ctx.message.add_reaction(emoji = '✅')
        elif option.lower() in ('remove', 'rm') and member.id != ctx.message.author.id:
            db.execute("DELETE FROM admins WHERE id = %s" % str(member.id))
            await ctx.message.add_reaction(emoji = '✅')
        else:
            await ctx.message.add_reaction(emoji = '❌')
    else:
        await ctx.message.add_reaction(emoji = '❌')

@bot.command()
async def ping(ctx):
    db.execute("SELECT id FROM admins")
    if ctx.message.channel.id == 774879269791858689 or ctx.message.author.id in [i[0] for i in db.fetchall()]:
        cmdstart = time.monotonic()
        message = await ctx.send("**Ping-time:**")
        ping = '%.2f' % (float(time.monotonic() - cmdstart) * 1000)
        await message.edit(content = "**Ping-time:** `%s milliseconds`" % str(ping))

@bot.command(aliases = ['8ball'])
async def _8ball(ctx, *, question):
    db.execute("SELECT id FROM admins")
    if ctx.message.channel.id == 774879269791858689 or ctx.message.author.id in [i[0] for i in db.fetchall()]:
        foundation = Image.new('RGBA', (2007, 2006), (0, 0, 0, 0))
        answer = Image.open(r'./images/magic8ball/%s.png' % str(random.randint(0, 19)))
        magicball = Image.open(r'./images/magic8ball/stencil.png')
        foundation.paste(magicball, (0, 0))
        foundation.paste(answer, (635, 788), mask = answer)
        imgfileObj = BytesIO()
        foundation.save(imgfileObj, format = 'png')
        imgfileObj.seek(0)
        await ctx.send(file = discord.File(BytesIO(imgfileObj.read()), filename = 'magic8ball.png'))

@bot.command()
async def avatar(ctx, member : discord.Member = None):
    db.execute("SELECT id FROM admins")
    if ctx.message.channel.id == 774879269791858689 or ctx.message.author.id in [i[0] for i in db.fetchall()]:
        member = ctx.message.author if member is None else member
        embed = discord.Embed(color = member.color)
        embed.set_image(url = member.avatar_url)
        embed.set_footer(text = 'Executed by %s [%s]' % (str(ctx.message.author), str(ctx.message.author.id)))
        await ctx.message.add_reaction(emoji = '✅')
        await ctx.send(embed = embed)

@bot.command()
async def test(ctx):
    member = ctx.message.author
    await ctx.message.delete()
    created_at, delta = member.created_at.strftime('%d %b %Y'), rd(dt.today(), member.created_at)
    datevalues = []
    for t in ((delta.years, 'year(s)'), (delta.months, 'month(s)'), (delta.years, 'day(s)')):
        if t[0] > 0:
            datevalues.append('%s %s' % (str(t[0]), t[1]))
    info = '**Created Account On: `%s`**\n**Account Age: `%s`**' % (created_at, ', '.join(datevalues))
    await ctx.send(info, delete_after = 20)

@bot.listen()
async def on_member_join(member):
    if member.guild.id == 774876477073391646:
        guild = member.guild
        logchannel = guild.get_channel(826633624413405184)
        db.execute("SELECT id FROM muted")
        if member.id in [int(i[0]) for i in db.fetchall()]:
            muted = discord.utils.get(guild.roles, id = 775041899408130079)
            await member.add_roles(muted)
            embed = discord.Embed(color = 0xd68307)
            embed.set_author(name = 'Mute-Evasion Attempt', icon_url = 'http://assets.stickpng.com/images/5a81af7d9123fa7bcc9b0793.png')
            embed.set_thumbnail(url = member.avatar_url)
            created_at, delta = member.created_at.strftime('%d %b %Y'), rd(dt.today(), member.created_at)
            datevalues = []
            #for t in ((delta.days, 'day(s)'), (delta.months, 'month(s)'), (delta.years, 'year(s)')):
            for t in ((delta.years, 'year(s)'), (delta.months, 'month(s)'), (delta.years, 'day(s)')):
                if t[0] > 0:
                    datevalues.append('%s %s' % (str(t[0]), t[1]))
            embed.add_field(name = 'User Information', value = '**Discord-Tag:** %s\n\n**User-ID:** %s\n\n**Created Account On: `%s`**\n**Account Age: `%s`**' % (str(member), str(member.id), created_at, ', '.join(datevalues)), inline = False)
            await logchannel.send(embed = embed)
        db.execute("SELECT id FROM pending")
        if member.id in [i[0] for i in db.fetchall()]:
            pending = discord.utils.get(guild.roles, id = 825157846369828924)
            await member.add_roles(pending)

@bot.listen()
async def on_member_update(before, after):
    guild, member, br, ar = after.guild, after, [i.name for i in before.roles], [i.name for i in after.roles]
    verified, muted = (discord.utils.get(guild.roles, id = roleid) for roleid in (774902910965252117, 775041899408130079))
    logchannel = guild.get_channel(826633624413405184)
    if before.roles != after.roles:
        if muted.name not in br and muted.name in ar:
            db.execute("INSERT INTO muted VALUES ('%s', %s)" % (hex(int(time.time())).lstrip('0x'), str(member.id)))
            embed = discord.Embed(color = 0xf1d307)
            embed.set_author(name = 'User Muted', icon_url = 'https://cdn.iconscout.com/icon/free/png-512/muted-2090604-1770124.png')
            embed.set_thumbnail(url = member.avatar_url)
            created_at, delta = member.created_at.strftime('%d %b %Y'), rd(dt.today(), member.created_at)
            datevalues = []
            for t in ((delta.years, 'year(s)'), (delta.months, 'month(s)'), (delta.days, 'day(s)')):
                if t[0] > 0:
                    datevalues.append('%s %s' % (str(t[0]), t[1]))
            embed.add_field(name = 'User Information', value = '**Discord-Tag:** %s\n\n**User-ID:** %s\n\n**Created Account On: `%s`**\n**Account Age: `%s`**' % (str(member), str(member.id), created_at, ', '.join(datevalues)), inline = False)
            await logchannel.send(embed = embed)
        elif muted.name in br and muted.name not in ar:
            db.execute("DELETE FROM muted WHERE id = %s" % str(member.id))
            embed = discord.Embed(color = 0xf1d307)
            embed.set_author(name = 'User Unmuted', icon_url = 'https://cdn1.iconfinder.com/data/icons/modern-universal/32/icon-39-512.png')
            embed.set_thumbnail(url = member.avatar_url)
            created_at, delta = member.created_at.strftime('%d %b %Y'), rd(dt.today(), member.created_at)
            datevalues = []
            for t in ((delta.years, 'year(s)'), (delta.months, 'month(s)'), (delta.days, 'day(s)')):
                if t[0] > 0:
                    datevalues.append('%s %s' % (str(t[0]), t[1]))
            embed.add_field(name = 'User Information', value = '**Discord-Tag:** %s\n\n**User-ID:** %s\n\n**Created Account On: `%s`**\n**Account Age: `%s`**' % (str(member), str(member.id), created_at, ', '.join(datevalues)), inline = False)
            await logchannel.send(embed = embed)

@bot.listen()
async def on_message(message):
    if not message.author.bot:
        guild, channel, member, stamp = bot.get_guild(774876477073391646), message.channel, message.author, dt.today()
        guildname, pendingapprovals, logchannel = guild.name, guild.get_channel(825151607289020477), guild.get_channel(825151639534305320)
        if channel.id == 825151429827756042:
            timestamp, bio = hex(int(time.time())).lstrip('0x'), str(message.content)
            await message.delete()
            try:
                embed = discord.Embed(color = 0xfffff)
                embed.set_author(name = 'Welcome to "%s", %s!' % (guildname, member.name), icon_url = member.avatar_url)
                embed.set_thumbnail(url = guild.icon_url)
                embed.description = 'You\'ve successfully submitted your intro/biography. Please be patient while your submission is reviewed and your access is decided on. While you wait, please feel free to review the #rules channel so that the overall user experience of members is at its best.\n\nIf your submission is denied, I will DM you again as to the reason, so that you may make appropriate changes to your original submission and try again.'
                await member.send(embed = embed)
            except discord.errors.Forbidden:
                print('Can\'t DM user. Forbidden.')
            embed = discord.Embed(color = 0xfffff)
            embed.set_thumbnail(url = member.avatar_url)
            embed.set_author(name = 'Verification Approval', icon_url = guild.icon_url)
            created_at, delta = member.created_at.strftime('%d %b %Y'), rd(dt.today(), member.created_at)
            datevalues = []
            for t in ((delta.years, 'year(s)'), (delta.months, 'month(s)'), (delta.days, 'day(s)')):
                if t[0] > 0:
                    datevalues.append('%s %s' % (str(t[0]), t[1]))
            embed.description = '**Discord-Tag:** %s\n\n**User-ID:** %s\n\n**Created Account On: `%s`**\n**Account Age: `%s`**' % (str(member), str(member.id), created_at, ', '.join(datevalues))
            embed.add_field(name = 'Biography', value = bio, inline = False)
            db.execute("INSERT INTO pending VALUES ('%s', %s, '%s')" % (timestamp, str(member.id), re.sub("'", "''", bio)))
            pendingapprovals = await pendingapprovals.send(embed = embed)
            pendingrole = discord.utils.get(guild.roles, id = 825157846369828924)
            await member.add_roles(pendingrole)
            for emoji in ('🔼','⏺️', '🔽', '✅', '⛔', '❓'):
                await pendingapprovals.add_reaction(emoji = emoji)
        elif channel.id == 825151607289020477:
            messages = await channel.history(limit=100).flatten()
            reason, matches = None, []
            for msg in messages:
                if msg.author.bot:
                    if int(msg.embeds[0].footer.text.split('[')[1][:-1]) == member.id:
                        reason = message.content
                        user = guild.get_member(int(str(msg.embeds[0].thumbnail.url).split('/')[4]))
                        db.execute("SELECT bio FROM pending WHERE id = %s" % str(user.id))
                        bio = db.fetchone()[0]
                        db.execute("INSERT INTO denied SELECT ts, %s, id, bio, '%s' FROM pending WHERE id = %s" % (str(member.id), re.sub("'", "''", reason), str(user.id)))
                        db.execute("DELETE FROM pending WHERE id = %s" % str(user.id))
                        await msg.delete()
                        await message.delete()
                        embed = discord.Embed(color = 0xff0000)
                        embed.set_author(name = 'Denied', icon_url = 'https://uxwing.com/wp-content/themes/uxwing/download/01-user_interface/red-x.png')
                        embed.set_thumbnail(url = user.avatar_url)
                        embed.set_footer(text = 'Denied by %s [%s]' % (str(member), str(member.id)))
                        created_at, delta = str(user.created_at).split(' ')[0], rd(dt.today(), user.created_at)
                        datevalues = []
                        for t in ((delta.years, 'year(s)'), (delta.months, 'month(s)'), (delta.days, 'day(s)')):
                            if t[0] > 0:
                                datevalues.append('%s %s' % (str(t[0]), t[1]))
                        embed.add_field(name = 'User Information', value = '**Discord-Tag:** %s\n\n**User-ID:** %s\n\n**Created Account On: `%s`**\n**Account Age: `%s`**' % (str(user), str(user.id), created_at, ', '.join(datevalues)), inline = False)
                        embed.add_field(name = 'Biography', value = bio, inline = False)
                        embed.add_field(name = 'Reason', value = reason, inline = False)
                        await logchannel.send(embed = embed)
                        pendingrole = discord.utils.get(guild.roles, id = 825157846369828924)
                        await user.remove_roles(pendingrole)
                        try:
                            embed = discord.Embed(color = 0xff0000)
                            embed.set_author(name = 'Denied', icon_url = 'https://uxwing.com/wp-content/themes/uxwing/download/01-user_interface/red-x.png')
                            embed.set_thumbnail(url = user.avatar_url)
                            embed.set_footer(text = 'Denied by %s [%s]' % (str(member), str(member.id)))
                            embed.description = 'I\'m sorry, but it seems that the intro/biography that you shared in the #welcome channel was denied.\n\nThe reason for the denial is shared under your intro/biography (below).\n\nIf you have any questions, feel free to DM a mod/admin.\n\nThank you.'
                            embed.add_field(name = 'Biography', value = bio, inline = False)
                            embed.add_field(name = 'Reason', value = reason, inline = False)
                            await user.send(embed = embed)
                        except discord.errors.Forbidden:
                            print('cannot DM user')

@bot.listen()
async def on_raw_reaction_add(payload):
    member = payload.member
    if not member.bot:
        guild = bot.get_guild(payload.guild_id)
        channel = guild.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        logchannel = guild.get_channel(825151639534305320)
        if message.embeds:
            emoji = str(payload.emoji)
            embedcontent = message.embeds[0]
            if embedcontent.author.name == 'Verification Approval':
                user = guild.get_member(int(embedcontent.description.split('\n')[2].split(' ')[1]))
                reactions = {
                    '✅' : 'approve',
                    '⛔' : 'reason',
                    '❓' : 'invalidtemplate'
                }
                if emoji in reactions.keys():
                    reaction = reactions[emoji]
                    db.execute("SELECT bio FROM pending WHERE id = %s" % str(user.id))
                    bio = db.fetchone()[0]
                    if reaction == 'approve':
                        await message.clear_reactions()
                        db.execute("INSERT INTO approved SELECT ts, %s, id, bio FROM pending WHERE id = %s" % (str(member.id), str(user.id)))
                        db.execute("DELETE FROM pending WHERE id = %s" % str(user.id))
                        await user.add_roles(discord.utils.get(guild.roles, id = 774902910965252117))
                        await user.remove_roles(discord.utils.get(guild.roles, id = 825157846369828924))
                        embed = discord.Embed(description = '%s has approved the user and the\n <@&774902910965252117> role has been assigned automatically.' % member.mention, color = 0x32cd32)
                        embed.set_author(name = 'Approved!', icon_url = 'https://www.dropboxforum.com/html/@2FF45D5FC6BE1C0209A83783F899B497/images/emoticons/2705.png')
                        await message.edit(embed = embed, delete_after = 30)
                        embed = discord.Embed(color = 0x32cd32)
                        embed.set_footer(text = 'Approved by %s [%s]' % (str(member), str(member.id)))
                        embed.set_author(name = 'Approved', icon_url = 'https://www.dropboxforum.com/html/@2FF45D5FC6BE1C0209A83783F899B497/images/emoticons/2705.png')
                        embed.set_thumbnail(url = user.avatar_url)
                        created_at, delta = str(user.created_at).split(' ')[0], rd(dt.today(), user.created_at)
                        datevalues = []
                        for t in ((delta.years, 'year(s)'), (delta.months, 'month(s)'), (delta.days, 'day(s)')):
                            if t[0] > 0:
                                datevalues.append('%s %s' % (str(t[0]), t[1]))
                        embed.add_field(name = 'User Information', value = '**Discord-Tag:** %s\n\n**User-ID:** %s\n\n**Created Account On: `%s`**\n**Account Age: `%s`**' % (str(user), str(user.id), created_at, ', '.join(datevalues)), inline = False)
                        embed.add_field(name = 'Biography', value = bio, inline = False)
                        await logchannel.send(embed = embed)
                        try:
                            embed = discord.Embed(color = 0x32cd32)
                            embed.set_thumbnail(url = user.avatar_url)
                            embed.set_author(name = 'Access Granted!', icon_url = '')
                            embed.set_footer(text = 'Approved by %s [%s]' % (str(member), str(member.id)))
                            embed.add_field(name = 'Biography', value = bio, inline = False)
                            await user.send(embed = embed)
                        except discord.errors.Forbidden:
                            print('cannot DM user')
                    elif reaction == 'invalidtemplate':
                        embed = discord.Embed(color = 0xff0000)
                        embed.set_author(name = 'Denied', icon_url = 'https://uxwing.com/wp-content/themes/uxwing/download/01-user_interface/red-x.png')
                        embed.set_footer(text = 'Denied by %s [%s]' % (str(member), str(member.id)))
                        embed.set_thumbnail(url = user.avatar_url)
                        try:
                            embed.add_field(name = 'Biography', value = bio, inline = False)
                            embed.add_field(name = 'Reason', value = 'The intro/biography does not match the template that was provided in the #welcome channel. Please give it another try. Perhaps it\'d help to reword and/or rephrase a few things. Appending additional detailed information also tends to be helpful! Thank you.', inline = False)
                            await user.send(embed = embed)
                        except discord.errors.Forbidden:
                            embed.set_author(name = 'Forbidden Access Alert', icon_url = member.avatar_url)
                            embed.set_thumbnail(url = 'https://uxwing.com/wp-content/themes/uxwing/download/01-user_interface/red-x.png')
                            embed.description = 'It seems that the user\'s privacy settings are restricting me from contacting them via DMs. Please contact them directly if you would like to provide them with specific information. I have re-granted them write-access to the <#825151429827756042> channel before ghost-pinging them there as well, so that they may try again.\n\n**Please react to this message with the :ok: emoji once you\'ve read & understood it.\n\nThank you.'
                            await message.clear_reactions()
                            await message.edit(embed = embed)
                            await message.add_reaction(emoji = '🆗')
                            ghostping = await guild.get_channel(825151429827756042).send(user.mention)
                            await ghostping.delete()
                        await user.remove_roles(discord.utils.get(guild.roles, id = 825157846369828924)) # unlocked #welcome channel
                        embed = discord.Embed(color = 0xff0000)
                        embed.set_author(name = 'Denied', icon_url = 'https://uxwing.com/wp-content/themes/uxwing/download/01-user_interface/red-x.png')
                        embed.set_footer(text = 'Denied by %s [%s]' % (str(member), str(member.id)))
                        embed.set_thumbnail(url = user.avatar_url)
                        created_at, delta = str(user.created_at).split(' ')[0], rd(dt.today(), user.created_at)
                        datevalues = []
                        for t in ((delta.years, 'year(s)'), (delta.months, 'month(s)'), (delta.days, 'day(s)')):
                            if t[0] > 0:
                                datevalues.append('%s %s' % (str(t[0]), t[1]))
                        embed.add_field(name = 'User Information', value = '**Discord-Tag:** %s\n\n**User-ID:** %s\n\n**Created Account On: `%s`**\n**Account Age: `%s`**' % (str(user), str(user.id), created_at, ', '.join(datevalues)), inline = False)
                        embed.add_field(name = 'Biography', value = bio, inline = False)
                        embed.add_field(name = 'Reason', value = 'The intro/biography does not match the template that was provided in the #welcome channel.', inline = False)
                        db.execute("INSERT INTO denied SELECT ts, %s, id, bio, 'invalid template' FROM pending WHERE id = %s" % (str(member.id), str(user.id)))
                        db.execute("DELETE FROM pending WHERE id = %s" % str(user.id))
                        await logchannel.send(embed = embed)
                        embed = discord.Embed(color = 0xff0000)
                        embed.set_author(name = 'Denied', icon_url = 'https://uxwing.com/wp-content/themes/uxwing/download/01-user_interface/red-x.png')
                        embed.set_thumbnail(url = user.avatar_url)
                        embed.set_footer(text = 'Denied by %s [%s]' % (str(member), str(member.id)))
                        embed.description = 'You have chosen to deny %s\'s access to the server due to the user not abiding by the template.' % str(user)
                        await message.clear_reactions()
                        await message.edit(embed = embed, delete_after = 30)
                        await message.clear_reactions()
                    elif reaction == 'reason':
                        embed = discord.Embed(color = 0xff0000)
                        embed.set_author(name = 'Denied', icon_url = 'https://uxwing.com/wp-content/themes/uxwing/download/01-user_interface/red-x.png')
                        embed.set_thumbnail(url = user.avatar_url)
                        embed.set_footer(text = 'Denied by %s [%s]' % (str(member), str(member.id)))
                        embed.description = 'You have chosen to deny %s\'s access to the server.\n\n**Please provide details regarding the reason for this user being denied access.**' % str(user)
                        await message.clear_reactions()
                        await message.edit(embed = embed)             

@bot.event
async def on_ready():
    availabilities = {
        0 : discord.Status.invisible,
        1 : discord.Status.online,
        2 : discord.Status.idle,
        3 : discord.Status.dnd,
    }
    db.execute("SELECT availability, activity FROM status")
    availability, activity = db.fetchone()
    await bot.change_presence(status = availabilities[availability], activity = discord.Game(name = activity))
    print('Chester Bot ONLINE!')


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.create_task(bot.start(os.environ['token']))
    loop.run_forever()
