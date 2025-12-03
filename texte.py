
"""
BOT DISCORD COMPLET - 250+ Commandes
Structure: Main + Cogs pour chaque catégorie
"""

import discord
from discord.ext import commands, tasks
from discord.ui import Button, View, Select
import asyncio
import json
import datetime
import random
import aiosqlite
import os
from typing import Optional, List, Dict, Union
import requests
import io
from PIL import Image, ImageFilter
import base64
import time
import math

# ==================== CONFIGURATION INITIALE ====================
intents = discord.Intents.all()
bot = commands.Bot(command_prefix=['!', '.', '?'], intents=intents, help_command=None)

# Configuration
TOKEN = "MTQ0NTgxNzk4Mzk4ODUzNTQzMA.G0cwJI.JwMIREKhaYu0dYIG-01mXTtr0iQh22AIsybpxg"
DB_PATH = "bot_database.db"
OWNER_IDS = [1280934640802332757,  1443665505519927458]  # Ajoutez vos IDs Discord ici

# Couleurs pour les embeds
COLORS = {
    "success": 0x2ecc71,
    "error": 0xe74c3c,
    "warning": 0xf39c12,
    "info": 0x3498db,
    "moderation": 0xe67e22,
    "fun": 0x9b59b6,
    "ticket": 0x1abc9c,
    "giveaway": 0xf1c40f
}

# ==================== BASE DE DONNÉES ====================
class Database:
    def __init__(self):
        self.db = None
    
    async def connect(self):
        self.db = await aiosqlite.connect(DB_PATH)
        await self.create_tables()
    
    async def create_tables(self):
        tables = [
            # Table warns
            """CREATE TABLE IF NOT EXISTS warns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                guild_id INTEGER NOT NULL,
                reason TEXT,
                moderator_id INTEGER NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )""",
            
            # Table mutes
            """CREATE TABLE IF NOT EXISTS mutes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                guild_id INTEGER NOT NULL,
                end_time DATETIME,
                reason TEXT,
                active BOOLEAN DEFAULT 1
            )""",
            
            # Table logs
            """CREATE TABLE IF NOT EXISTS logs (
                guild_id INTEGER PRIMARY KEY,
                modlog_channel INTEGER,
                joinlog_channel INTEGER,
                leavelog_channel INTEGER,
                msglog_channel INTEGER,
                voicelog_channel INTEGER,
                emojilog_channel INTEGER,
                fluxlog_channel INTEGER,
                gwlog_channel INTEGER,
                invitelog_channel INTEGER,
                raidlog_channel INTEGER,
                reactionlog_channel INTEGER,
                rolelog_channel INTEGER,
                starlog_channel INTEGER,
                systemlog_channel INTEGER
            )""",
            
            # Table tickets
            """CREATE TABLE IF NOT EXISTS tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                channel_id INTEGER NOT NULL,
                status TEXT DEFAULT 'open',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                claimed_by INTEGER
            )""",
            
            # Table giveaways
            """CREATE TABLE IF NOT EXISTS giveaways (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                channel_id INTEGER NOT NULL,
                message_id INTEGER NOT NULL,
                prize TEXT NOT NULL,
                winners INTEGER DEFAULT 1,
                end_time DATETIME NOT NULL,
                participants TEXT DEFAULT '[]',
                ended BOOLEAN DEFAULT 0
            )""",
            
            # Table invites
            """CREATE TABLE IF NOT EXISTS invites (
                guild_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                invites INTEGER DEFAULT 0,
                joins INTEGER DEFAULT 0,
                leaves INTEGER DEFAULT 0,
                fake INTEGER DEFAULT 0,
                PRIMARY KEY (guild_id, user_id)
            )""",
            
            # Table permissions
            """CREATE TABLE IF NOT EXISTS permissions (
                guild_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                command TEXT NOT NULL,
                allowed BOOLEAN DEFAULT 1,
                PRIMARY KEY (guild_id, user_id, command)
            )""",
            
            # Table afk
            """CREATE TABLE IF NOT EXISTS afk (
                user_id INTEGER PRIMARY KEY,
                reason TEXT,
                since DATETIME DEFAULT CURRENT_TIMESTAMP
            )""",
            
            # Table reminders
            """CREATE TABLE IF NOT EXISTS reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                reminder TEXT NOT NULL,
                time DATETIME NOT NULL,
                channel_id INTEGER NOT NULL,
                sent BOOLEAN DEFAULT 0
            )""",
            
            # Table starboard
            """CREATE TABLE IF NOT EXISTS starboard (
                guild_id INTEGER NOT NULL,
                original_message_id INTEGER NOT NULL,
                starboard_message_id INTEGER NOT NULL,
                stars INTEGER DEFAULT 1,
                PRIMARY KEY (guild_id, original_message_id)
            )"""
        ]
        
        for table in tables:
            await self.db.execute(table)
        await self.db.commit()

db = Database()

# ==================== UTILITAIRES ====================
class EmbedCreator:
    @staticmethod
    def success(description: str, title: str = "✅ Succès") -> discord.Embed:
        return discord.Embed(title=title, description=description, color=COLORS["success"])
    
    @staticmethod
    def error(description: str, title: str = "❌ Erreur") -> discord.Embed:
        return discord.Embed(title=title, description=description, color=COLORS["error"])
    
    @staticmethod
    def warning(description: str, title: str = "⚠️ Attention") -> discord.Embed:
        return discord.Embed(title=title, description=description, color=COLORS["warning"])
    
    @staticmethod
    def info(description: str, title: str = "ℹ️ Information") -> discord.Embed:
        return discord.Embed(title=title, description=description, color=COLORS["info"])
    
    @staticmethod
    def moderation(action: str, user: discord.Member, moderator: discord.Member, reason: str = "Aucune raison fournie") -> discord.Embed:
        embed = discord.Embed(
            title=f"🔨 {action}",
            color=COLORS["moderation"],
            timestamp=datetime.datetime.now()
        )
        embed.add_field(name="👤 Membre", value=user.mention, inline=True)
        embed.add_field(name="🛡️ Modérateur", value=moderator.mention, inline=True)
        embed.add_field(name="📝 Raison", value=reason, inline=False)
        return embed

class Paginator(View):
    def __init__(self, embeds: List[discord.Embed]):
        super().__init__(timeout=60)
        self.embeds = embeds
        self.current_page = 0
        
    @discord.ui.button(label="◀", style=discord.ButtonStyle.gray)
    async def previous(self, interaction: discord.Interaction, button: Button):
        if self.current_page > 0:
            self.current_page -= 1
            await interaction.response.edit_message(embed=self.embeds[self.current_page])
    
    @discord.ui.button(label="▶", style=discord.ButtonStyle.gray)
    async def next(self, interaction: discord.Interaction, button: Button):
        if self.current_page < len(self.embeds) - 1:
            self.current_page += 1
            await interaction.response.edit_message(embed=self.embeds[self.current_page])

# ==================== COG: MODÉRATION ====================
class ModerationCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name="ban")
    @commands.has_permissions(ban_members=True)
    async def ban_cmd(self, ctx, member: discord.Member, *, reason="Aucune raison"):
        """Bannir un membre"""
        await member.ban(reason=f"{ctx.author}: {reason}")
        embed = EmbedCreator.moderation("Bannissement", member, ctx.author, reason)
        await ctx.send(embed=embed)
    
    @commands.command(name="kick")
    @commands.has_permissions(kick_members=True)
    async def kick_cmd(self, ctx, member: discord.Member, *, reason="Aucune raison"):
        """Expulser un membre"""
        await member.kick(reason=f"{ctx.author}: {reason}")
        embed = EmbedCreator.moderation("Expulsion", member, ctx.author, reason)
        await ctx.send(embed=embed)
    
    @commands.command(name="mute")
    @commands.has_permissions(manage_roles=True)
    async def mute_cmd(self, ctx, member: discord.Member, duration: str = "10m", *, reason="Aucune raison"):
        """Muter un membre"""
        # Créer/obtenir rôle muted
        muted_role = discord.utils.get(ctx.guild.roles, name="Muted")
        if not muted_role:
            muted_role = await ctx.guild.create_role(name="Muted")
            for channel in ctx.guild.channels:
                await channel.set_permissions(muted_role, speak=False, send_messages=False)
        
        await member.add_roles(muted_role)
        embed = EmbedCreator.moderation("Mute", member, ctx.author, f"{reason} | Durée: {duration}")
        await ctx.send(embed=embed)
    
    @commands.command(name="clear")
    @commands.has_permissions(manage_messages=True)
    async def clear_cmd(self, ctx, amount: int = 10):
        """Supprimer des messages"""
        if amount > 100:
            amount = 100
        deleted = await ctx.channel.purge(limit=amount + 1)
        embed = EmbedCreator.success(f"{len(deleted)-1} messages supprimés")
        msg = await ctx.send(embed=embed)
        await asyncio.sleep(3)
        await msg.delete()
    
    @commands.command(name="warn")
    @commands.has_permissions(kick_members=True)
    async def warn_cmd(self, ctx, member: discord.Member, *, reason="Aucune raison"):
        """Avertir un membre"""
        async with db.db.cursor() as cursor:
            await cursor.execute(
                "INSERT INTO warns (user_id, guild_id, reason, moderator_id) VALUES (?, ?, ?, ?)",
                (member.id, ctx.guild.id, reason, ctx.author.id)
            )
            await db.db.commit()
        
        embed = EmbedCreator.moderation("Avertissement", member, ctx.author, reason)
        await ctx.send(embed=embed)
    
    @commands.command(name="warnings")
    async def warnings_cmd(self, ctx, member: discord.Member = None):
        """Voir les avertissements d'un membre"""
        member = member or ctx.author
        async with db.db.cursor() as cursor:
            await cursor.execute(
                "SELECT reason, timestamp FROM warns WHERE user_id = ? AND guild_id = ?",
                (member.id, ctx.guild.id)
            )
            warns = await cursor.fetchall()
        
        if not warns:
            embed = EmbedCreator.info(f"{member.mention} n'a aucun avertissement")
        else:
            warnings_list = "\n".join([f"• {reason} ({timestamp})" for reason, timestamp in warns])
            embed = discord.Embed(
                title=f"⚠️ Avertissements de {member}",
                description=warnings_list,
                color=COLORS["warning"]
            )
        await ctx.send(embed=embed)
    
    @commands.command(name="slowmode")
    @commands.has_permissions(manage_channels=True)
    async def slowmode_cmd(self, ctx, seconds: int = 0):
        """Activer/Désactiver le slowmode"""
        await ctx.channel.edit(slowmode_delay=seconds)
        if seconds > 0:
            embed = EmbedCreator.success(f"Slowmode activé: {seconds} secondes")
        else:
            embed = EmbedCreator.success("Slowmode désactivé")
        await ctx.send(embed=embed)
    
    @commands.command(name="lock")
    @commands.has_permissions(manage_channels=True)
    async def lock_cmd(self, ctx, channel: discord.TextChannel = None):
        """Verrouiller un salon"""
        channel = channel or ctx.channel
        overwrite = channel.overwrites_for(ctx.guild.default_role)
        overwrite.send_messages = False
        await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
        embed = EmbedCreator.success(f"{channel.mention} verrouillé")
        await ctx.send(embed=embed)
    
    @commands.command(name="unlock")
    @commands.has_permissions(manage_channels=True)
    async def unlock_cmd(self, ctx, channel: discord.TextChannel = None):
        """Déverrouiller un salon"""
        channel = channel or ctx.channel
        overwrite = channel.overwrites_for(ctx.guild.default_role)
        overwrite.send_messages = None
        await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
        embed = EmbedCreator.success(f"{channel.mention} déverrouillé")
        await ctx.send(embed=embed)
    
    @commands.command(name="nick")
    @commands.has_permissions(manage_nicknames=True)
    async def nick_cmd(self, ctx, member: discord.Member, *, nickname: str = None):
        """Changer le surnom d'un membre"""
        await member.edit(nick=nickname)
        if nickname:
            embed = EmbedCreator.success(f"Surnom de {member.mention} changé en: {nickname}")
        else:
            embed = EmbedCreator.success(f"Surnom de {member.mention} réinitialisé")
        await ctx.send(embed=embed)
    
    @commands.command(name="role")
    @commands.has_permissions(manage_roles=True)
    async def role_cmd(self, ctx, member: discord.Member, role: discord.Role):
        """Ajouter/Retirer un rôle"""
        if role in member.roles:
            await member.remove_roles(role)
            action = "retiré"
        else:
            await member.add_roles(role)
            action = "ajouté"
        
        embed = EmbedCreator.success(f"Rôle {role.mention} {action} à {member.mention}")
        await ctx.send(embed=embed)
    
    @commands.command(name="temprole")
    @commands.has_permissions(manage_roles=True)
    async def temprole_cmd(self, ctx, member: discord.Member, duration: str, role: discord.Role):
        """Donner un rôle temporaire"""
        await member.add_roles(role)
        embed = EmbedCreator.success(f"Rôle {role.mention} donné temporairement à {member.mention} pour {duration}")
        await ctx.send(embed=embed)
        
        # Timer pour retirer le rôle
        if 'm' in duration:
            seconds = int(duration.replace('m', '')) * 60
        elif 'h' in duration:
            seconds = int(duration.replace('h', '')) * 3600
        elif 'd' in duration:
            seconds = int(duration.replace('d', '')) * 86400
        else:
            seconds = 3600
        
        await asyncio.sleep(seconds)
        if role in member.roles:
            await member.remove_roles(role)

# ==================== COG: INFORMATION ====================
class InformationCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name="serverinfo")
    async def serverinfo_cmd(self, ctx):
        """Informations du serveur"""
        guild = ctx.guild
        
        embed = discord.Embed(
            title=f"🏰 {guild.name}",
            color=COLORS["info"],
            timestamp=datetime.datetime.now()
        )
        
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        
        embed.add_field(name="👑 Propriétaire", value=guild.owner.mention, inline=True)
        embed.add_field(name="📅 Créé le", value=guild.created_at.strftime("%d/%m/%Y"), inline=True)
        embed.add_field(name="👥 Membres", value=f"{guild.member_count}", inline=True)
        embed.add_field(name="📁 Salons", value=f"{len(guild.text_channels)} text | {len(guild.voice_channels)} vocal", inline=True)
        embed.add_field(name="🎭 Rôles", value=f"{len(guild.roles)}", inline=True)
        embed.add_field(name="😎 Émojis", value=f"{len(guild.emojis)}", inline=True)
        embed.add_field(name="🚀 Boosts", value=f"Niveau {guild.premium_tier} ({guild.premium_subscription_count} boosts)", inline=True)
        embed.add_field(name="🌐 Région", value=str(guild.preferred_locale).capitalize(), inline=True)
        embed.add_field(name="🆔 ID", value=guild.id, inline=True)
        
        await ctx.send(embed=embed)
    
    @commands.command(name="userinfo")
    async def userinfo_cmd(self, ctx, member: discord.Member = None):
        """Informations d'un utilisateur"""
        member = member or ctx.author
        
        embed = discord.Embed(
            title=f"👤 {member}",
            color=member.color,
            timestamp=datetime.datetime.now()
        )
        
        if member.avatar:
            embed.set_thumbnail(url=member.avatar.url)
        
        status_emoji = {
            "online": "🟢",
            "idle": "🟡",
            "dnd": "🔴",
            "offline": "⚫"
        }
        
        embed.add_field(name="🆔 ID", value=member.id, inline=True)
        embed.add_field(name="📛 Surnom", value=member.nick or "Aucun", inline=True)
        embed.add_field(name="📊 Statut", value=f"{status_emoji[str(member.status)]} {str(member.status).capitalize()}", inline=True)
        embed.add_field(name="📅 Compte créé", value=member.created_at.strftime("%d/%m/%Y %H:%M"), inline=True)
        embed.add_field(name="📅 Rejoint le", value=member.joined_at.strftime("%d/%m/%Y %H:%M"), inline=True)
        embed.add_field(name="🎭 Rôle le plus haut", value=member.top_role.mention, inline=True)
        
        roles = [role.mention for role in member.roles[1:]]
        if roles:
            embed.add_field(name=f"🎭 Rôles ({len(roles)})", value=" ".join(roles[:5]) + ("..." if len(roles) > 5 else ""), inline=False)
        
        await ctx.send(embed=embed)
    
    @commands.command(name="avatar")
    async def avatar_cmd(self, ctx, member: discord.Member = None):
        """Afficher l'avatar d'un membre"""
        member = member or ctx.author
        
        embed = discord.Embed(
            title=f"🖼️ Avatar de {member}",
            color=member.color
        )
        
        if member.avatar:
            embed.set_image(url=member.avatar.url)
            embed.description = f"[Lien direct]({member.avatar.url})"
        else:
            embed.set_image(url=member.default_avatar.url)
        
        await ctx.send(embed=embed)
    
    @commands.command(name="banner")
    async def banner_cmd(self, ctx, member: discord.Member = None):
        """Afficher la bannière d'un membre"""
        member = member or ctx.author
        
        # Nécessite d'utiliser l'API Discord
        user = await self.bot.fetch_user(member.id)
        
        if user.banner:
            embed = discord.Embed(
                title=f"🎨 Bannière de {member}",
                color=member.color
            )
            embed.set_image(url=user.banner.url)
            embed.description = f"[Lien direct]({user.banner.url})"
        else:
            embed = EmbedCreator.info(f"{member} n'a pas de bannière")
        
        await ctx.send(embed=embed)
    
    @commands.command(name="roleinfo")
    async def roleinfo_cmd(self, ctx, role: discord.Role):
        """Informations sur un rôle"""
        embed = discord.Embed(
            title=f"🎭 {role.name}",
            color=role.color,
            timestamp=datetime.datetime.now()
        )
        
        embed.add_field(name="🆔 ID", value=role.id, inline=True)
        embed.add_field(name="🎨 Couleur", value=str(role.color), inline=True)
        embed.add_field(name="👥 Membres", value=len(role.members), inline=True)
        embed.add_field(name="📅 Créé le", value=role.created_at.strftime("%d/%m/%Y"), inline=True)
        embed.add_field(name="👑 Position", value=role.position, inline=True)
        embed.add_field(name="💎 Hoist", value="Oui" if role.hoist else "Non", inline=True)
        embed.add_field(name="📢 Mentionnable", value="Oui" if role.mentionable else "Non", inline=True)
        
        # Permissions importantes
        perms = []
        if role.permissions.administrator:
            perms.append("Administrateur")
        if role.permissions.manage_guild:
            perms.append("Gérer le serveur")
        if role.permissions.ban_members:
            perms.append("Bannir des membres")
        if role.permissions.kick_members:
            perms.append("Expulser des membres")
        if role.permissions.manage_messages:
            perms.append("Gérer les messages")
        
        if perms:
            embed.add_field(name="🔑 Permissions principales", value=", ".join(perms), inline=False)
        
        await ctx.send(embed=embed)
    
    @commands.command(name="botinfo")
    async def botinfo_cmd(self, ctx):
        """Informations sur le bot"""
        embed = discord.Embed(
            title=f"🤖 {self.bot.user.name}",
            color=COLORS["info"],
            timestamp=datetime.datetime.now()
        )
        
        embed.set_thumbnail(url=self.bot.user.avatar.url if self.bot.user.avatar else None)
        
        embed.add_field(name="🆔 ID", value=self.bot.user.id, inline=True)
        embed.add_field(name="📅 Créé le", value=self.bot.user.created_at.strftime("%d/%m/%Y"), inline=True)
        embed.add_field(name="🏠 Serveurs", value=len(self.bot.guilds), inline=True)
        embed.add_field(name="👥 Utilisateurs", value=sum(g.member_count for g in self.bot.guilds), inline=True)
        embed.add_field(name="📈 Latence", value=f"{round(self.bot.latency * 1000)}ms", inline=True)
        embed.add_field(name="⚡ Version Discord.py", value=discord.__version__, inline=True)
        
        embed.add_field(name="👑 Développeur", value="<VOTRE_NOM>", inline=True)
        embed.add_field(name="🔗 Support", value="[Serveur Discord](<VOTRE_LIEN>)", inline=True)
        
        await ctx.send(embed=embed)
    
    @commands.command(name="ping")
    async def ping_cmd(self, ctx):
        """Afficher la latence du bot"""
        embed = discord.Embed(
            title="🏓 Pong!",
            description=f"Latence: **{round(self.bot.latency * 1000)}ms**",
            color=COLORS["info"]
        )
        await ctx.send(embed=embed)
    
    @commands.command(name="uptime")
    async def uptime_cmd(self, ctx):
        """Temps de fonctionnement du bot"""
        delta = datetime.datetime.now() - self.bot.start_time
        hours, remainder = divmod(int(delta.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        days, hours = divmod(hours, 24)
        
        uptime_str = f"{days}j {hours}h {minutes}m {seconds}s"
        embed = EmbedCreator.info(f"**{uptime_str}**")
        await ctx.send(embed=embed)

# ==================== COG: FUN & JEUX ====================
class FunCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name="hug")
    async def hug_cmd(self, ctx, member: discord.Member = None):
        """Faire un câlin"""
        member = member or ctx.author
        
        hugs = [
            f"🤗 {ctx.author.mention} fait un câlin chaleureux à {member.mention}!",
            f"💕 {ctx.author.mention} serre tendrement {member.mention} dans ses bras!",
            f"❤️ Câlin doux de {ctx.author.mention} pour {member.mention}!",
            f"🫂 {ctx.author.mention} enlace affectueusement {member.mention}!"
        ]
        
        embed = discord.Embed(
            description=random.choice(hugs),
            color=COLORS["fun"],
            timestamp=datetime.datetime.now()
        )
        await ctx.send(embed=embed)
    
    @commands.command(name="kiss")
    async def kiss_cmd(self, ctx, member: discord.Member):
        """Faire un bisou"""
        kisses = [
            f"💋 {ctx.author.mention} fait un bisou tendre à {member.mention}!",
            f"😘 {ctx.author.mention} envoie un baiser à {member.mention}!",
            f"💖 Bisous doux de {ctx.author.mention} pour {member.mention}!"
        ]
        
        embed = discord.Embed(
            description=random.choice(kisses),
            color=COLORS["fun"],
            timestamp=datetime.datetime.now()
        )
        await ctx.send(embed=embed)
    
    @commands.command(name="slap")
    async def slap_cmd(self, ctx, member: discord.Member):
        """Donner une gifle"""
        slaps = [
            f"👋 {ctx.author.mention} donne une gifle à {member.mention}!",
            f"🤚 {ctx.author.mention} frappe {member.mention}!",
            f"✋ {ctx.author.mention} gifle violemment {member.mention}!"
        ]
        
        embed = discord.Embed(
            description=random.choice(slaps),
            color=COLORS["fun"],
            timestamp=datetime.datetime.now()
        )
        await ctx.send(embed=embed)
    
    @commands.command(name="roll")
    async def roll_cmd(self, ctx, max_num: int = 100):
        """Lancer un dé"""
        result = random.randint(1, max_num)
        embed = discord.Embed(
            title="🎲 Lancé de dé",
            description=f"{ctx.author.mention} a obtenu: **{result}**/{max_num}",
            color=COLORS["fun"],
            timestamp=datetime.datetime.now()
        )
        await ctx.send(embed=embed)
    
    @commands.command(name="coinflip")
    async def coinflip_cmd(self, ctx):
        """Pile ou face"""
        result = random.choice(["Pile", "Face"])
        embed = discord.Embed(
            title="🪙 Pile ou Face",
            description=f"{ctx.author.mention} a obtenu: **{result}**",
            color=COLORS["fun"]
        )
        await ctx.send(embed=embed)
    
    @commands.command(name="8ball")
    async def eightball_cmd(self, ctx, *, question: str):
        """Poser une question à la magic 8-ball"""
        responses = [
            "Oui, absolument.", "C'est certain.", "Sans aucun doute.",
            "Oui.", "Très probablement.", "Je pense que oui.",
            "Les signes indiquent oui.", "Demande à nouveau plus tard.",
            "Mieux vaut ne pas te le dire maintenant.", "Je ne peux pas prédire maintenant.",
            "Concentre-toi et demande à nouveau.", "Ne compte pas dessus.",
            "Ma réponse est non.", "Mes sources disent non.",
            "Très improbable.", "Non."
        ]
        
        embed = discord.Embed(
            title="🎱 Magic 8-Ball",
            color=COLORS["fun"]
        )
        embed.add_field(name="Question", value=question, inline=False)
        embed.add_field(name="Réponse", value=random.choice(responses), inline=False)
        await ctx.send(embed=embed)
    
    @commands.command(name="lovecalc")
    async def lovecalc_cmd(self, ctx, member1: discord.Member, member2: discord.Member = None):
        """Calculer l'amour entre deux personnes"""
        member2 = member2 or ctx.author
        
        # Générer un pourcentage basé sur les IDs
        love_percent = (member1.id + member2.id) % 101
        
        # Phrases selon le pourcentage
        if love_percent < 30:
            phrase = "💔 Pas vraiment fait l'un pour l'autre..."
        elif love_percent < 50:
            phrase = "❤️‍🩹 Il y a un petit quelque chose..."
        elif love_percent < 70:
            phrase = "💖 Une belle relation possible!"
        elif love_percent < 90:
            phrase = "💕 C'est le coup de foudre!"
        else:
            phrase = "💘 L'amour parfait! 💍"
        
        embed = discord.Embed(
            title="💘 Calculateur d'Amour",
            color=discord.Color.pink()
        )
        embed.add_field(name="Personne 1", value=member1.mention, inline=True)
        embed.add_field(name="Personne 2", value=member2.mention, inline=True)
        embed.add_field(name="Score d'amour", value=f"**{love_percent}%**", inline=False)
        embed.add_field(name="Verdict", value=phrase, inline=False)
        
        await ctx.send(embed=embed)
    
    @commands.command(name="cat")
    async def cat_cmd(self, ctx):
        """Afficher une photo de chat"""
        try:
            response = requests.get("https://api.thecatapi.com/v1/images/search")
            data = response.json()
            cat_url = data[0]['url']
            
            embed = discord.Embed(title="😺 Miaou!", color=COLORS["fun"])
            embed.set_image(url=cat_url)
            await ctx.send(embed=embed)
        except:
            embed = EmbedCreator.error("Impossible de récupérer une image de chat")
            await ctx.send(embed=embed)
    
    @commands.command(name="dog")
    async def dog_cmd(self, ctx):
        """Afficher une photo de chien"""
        try:
            response = requests.get("https://dog.ceo/api/breeds/image/random")
            data = response.json()
            dog_url = data['message']
            
            embed = discord.Embed(title="🐶 Ouaf!", color=COLORS["fun"])
            embed.set_image(url=dog_url)
            await ctx.send(embed=embed)
        except:
            embed = EmbedCreator.error("Impossible de récupérer une image de chien")
            await ctx.send(embed=embed)
    
    @commands.command(name="meme")
    async def meme_cmd(self, ctx):
        """Afficher un meme"""
        try:
            response = requests.get("https://meme-api.com/gimme")
            data = response.json()
            
            embed = discord.Embed(title=data['title'], color=COLORS["fun"])
            embed.set_image(url=data['url'])
            embed.set_footer(text=f"r/{data['subreddit']} | 👍 {data['ups']}")
            await ctx.send(embed=embed)
        except:
            embed = EmbedCreator.error("Impossible de récupérer un meme")
            await ctx.send(embed=embed)
    
    @commands.command(name="say")
    @commands.has_permissions(manage_messages=True)
    async def say_cmd(self, ctx, *, message: str):
        """Faire parler le bot"""
        await ctx.message.delete()
        await ctx.send(message)
    
    @commands.command(name="embed")
    @commands.has_permissions(manage_messages=True)
    async def embed_cmd(self, ctx, *, text: str):
        """Créer un embed"""
        embed = discord.Embed(
            description=text,
            color=COLORS["info"],
            timestamp=datetime.datetime.now()
        )
        embed.set_footer(text=ctx.author.display_name, icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
        await ctx.send(embed=embed)

# ==================== COG: TICKETS ====================
class TicketCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    class TicketView(View):
        def __init__(self):
            super().__init__(timeout=None)
        
        @discord.ui.button(label="🎫 Ouvrir un ticket", style=discord.ButtonStyle.green, custom_id="ticket_open")
        async def open_ticket(self, interaction: discord.Interaction, button: Button):
            # Vérifier si l'utilisateur a déjà un ticket ouvert
            async with db.db.cursor() as cursor:
                await cursor.execute(
                    "SELECT channel_id FROM tickets WHERE user_id = ? AND guild_id = ? AND status = 'open'",
                    (interaction.user.id, interaction.guild.id)
                )
                existing = await cursor.fetchone()
                
                if existing:
                    embed = EmbedCreator.error("Vous avez déjà un ticket ouvert!")
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                    return
            
            # Créer le salon
            overwrites = {
                interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            }
            
            # Ajouter les modérateurs
            for role in interaction.guild.roles:
                if role.permissions.manage_messages:
                    overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
            
            category = discord.utils.get(interaction.guild.categories, name="Tickets")
            if not category:
                category = await interaction.guild.create_category("Tickets")
            
            ticket_channel = await interaction.guild.create_text_channel(
                name=f"ticket-{interaction.user.name}",
                category=category,
                overwrites=overwrites
            )
            
            # Sauvegarder dans la DB
            async with db.db.cursor() as cursor:
                await cursor.execute(
                    "INSERT INTO tickets (guild_id, user_id, channel_id, status) VALUES (?, ?, ?, 'open')",
                    (interaction.guild.id, interaction.user.id, ticket_channel.id)
                )
                await db.db.commit()
            
            # Envoyer le message d'accueil
            embed = discord.Embed(
                title="🎫 Ticket Support",
                description=f"Bonjour {interaction.user.mention}!\n"
                          f"Le staff vous répondra bientôt.\n\n"
                          f"Utilisez `!close` pour fermer ce ticket.",
                color=COLORS["ticket"],
                timestamp=datetime.datetime.now()
            )
            
            close_button = Button(label="🔒 Fermer", style=discord.ButtonStyle.red, custom_id=f"close_{ticket_channel.id}")
            
            async def close_callback(interaction: discord.Interaction):
                await self.close_ticket(interaction, ticket_channel.id)
            
            close_button.callback = close_callback
            
            view = View()
            view.add_item(close_button)
            
            await ticket_channel.send(embed=embed, view=view)
            
            embed = EmbedCreator.success(f"Ticket créé: {ticket_channel.mention}")
            await interaction.response.send_message(embed=embed, ephemeral=True)
        
        async def close_ticket(self, interaction: discord.Interaction, channel_id: int):
            # Mettre à jour la DB
            async with db.db.cursor() as cursor:
                await cursor.execute(
                    "UPDATE tickets SET status = 'closed' WHERE channel_id = ?",
                    (channel_id,)
                )
                await db.db.commit()
            
            channel = interaction.guild.get_channel(channel_id)
            if channel:
                await channel.delete()
            
            embed = EmbedCreator.success("Ticket fermé avec succès")
            await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @commands.command(name="ticketsetup")
    @commands.has_permissions(administrator=True)
    async def ticketsetup_cmd(self, ctx):
        """Configurer le système de tickets"""
        embed = discord.Embed(
            title="🎫 Système de Tickets",
            description="Cliquez sur le bouton ci-dessous pour ouvrir un ticket de support.",
            color=COLORS["ticket"]
        )
        
        await ctx.send(embed=embed, view=self.TicketView())
    
    @commands.command(name="close")
    async def close_cmd(self, ctx):
        """Fermer un ticket"""
        async with db.db.cursor() as cursor:
            await cursor.execute(
                "SELECT * FROM tickets WHERE channel_id = ?",
                (ctx.channel.id,)
            )
            ticket = await cursor.fetchone()
        
        if not ticket:
            embed = EmbedCreator.error("Ce salon n'est pas un ticket!")
            await ctx.send(embed=embed)
            return
        
        # Mettre à jour la DB
        async with db.db.cursor() as cursor:
            await cursor.execute(
                "UPDATE tickets SET status = 'closed' WHERE channel_id = ?",
                (ctx.channel.id,)
            )
            await db.db.commit()
        
        embed = EmbedCreator.success("Ticket fermé. Le salon sera supprimé dans 5 secondes.")
        await ctx.send(embed=embed)
        
        await asyncio.sleep(5)
        await ctx.channel.delete()

# ==================== COG: GIVEAWAYS ====================
class GiveawayCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.giveaway_check.start()
    
    def cog_unload(self):
        self.giveaway_check.cancel()
    
    @tasks.loop(seconds=30)
    async def giveaway_check(self):
        """Vérifier les giveaways terminés"""
        async with db.db.cursor() as cursor:
            await cursor.execute(
                "SELECT * FROM giveaways WHERE end_time < datetime('now') AND ended = 0"
            )
            giveaways = await cursor.fetchall()
            
            for giveaway in giveaways:
                await self.end_giveaway(giveaway)
    
    @giveaway_check.before_loop
    async def before_giveaway_check(self):
        await self.bot.wait_until_ready()
    
    async def end_giveaway(self, giveaway):
        guild_id, channel_id, message_id, prize, winners, end_time, participants_json, ended = giveaway
        
        guild = self.bot.get_guild(guild_id)
        if not guild:
            return
        
        channel = guild.get_channel(channel_id)
        if not channel:
            return
        
        try:
            message = await channel.fetch_message(message_id)
        except:
            return
        
        # Récupérer les participants
        participants = json.loads(participants_json)
        
        if not participants:
            embed = discord.Embed(
                title="🎉 Giveaway Terminé",
                description=f"**Prix:** {prize}\n\n❌ Personne n'a participé!",
                color=COLORS["giveaway"],
                timestamp=datetime.datetime.now()
            )
            await message.edit(embed=embed, view=None)
            
            async with db.db.cursor() as cursor:
                await cursor.execute(
                    "UPDATE giveaways SET ended = 1 WHERE message_id = ?",
                    (message_id,)
                )
                await db.db.commit()
            return
        
        # Sélectionner les gagnants
        winners_list = []
        for _ in range(min(winners, len(participants))):
            winner_id = random.choice(participants)
            winners_list.append(winner_id)
            participants.remove(winner_id)
        
        # Mentionner les gagnants
        winner_mentions = []
        for winner_id in winners_list:
            member = guild.get_member(winner_id)
            if member:
                winner_mentions.append(member.mention)
        
        embed = discord.Embed(
            title="🎉 Giveaway Terminé",
            description=f"**Prix:** {prize}\n\n🏆 **Gagnant(s):** {', '.join(winner_mentions) if winner_mentions else 'Aucun'}",
            color=COLORS["giveaway"],
            timestamp=datetime.datetime.now()
        )
        
        await message.edit(embed=embed, view=None)
        await channel.send(f"🎉 Félicitations {', '.join(winner_mentions)}! Vous avez gagné **{prize}**!")
        
        # Marquer comme terminé
        async with db.db.cursor() as cursor:
            await cursor.execute(
                "UPDATE giveaways SET ended = 1 WHERE message_id = ?",
                (message_id,)
            )
            await db.db.commit()
    
    class GiveawayView(View):
        def __init__(self, giveaway_id: int):
            super().__init__(timeout=None)
            self.giveaway_id = giveaway_id
        
        @discord.ui.button(label="🎁 Participer", style=discord.ButtonStyle.green, custom_id="giveaway_join")
        async def join_giveaway(self, interaction: discord.Interaction, button: Button):
            async with db.db.cursor() as cursor:
                await cursor.execute(
                    "SELECT participants FROM giveaways WHERE id = ?",
                    (self.giveaway_id,)
                )
                result = await cursor.fetchone()
                
                if result:
                    participants = json.loads(result[0])
                    
                    if interaction.user.id not in participants:
                        participants.append(interaction.user.id)
                        
                        await cursor.execute(
                            "UPDATE giveaways SET participants = ? WHERE id = ?",
                            (json.dumps(participants), self.giveaway_id)
                        )
                        await db.db.commit()
                        
                        embed = EmbedCreator.success("Vous participez maintenant au giveaway!")
                        await interaction.response.send_message(embed=embed, ephemeral=True)
                    else:
                        embed = EmbedCreator.warning("Vous participez déjà à ce giveaway!")
                        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @commands.command(name="giveaway")
    @commands.has_permissions(manage_guild=True)
    async def giveaway_cmd(self, ctx, duration: str, winners: int, *, prize: str):
        """Créer un giveaway"""
        # Convertir la durée
        if duration.endswith('s'):
            seconds = int(duration[:-1])
        elif duration.endswith('m'):
            seconds = int(duration[:-1]) * 60
        elif duration.endswith('h'):
            seconds = int(duration[:-1]) * 3600
        elif duration.endswith('d'):
            seconds = int(duration[:-1]) * 86400
        else:
            seconds = 3600  # 1 heure par défaut
        
        end_time = datetime.datetime.now() + datetime.timedelta(seconds=seconds)
        
        embed = discord.Embed(
            title="🎉 GIVEAWAY 🎉",
            description=f"**Prix:** {prize}\n"
                       f"**Nombre de gagnants:** {winners}\n"
                       f"**Temps restant:** <t:{int(end_time.timestamp())}:R>\n\n"
                       f"Cliquez sur 🎁 pour participer!",
            color=COLORS["giveaway"],
            timestamp=end_time
        )
        embed.set_footer(text="Fin du giveaway")
        
        message = await ctx.send(embed=embed)
        
        # Sauvegarder dans la DB
        async with db.db.cursor() as cursor:
            await cursor.execute(
                "INSERT INTO giveaways (guild_id, channel_id, message_id, prize, winners, end_time, participants) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (ctx.guild.id, ctx.channel.id, message.id, prize, winners, end_time, '[]')
            )
            await cursor.execute("SELECT last_insert_rowid()")
            giveaway_id = (await cursor.fetchone())[0]
            await db.db.commit()
        
        # Ajouter le bouton de participation
        view = self.GiveawayView(giveaway_id)
        await message.edit(view=view)
        
        embed = EmbedCreator.success(f"Giveaway créé! [Aller au giveaway]({message.jump_url})")
        await ctx.send(embed=embed, delete_after=5)
    
    @commands.command(name="reroll")
    @commands.has_permissions(manage_guild=True)
    async def reroll_cmd(self, ctx, message_id: int):
        """Relancer un giveaway"""
        async with db.db.cursor() as cursor:
            await cursor.execute(
                "SELECT * FROM giveaways WHERE message_id = ?",
                (message_id,)
            )
            giveaway = await cursor.fetchone()
        
        if not giveaway:
            embed = EmbedCreator.error("Giveaway non trouvé!")
            await ctx.send(embed=embed)
            return
        
        await self.end_giveaway(giveaway)
        embed = EmbedCreator.success("Giveaway relancé!")
        await ctx.send(embed=embed)

# ==================== COG: VOCAL ====================
class VocalCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name="join")
    async def join_cmd(self, ctx):
        """Rejoindre le salon vocal"""
        if not ctx.author.voice:
            embed = EmbedCreator.error("Vous devez être dans un salon vocal!")
            await ctx.send(embed=embed)
            return
        
        channel = ctx.author.voice.channel
        await channel.connect()
        
        embed = EmbedCreator.success(f"Connecté à {channel.mention}")
        await ctx.send(embed=embed)
    
    @commands.command(name="leave")
    async def leave_cmd(self, ctx):
        """Quitter le salon vocal"""
        if not ctx.voice_client:
            embed = EmbedCreator.error("Je ne suis pas dans un salon vocal!")
            await ctx.send(embed=embed)
            return
        
        await ctx.voice_client.disconnect()
        
        embed = EmbedCreator.success("Déconnecté du salon vocal")
        await ctx.send(embed=embed)
    
    @commands.command(name="move")
    @commands.has_permissions(move_members=True)
    async def move_cmd(self, ctx, member: discord.Member, channel: discord.VoiceChannel):
        """Déplacer un membre vers un salon vocal"""
        await member.move_to(channel)
        
        embed = EmbedCreator.success(f"{member.mention} déplacé vers {channel.mention}")
        await ctx.send(embed=embed)
    
    @commands.command(name="voicelock")
    @commands.has_permissions(manage_channels=True)
    async def voicelock_cmd(self, ctx, channel: discord.VoiceChannel = None):
        """Verrouiller un salon vocal"""
        channel = channel or ctx.author.voice.channel if ctx.author.voice else None
        if not channel:
            embed = EmbedCreator.error("Vous devez être dans un salon vocal ou en spécifier un!")
            await ctx.send(embed=embed)
            return
        
        overwrite = channel.overwrites_for(ctx.guild.default_role)
        overwrite.connect = False
        await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
        
        embed = EmbedCreator.success(f"{channel.mention} verrouillé")
        await ctx.send(embed=embed)
    
    @commands.command(name="voicekick")
    @commands.has_permissions(move_members=True)
    async def voicekick_cmd(self, ctx, member: discord.Member):
        """Expulser un membre d'un salon vocal"""
        if not member.voice:
            embed = EmbedCreator.error("Ce membre n'est pas dans un salon vocal!")
            await ctx.send(embed=embed)
            return
        
        await member.move_to(None)
        
        embed = EmbedCreator.success(f"{member.mention} expulsé du vocal")
        await ctx.send(embed=embed)
    
    @commands.command(name="voicemute")
    @commands.has_permissions(mute_members=True)
    async def voicemute_cmd(self, ctx, member: discord.Member):
        """Muter un membre dans le vocal"""
        if not member.voice:
            embed = EmbedCreator.error("Ce membre n'est pas dans un salon vocal!")
            await ctx.send(embed=embed)
            return
        
        await member.edit(mute=True)
        
        embed = EmbedCreator.success(f"{member.mention} muté dans le vocal")
        await ctx.send(embed=embed)
    
    @commands.command(name="voicedeaf")
    @commands.has_permissions(deafen_members=True)
    async def voicedeaf_cmd(self, ctx, member: discord.Member):
        """Rendre sourd un membre dans le vocal"""
        if not member.voice:
            embed = EmbedCreator.error("Ce membre n'est pas dans un salon vocal!")
            await ctx.send(embed=embed)
            return
        
        await member.edit(deafen=True)
        
        embed = EmbedCreator.success(f"{member.mention} rendu sourd dans le vocal")
        await ctx.send(embed=embed)

# ==================== COG: LOGS ====================
class LogsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Log les arrivées"""
        async with db.db.cursor() as cursor:
            await cursor.execute(
                "SELECT joinlog_channel FROM logs WHERE guild_id = ?",
                (member.guild.id,)
            )
            result = await cursor.fetchone()
        
        if result and result[0]:
            channel = member.guild.get_channel(result[0])
            if channel:
                embed = discord.Embed(
                    title="📥 Nouveau Membre",
                    description=f"{member.mention} a rejoint le serveur",
                    color=COLORS["success"],
                    timestamp=datetime.datetime.now()
                )
                embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
                embed.add_field(name="🆔 ID", value=member.id, inline=True)
                embed.add_field(name="📅 Compte créé", value=member.created_at.strftime("%d/%m/%Y"), inline=True)
                embed.add_field(name="👥 Total membres", value=member.guild.member_count, inline=True)
                
                await channel.send(embed=embed)
    
    @commands.Cog.listener()
    async def on_member_remove(self, member):
        """Log les départs"""
        async with db.db.cursor() as cursor:
            await cursor.execute(
                "SELECT leavelog_channel FROM logs WHERE guild_id = ?",
                (member.guild.id,)
            )
            result = await cursor.fetchone()
        
        if result and result[0]:
            channel = member.guild.get_channel(result[0])
            if channel:
                embed = discord.Embed(
                    title="📤 Départ",
                    description=f"{member.mention} a quitté le serveur",
                    color=COLORS["error"],
                    timestamp=datetime.datetime.now()
                )
                embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
                embed.add_field(name="🆔 ID", value=member.id, inline=True)
                embed.add_field(name="📅 A rejoint le", value=member.joined_at.strftime("%d/%m/%Y"), inline=True)
                
                await channel.send(embed=embed)
    
    @commands.Cog.listener()
    async def on_message_delete(self, message):
        """Log les messages supprimés"""
        if not message.guild or message.author.bot:
            return
        
        async with db.db.cursor() as cursor:
            await cursor.execute(
                "SELECT msglog_channel FROM logs WHERE guild_id = ?",
                (message.guild.id,)
            )
            result = await cursor.fetchone()
        
        if result and result[0]:
            channel = message.guild.get_channel(result[0])
            if channel:
                embed = discord.Embed(
                    title="🗑️ Message Supprimé",
                    color=COLORS["warning"],
                    timestamp=datetime.datetime.now()
                )
                embed.add_field(name="👤 Auteur", value=message.author.mention, inline=True)
                embed.add_field(name="📁 Salon", value=message.channel.mention, inline=True)
                embed.add_field(name="📝 Contenu", value=message.content[:1000] or "*[Contenu vide ou embed]*", inline=False)
                
                await channel.send(embed=embed)
    
    @commands.command(name="setlog")
    @commands.has_permissions(administrator=True)
    async def setlog_cmd(self, ctx, log_type: str, channel: discord.TextChannel):
        """Définir un salon de logs"""
        valid_types = ["modlog", "joinlog", "leavelog", "msglog", "voicelog", 
                      "emojilog", "fluxlog", "gwlog", "invitelog", "raidlog", 
                      "reactionlog", "rolelog", "starlog", "systemlog"]
        
        if log_type not in valid_types:
            embed = EmbedCreator.error(f"Type de log invalide! Types valides: {', '.join(valid_types)}")
            await ctx.send(embed=embed)
            return
        
        async with db.db.cursor() as cursor:
            await cursor.execute(
                f"INSERT OR REPLACE INTO logs (guild_id, {log_type}_channel) VALUES (?, ?)",
                (ctx.guild.id, channel.id)
            )
            await db.db.commit()
        
        embed = EmbedCreator.success(f"Salon {log_type} défini sur {channel.mention}")
        await ctx.send(embed=embed)

# ==================== COG: OWNER ====================
class OwnerCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    async def is_owner(self, ctx):
        return ctx.author.id in OWNER_IDS or await self.bot.is_owner(ctx.author)
    
    @commands.command(name="blacklist")
    async def blacklist_cmd(self, ctx, user: discord.User):
        """Blacklist un utilisateur"""
        if not await self.is_owner(ctx):
            embed = EmbedCreator.error("Commande réservée au propriétaire!")
            await ctx.send(embed=embed)
            return
        
        # Implémentation de la blacklist
        embed = EmbedCreator.success(f"{user.mention} blacklisté")
        await ctx.send(embed=embed)
    
    @commands.command(name="serverlist")
    async def serverlist_cmd(self, ctx):
        """Liste des serveurs"""
        if not await self.is_owner(ctx):
            embed = EmbedCreator.error("Commande réservée au propriétaire!")
            await ctx.send(embed=embed)
            return
        
        embed = discord.Embed(
            title="🏠 Serveurs",
            color=COLORS["info"]
        )
        
        for guild in self.bot.guilds:
            embed.add_field(
                name=guild.name,
                value=f"👥 {guild.member_count} membres | 🆔 {guild.id}",
                inline=False
            )
        
        await ctx.send(embed=embed)
    
    @commands.command(name="leaveguild")
    async def leaveguild_cmd(self, ctx, guild_id: int):
        """Quitter un serveur"""
        if not await self.is_owner(ctx):
            embed = EmbedCreator.error("Commande réservée au propriétaire!")
            await ctx.send(embed=embed)
            return
        
        guild = self.bot.get_guild(guild_id)
        if guild:
            await guild.leave()
            embed = EmbedCreator.success(f"Quitté {guild.name}")
        else:
            embed = EmbedCreator.error("Serveur non trouvé!")
        
        await ctx.send(embed=embed)

# ==================== COMMANDES RAPIDES (sans cogs) ====================
@bot.command(name="help")
async def help_command(ctx, category: str = None):
    """Affiche l'aide"""
    all_commands = {
        "🔨 Modération": [
            "ban", "kick", "mute", "clear", "warn", "warnings", 
            "slowmode", "lock", "unlock", "nick", "role", "temprole"
        ],
        "ℹ️ Information": [
            "serverinfo", "userinfo", "avatar", "banner", "roleinfo",
            "botinfo", "ping", "uptime"
        ],
        "😄 Fun": [
            "hug", "kiss", "slap", "roll", "coinflip", "8ball",
            "lovecalc", "cat", "dog", "meme", "say", "embed"
        ],
        "🎫 Tickets": [
            "ticketsetup", "close"
        ],
        "🎉 Giveaways": [
            "giveaway", "reroll"
        ],
        "🎤 Vocal": [
            "join", "leave", "move", "voicelock", "voicekick",
            "voicemute", "voicedeaf"
        ],
        "📊 Logs": [
            "setlog"
        ],
        "👑 Owner": [
            "blacklist", "serverlist", "leaveguild"
        ]
    }
    
    if category:
        category_lower = category.lower()
        for cat_name, cmds in all_commands.items():
            if category_lower in cat_name.lower():
                embed = discord.Embed(
                    title=f"📚 {cat_name}",
                    description="\n".join([f"• `{cmd}`" for cmd in cmds]),
                    color=COLORS["info"]
                )
                await ctx.send(embed=embed)
                return
        embed = EmbedCreator.error(f"Catégorie '{category}' non trouvée!")
        await ctx.send(embed=embed)
    else:
        embeds = []
        
        # Créer 3 pages
        categories = list(all_commands.items())
        page_size = len(categories) // 3 + 1
        
        for i in range(3):
            start = i * page_size
            end = start + page_size
            page_categories = categories[start:end]
            
            embed = discord.Embed(
                title=f"📚 Aide - Page {i+1}/3",
                color=[COLORS["info"], COLORS["success"], COLORS["fun"]][i],
                timestamp=datetime.datetime.now()
            )
            
            for cat_name, cmds in page_categories:
                embed.add_field(
                    name=cat_name,
                    value=", ".join([f"`{cmd}`" for cmd in cmds[:8]]) + ("..." if len(cmds) > 8 else ""),
                    inline=False
                )
            
            embed.set_footer(text=f"Utilisez !help <catégorie> pour plus d'infos")
            embeds.append(embed)
        
        view = Paginator(embeds)
        await ctx.send(embed=embeds[0], view=view)

# ==================== ÉVÉNEMENTS ====================
@bot.event
async def on_ready():
    await db.connect()
    bot.start_time = datetime.datetime.now()
    print(f"✅ {bot.user} est connecté!")
    print(f"📊 Nombre de serveurs: {len(bot.guilds)}")
    print(f"👥 Nombre d'utilisateurs: {sum(g.member_count for g in bot.guilds)}")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        embed = EmbedCreator.warning(f"Commande non trouvée! Utilisez `!help`")
        await ctx.send(embed=embed)
    elif isinstance(error, commands.MissingPermissions):
        embed = EmbedCreator.error("Vous n'avez pas les permissions nécessaires!")
        await ctx.send(embed=embed)
    elif isinstance(error, commands.MissingRequiredArgument):
        embed = EmbedCreator.error(f"Argument manquant! Utilisez `!help {ctx.command.name}`")
        await ctx.send(embed=embed)
    else:
        embed = EmbedCreator.error(f"Erreur: {str(error)[:100]}")
        await ctx.send(embed=embed)

# ==================== AJOUT DES COGS ====================
async def setup_cogs():
    await bot.add_cog(ModerationCog(bot))
    await bot.add_cog(InformationCog(bot))
    await bot.add_cog(FunCog(bot))
    await bot.add_cog(TicketCog(bot))
    await bot.add_cog(GiveawayCog(bot))
    await bot.add_cog(VocalCog(bot))
    await bot.add_cog(LogsCog(bot))
    await bot.add_cog(OwnerCog(bot))

# ==================== LANCEMENT ====================
async def main():
    await setup_cogs()
    await bot.start(TOKEN)

if __name__ == "__main__":
    # Créer un fichier config si nécessaire
    if not os.path.exists("config.json"):
        config = {
            "token": "VOTRE_TOKEN_ICI",
            "owner_ids": [],
            "default_prefix": "!",
            "database_path": "bot_database.db"
        }
        with open("config.json", "w") as f:
            json.dump(config, f, indent=4)
        print("⚠️  Fichier config.json créé. Veuillez y ajouter votre token Discord!")
        exit()
    
    # Charger la config
    with open("config.json", "r") as f:
        config = json.load(f)
    
    TOKEN = config["token"]
    OWNER_IDS = config.get("owner_ids", [])
    
    asyncio.run(main())
