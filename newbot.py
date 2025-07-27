import re
import logging
import asyncio
import uuid
import random
from pathlib import Path
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    CallbackContext,
)
from concurrent.futures import ThreadPoolExecutor, as_completed
import pickle
import os

# -----------------------------
# Logging and Directories 📊📂
# -----------------------------
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s", level=logging.DEBUG
)
LOGS_DIR = Path("./logs/")
LOGS_DIR.mkdir(parents=True, exist_ok=True)
SAVE_DIR = Path("./Generated_Results/")
SAVE_DIR.mkdir(parents=True, exist_ok=True)

# -----------------------------
# Bot Token and Admin Settings 🤖👑
# -----------------------------
import os
TOKEN = os.getenv("7807079382:AAF2urH8cuDF2fdF4I7LXqGOX8QKZv44XDg")  # Replace with your actual token
ADMIN_ID = 7104410545  # Replace with your Telegram ID
ALLOWED_USERS = set()  # Users must redeem a key to access

# -----------------------------
# Global Variables for Keys, Pause Status, and Command Cancellation 🔐⏸️
# -----------------------------
keys = {}  # Stores keys: key-string or user_id -> expiration datetime
used_keys = set()  # Tracks keys that have been redeemed (or expired)
paused_users = set()  # Set of user IDs whose key is paused
DATA_FILE = "bot_data.pkl"
generation_history = {}  # {user_id: {"username": str, "generated_count": int, "total_lines": int}}

# This dict stores the latest command ID for each user to allow cancellation
current_commands = {}  # {user_id: uuid.UUID}

# -----------------------------
# Keywords Categories 💡
# -----------------------------
KEYWORDS_CATEGORIES = {
    "⚡ GARENA FILES": {
    "🛡️ [CORE] CODM": "garena.com",
    "🔐 [LOGIN] SSO CODM": "sso.garena.com",
    "🕶️ [HIDDEN] Ghost Link": "authgop.garena.com/universal/oauth",
    "💎 [VIP] Elite Access": "authgop.garena.com/oauth/login",
    "🔑 [GATE] Paldo Entry": "auth.garena.com/ui/login",
    "⚠️ [VIP] Auth Point": "auth.garena.com/oauth/login",
    "⚠️ [VIP] Uni Link": "sso.garena.com/universal/login",
    "⚠️ [VIP] Reg Link": "sso.garena.com/ui/register",
    "🌐 [SITE] 100055": "100055.connect.garena.com",
    "🌐 [SITE] 100080": "100080.connect.garena.com",
    "🌐 [SITE] 100054": "100054.connect.garena.com",
    "🌐 [SITE] 100072": "100072.connect.garena.com",
    "🌐 [SITE] 100082": "100082.connect.garena.com"
    },
    "⚡ ML FILES": {
    "🛡️ Official Site": "mobilelegends.com",
    "🔐 Login Portal": "mtacc.mobilelegends.com",
    "🕶️ Hidden Login": "play.mobilelegends.com",
    "💎 VIP Access": "m.mobilelegends.com"
    },
    "🌐 SOCMED": {
    "📘 Facebook": "facebook.com",
    "📷 Instagram": "instagram.com",
    "🐦 X (Twitter)": "twitter.com",
    "🎥 YouTube": "youtube.com",
    "💬 WhatsApp": "whatsapp.com",
    "🎵 TikTok": "tiktok.com",
    "👻 Snapchat": "snapchat.com",
    "💼 LinkedIn": "linkedin.com",
    "📌 Pinterest": "pinterest.com",
    "📱 Reddit": "reddit.com",
    "📖 Tumblr": "tumblr.com",
    "🎮 Discord": "discord.com",
    "📡 Telegram": "telegram.org",
    "🟢 WeChat": "wechat.com",
    "💬 QQ": "qq.com",
    "🌏 Sina Weibo": "weibo.com",
    "📱 Kuaishou": "kuaishou.com",
    "🎵 Douyin (China TikTok)": "douyin.com",
    "📱 Xiaohongshu (RED)": "xiaohongshu.com",
    "🎮 Twitch": "twitch.tv",
    "🦣 Mastodon": "joinmastodon.org",
    "🌌 Bluesky": "bsky.app",
    "📢 Threads (Meta)": "threads.net",
    "🎙️ Clubhouse": "clubhouse.com",
    "👥 MeWe": "mewe.com",
    "🔴 Parler": "parler.com",
    "🐸 Gab": "gab.com",
    "🇺🇸 Truth Social": "truthsocial.com",
    "✅ Vero": "vero.co",
    "🧠 Minds": "minds.com",
    "📺 Rumble": "rumble.com",
    "🔵 Gettr": "gettr.com",
    "📡 Caffeine": "caffeine.tv",
    "🎥 DLive": "dlive.tv",
    "📹 Bigo Live": "bigo.tv",
    "🎭 Likee": "likee.video",
    "🎬 Triller": "triller.co",
    "🌍 VKontakte (VK)": "vk.com",
    "🧑‍🤝‍🧑 Odnoklassniki (OK)": "ok.ru",
    "👔 Xing": "xing.com",
    "🌏 Baidu Tieba": "tieba.baidu.com",
    "💬 Line": "line.me",
    "🟡 KakaoTalk": "kakaocorp.com/service/KakaoTalk",
    "🇻🇳 Zalo": "zalo.me",
    "🌎 Taringa!": "taringa.net",
    "🗾 Mixi": "mixi.jp",
    "🏯 Cyworld": "cyworld.com",
    "🎶 SoundCloud": "soundcloud.com",
    "🎵 ReverbNation": "reverbnation.com",
    "🎭 Ello": "ello.co",
    "📝 Steemit": "steemit.com",
    "🎞️ Flixster": "flixster.com",
    "📚 Goodreads": "goodreads.com",
    "🎬 Letterboxd": "letterboxd.com",
    "🎭 DeviantArt": "deviantart.com",
    "🎨 Behance": "behance.net",
    "🎨 Dribbble": "dribbble.com",
    "📷 500px": "500px.com",
    "🎭 VSCO": "vsco.co",
    "📷 Unsplash": "unsplash.com",
    "🏡 Houzz": "houzz.com",
    "👩‍👦 BabyCenter": "babycenter.com",
    "👨‍👩‍👦 CafeMom": "cafemom.com",
    "🎮 Gaia Online": "gaiaonline.com",
    "🏠 Nextdoor": "nextdoor.com",
    "🕹️ Habbo": "habbo.com",
    "🕹️ IMVU": "imvu.com",
    "🌐 Second Life": "secondlife.com",
    "📺 Myspace": "myspace.com",
    "📍 Foursquare": "foursquare.com",
    "🎙️ Anchor": "anchor.fm",
    "🗣️ Yik Yak": "yikyak.com",
    "🎙️ Audius": "audius.co",
    "📰 Flipboard": "flipboard.com",
    "📖 Medium": "medium.com",
    "📢 Substack": "substack.com",
    "📚 Wattpad": "wattpad.com",
    "📝 Scribd": "scribd.com",
    "🎮 ROBLOX Groups": "roblox.com/groups",
    "🕹️ Steam Community": "steamcommunity.com",
    "🟢 OpenSea (NFT)": "opensea.io",
    "💰 Patreon": "patreon.com",
    "💰 Ko-fi": "ko-fi.com",
    "🤑 OnlyFans": "onlyfans.com",
    "📷 9GAG": "9gag.com",
    "🐝 Hive Social": "hivesocial.app",
    "🕵️ TruthFinder": "truthfinder.com",
    "👨‍⚖️ PeerTube": "joinpeertube.org",
    "📩 Minds Chat": "chat.minds.com",
    "🚀 IndieHackers": "indiehackers.com",
    "📜 Amino Apps": "aminoapps.com",
    "🎵 Smule": "smule.com",
    "📷 Fotolog": "fotolog.com",
    "📢 Gab TV": "tv.gab.com",
    "📺 BitChute": "bitchute.com",
    "📷 Pixiv": "pixiv.net",
    "🔵 Tribel": "tribel.com",
    "🚀 Mastodon Instances": "instances.social",
    "🕹️ GameJolt": "gamejolt.com",
    "📱 Weverse": "weverse.io",
    "🎤 StarMaker": "starmakerstudios.com",
    "🎮 Gamebanana": "gamebanana.com"
    },
    "🎬 Cinema & Streaming": {
    "🍿 Netflix": "netflix.com",
    "📺 YouTube": "youtube.com",
    "🎭 Amazon Prime Video": "primevideo.com",
    "🎞 Disney+": "disneyplus.com",
    "🎥 HBO Max": "hbomax.com",
    "📡 Hulu": "hulu.com",
    "💎 Apple TV+": "tv.apple.com",
    "🔵 Paramount+": "paramountplus.com",
    "🦄 Peacock": "peacocktv.com",
    "🔥 Hotstar": "hotstar.com",
    "🎬 STARZ": "starz.com",
    "🌍 Rakuten TV": "rakuten.tv",
    "🖥 Crackle": "crackle.com",
    "🎦 Acorn TV": "acorn.tv",
    "🇬🇧 BritBox": "britbox.com",
    "🇦🇺 Stan": "stan.com.au",
    "🇪🇸 Movistar+": "movistarplus.es",
    "🇧🇷 GloboPlay": "globoplay.com",
    "🇨🇦 CBC Gem": "gem.cbc.ca",
    "🇫🇷 Canal+": "canalplus.com",
    "🇷🇺 Okko": "okko.tv",
    "🆓 Pluto TV": "pluto.tv",
    "🔄 Plex": "plex.tv",
    "📺 The Roku Channel": "therokuchannel.com",
    "🆓 Freevee": "freevee.com",
    "🎭 Mubi": "mubi.com",
    "🎞 FilmStruck": "filmstruck.com",
    "📽 Criterion Channel": "criterionchannel.com",
    "🕵 Shudder": "shudder.com",
    "🦇 DC Universe Infinite": "dcuniverse.com",
    "👻 Screambox": "screambox.com",
    "🧛‍♂ Midnight Pulp": "midnightpulp.com",
    "🔫 RetroCrush": "retrocrush.tv",
    "📼 Tubi TV": "tubitv.com",
    "💀 Fandor": "fandor.com",
    "🏆 ESPN+": "espn.com",
    "⚽ DAZN": "dazn.com",
    "🏈 NFL Game Pass": "nfl.com",
    "🏀 NBA League Pass": "nba.com",
    "⚾ MLB.TV": "mlb.com",
    "🏒 NHL TV": "nhl.com",
    "🎾 Tennis TV": "tennistv.com",
    "🎬 PopcornFlix": "popcornflix.com",
    "🍜 Crunchyroll": "crunchyroll.com",
    "🐲 Funimation": "funimation.com",
    "🎎 AnimeLab": "animelab.com",
    "📀 HIDIVE": "hidive.com",
    "🐼 Bilibili": "bilibili.com",
    "🎌 U-Next": "unext.jp",
    "🌙 Viu": "viu.com",
    "🈵 Youku": "youku.com",
    "🇰🇷 Kocowa": "kocowa.com",
    "🎤 Line TV": "tv.line.me",
    "🕵 Discovery+": "discoveryplus.com",
    "🌍 Nat Geo TV": "natgeotv.com",
    "🔬 Magellan TV": "magellantv.com",
    "🧠 MasterClass": "masterclass.com",
    "📖 Curiosity Stream": "curiositystream.com",
    "📚 The Great Courses": "thegreatcoursesplus.com",
    "📰 BBC iPlayer": "bbc.co.uk",
    "📰 CNN Live": "cnn.com",
    "📡 Al Jazeera Live": "aljazeera.com",
    "🌐 Sky Go": "sky.com",
    "🏡 HGTV Go": "watch.hgtv.com",
    "🎭 BroadwayHD": "broadwayhd.com",
    "🎞 Hallmark Movies Now": "hallmarkmoviesnow.com",
    "🎵 Stingray Qello": "qello.com",
    "🕵 True Crime Network": "truecrimenetworktv.com",
    "🎶 Spotify Video": "spotify.com",
    "🎸 Apple Music Videos": "music.apple.com",
    "🎤 Tidal": "tidal.com",
    "🎙 NPR Live": "npr.org",
    "🎬 ARGO": "watchargo.com",
    "🕵 Court TV": "courttv.com",
    "🚀 NASA TV": "nasa.gov",
    "🛸 Gaia": "gaia.com",
    "🎼 Mezzo TV": "mezzotv.com",
    "📺 ABC iView": "iview.abc.net.au",
    "🎬 SBS On Demand": "sbs.com.au",
    "🔫 Filmzie": "filmzie.com",
    "🌟 Xumo": "xumo.tv",
    "📀 Reelgood": "reelgood.com",
    "📽 Kanopy": "kanopy.com",
    "📡 Yahoo View": "view.yahoo.com",
    "🎞 SnagFilms": "snagfilms.com",
    "🛑 Redbox Free Live TV": "redbox.com",
    "🍿 Cineplex Store": "store.cineplex.com",
    "💎 Criterion Collection": "criterion.com",
    "🌎 BBC Earth": "bbcearth.com",
    "🚗 MotorTrend On Demand": "motortrendondemand.com",
    "🦸 Marvel HQ": "marvel.com",
    "🧩 PBS Kids": "pbskids.org",
    "🏚 HorrorFlix": "horrorflix.com",
    "🐍 Syfy Now": "syfy.com",
    "🤠 Western Mania": "westernmania.com",
    "🌆 BET+": "bet.com",
    "🦸‍♂️ Heroes & Icons": "heroesandicons.com",
    "📹 Facebook Watch": "facebook.com/watch",
    "💻 Cyberflix TV": "cyberflixtv.com",
    "🦉 Owl TV": "owltv.com",
    "🎸 Qello Concerts": "qello.com",
    "🎮 Twitch TV": "twitch.tv",
    "🎬 AMC+": "amcplus.com",
    "🦊 Fox Nation": "foxnation.com",
    "📼 Old Movies": "oldmovies.com",
    "🔦 Reelgood Originals": "reelgood.com/originals",
    "🕵 True Crime TV": "truecrime.com",
    "🎭 Hallmark Drama": "hallmarkdrama.com",
    "🌞 Outdoor Channel": "outdoorchannel.com",
    "🦖 Jurassic World TV": "jurassicworld.com",
    "🐻 Animal Planet GO": "animalplanetgo.com",
    "🎭 Bollywood Hungama": "bollywoodhungama.com",
    "🔮 Supernatural TV": "supernaturaltv.com",
    "👽 Sci-Fi Central": "scificentral.com",
    "🏹 The CW Network": "cwtv.com",
    "🕵 Crime + Investigation": "crimeandinvestigation.com",
    "🧙‍♂️ Magic TV": "magictv.com",
    "🎮 eSports TV": "esportstv.com",
    "🦸‍♂️ Superhero Channel": "superherochannel.com",
    "🚓 COPS TV": "copstv.com",
    "🗽 NYC Media": "nyc.gov/media",
    "🎞 ClassicFlix": "classicflix.com",
    "🦊 Fox Sports": "foxsports.com",
    "🏎 F1 TV": "f1tv.com",
    "🚁 Military Channel": "militarychannel.com",
    "📺 My5": "my5.tv",
    "🕶 IFC Films Unlimited": "ifcfilms.com",
    "🎮 Game Pass TV": "gamepass.com",
    "🌑 Night Flight": "nightflight.com",
    "💰 Bloomberg TV": "bloomberg.com/live",
    "💡 TED Talks": "ted.com",
     },
    "🗃️ COMBOLIST": {
    "📩⚠️COMBO_OUTLOOK": "outlook.com",
    "📩⚠️COMBO_HOTMAIL": "hotmail.com",
    "📂💀COMBO_G00GLE": "gmail.com",
    "💎🔐COMBO_YAH00": "yahoo.com",
    "🕶️🔓COMBO_PROTON": "protonmail.com",
    "🛰️⚡COMBO_TUTANOTA": "tutanota.com",
    "🔰📡COMBO_ZOHO": "zoho.com",
    "🔥📩COMBO_GMX": "gmx.com",
    "🌍🛡️COMBO_YANDEX": "yandex.com",
    "🕵️‍♂️🚨COMBO_HUSHMAIL": "hushmail.com",
    "🔒📡COMBO_STARTMAIL": "startmail.com",
    "⚡🚀COMBO_FASTMAIL": "fastmail.com"
    },
    "⚔️ MOBA GAMES": {
    "🛡️ Mobile Legends: Bang Bang": "account.mobilelegends.com",
    "🔥 League of Legends: Wild Rift": "login.riotgames.com",
    "⚔️ League of Legends (PC)": "auth.riotgames.com",
    "🐉 Arena of Valor (AOV)": "login.garena.com",
    "🎭 Marvel Super War": "login.marvelsuperwar.com",
    "👹 Heroes Evolved": "account.r2games.com",
    "🔥 Pokémon UNITE": "club.pokemon.com",
    "🕹️ Vainglory": "superevilmegacorp.com/login",
    "⚔️ Onmyoji Arena": "account.onmyojiarena.com",
    "🔥 Honor of Kings (China)": "login.tencent.com",
    "⚡ Smite": "login.hirezstudios.com",
    "🔥 Battlerite": "login.battlerite.com",
    "⚡ Eternal Return": "account.eternalreturn.com",
    "🔥 Frayhem": "login.frayhem.com",
    "⚔️ Planet of Heroes": "login.planetheroes.com",
    "🔥 War Song": "login.warsong.com",
    "🐲 Heroes Arise": "account.heroesarise.com",
    "⚡ Auto Chess MOBA": "account.autochessmoba.com",
    "🔥 Thetan Arena": "login.thetanarena.com",
    "⚡ Battle Rivals": "login.battlerivals.com",
    "🔥 Lokapala": "login.lokapala.com",
    "🛡️ Extraordinary Ones": "login.netase.com",
    "🔥 Light x Shadow": "login.lightxshadow.com",
    "🦸‍♂️ DC Battle Arena": "login.dcbattlearena.com",
    "🛡️ Smash Legends": "login.smashlegends.com",
    "⚡ Warbound Storm": "login.warboundstorm.com",
    "🔥 Bloodline Champions": "login.bloodlinechampions.com",
    "⚔️ Awakening of Heroes": "login.awakeningofheroes.com",
    "🔥 Battle Boom": "login.battleboom.com",
    "⚡ Kingdom Arena": "login.kingdombattle.com",
    "🛡️ Dream Arena": "login.dreamarena.com",
    "🔥 Heroes of Order & Chaos": "login.gameloft.com",
    "⚔️ Strife": "login.strife.com",
    "🔥 FOG MOBA": "login.fogmoba.com",
    "⚔️ Iron League": "login.irleague.com",
    "🔥 Survival Heroes": "login.survivalheroes.com",
    "⚔️ Hero Hunters": "login.herohunters.com",
    "🔥 Tower Conquest": "login.towerconquest.com",
    "⚡ Mystic Warriors MOBA": "login.mysticwarriors.com",
    "🔥 League of Smashers": "account.leagueofsmashers.com",
    "⚔️ Supreme Heroes": "login.supremeheroes.com",
    "🔥 Celestial MOBA": "login.celestialmoba.com",
    "👹 War of Titans": "account.waroftitans.com",
    "⚡ Rift Warriors": "login.riftwarriors.com",
    "🎮 Dominion Clash": "account.dominionclash.com",
    "🔥 Phantom Arena": "login.phantomarena.com",
    "⚡ Shadow Brawl": "login.shadowbrawl.com",
    "🔥 Chaos Legends": "login.chaoslegends.com",
    "⚔️ War Gods": "login.wargods.com",
    "🔥 Titan Arena": "login.titanarena.com",
    "⚡ Smash Arena": "login.smasharena.com",
    "🔥 Doom Arena MOBA": "login.doomarena.com",
    "⚔️ Arcane Battle": "login.arcanebattle.com",
    "👹 Inferno Warriors": "account.infernowarriors.com",
    "⚡ Kings Arena": "login.kingsarena.com",
    "🔥 Legendary Clash": "login.legendaryclash.com",
    "👑 Divine Warriors": "account.divinewarriors.com",
    "⚔️ Eclipse Battle": "login.eclipsebattle.com",
    "🔥 Nexus Wars": "login.nexuswars.com",
    "⚔️ Gladiator Arena": "login.gladiatorarena.com",
    "🔥 Blood Moon Battle": "login.bloodmoonbattle.com",
    "👊 Outlaw Legends": "account.outlawlegends.com",
    "⚡ Abyss Warriors": "login.abysswarriors.com",
    "🔥 Undying Champions": "login.undyingchampions.com",
    "⚔️ Supreme Battle": "login.supremebattle.com",
    "🔥 Celestial Arena": "login.celestialarena.com",
    "⚡ Overlord Battle": "login.overlordbattle.com",
    "👹 Dark Empire": "account.darkempire.com",
    "⚔️ Eternal Battleground": "login.eternalbattleground.com",
    "🎮 Void War": "login.voidwar.com",
    "🔥 Clash of Warriors": "account.clashofwarriors.com",
    "⚔️ Chaos Champions": "login.chaoschampions.com",
    "🔥 Destiny Clash": "login.destinyclash.com",
    "⚔️ Legacy of Legends": "login.legacyoflegends.com",
    "🔥 Mythical War": "login.mythicalwar.com",
    "⚔️ Inferno Clash": "login.infernoclash.com",
    "🔥 Eternal Champions": "login.eternalchampions.com",
    "⚡ Heroic Battle": "login.heroicbattle.com",
    "🔥 Storm League": "login.stormleague.com",
    "⚔️ Warzone Arena": "login.warzonearena.com",
    "🔥 Supernova MOBA": "login.supernovamoba.com",
    "⚡ Celestial Clash": "login.celestialclash.com",
    "🔥 Doom League": "login.doomleague.com",
    "⚔️ Arena Titans": "login.arenatitans.com",
    "🔥 Legacy Brawlers": "login.legacybrawlers.com",
    "⚔️ Mythic Champions": "login.mythicchampions.com",
    "🔥 Warpath MOBA": "login.warpathmoba.com",
    "⚡ Shadow Empire": "login.shadowempire.com",
    "🔥 Thunderstrike MOBA": "login.thunderstrikemoba.com",
    "⚔️ Hero Brawl": "login.herobrawl.com",
    "🔥 Cosmic Legends": "login.cosmiclegends.com",
    "⚡ Galactic Arena": "login.galacticarena.com",
    "🔥 CyberWar MOBA": "login.cyberwarmoba.com",
    "⚔️ Abyss Titans": "login.abysstitans.com"
},
     "🔫 FPS": {
    "🛡️ Call of Duty: Warzone": "login.callofduty.com",
    "🔥 Call of Duty: Modern Warfare III": "login.callofduty.com",
    "🔫 Call of Duty: Mobile": "account.callofduty.com",
    "⚔️ Battlefield 2042": "login.ea.com",
    "🎯 Battlefield V": "login.ea.com",
    "🛡️ Battlefield 1": "login.ea.com",
    "🚀 Halo Infinite": "login.xbox.com",
    "🔥 Halo: The Master Chief Collection": "login.xbox.com",
    "🎮 Rainbow Six Siege": "login.ubisoft.com",
    "🔫 Rainbow Six Extraction": "login.ubisoft.com",
    "⚔️ Counter-Strike 2 (CS2)": "account.steampowered.com",
    "🔥 Counter-Strike: Global Offensive (CS:GO)": "account.steampowered.com",
    "🎯 Valorant": "login.riotgames.com",
    "🚀 Overwatch 2": "account.blizzard.com",
    "🔫 Overwatch": "account.blizzard.com",
    "🔥 DOOM Eternal": "login.bethesda.net",
    "💀 DOOM (2016)": "login.bethesda.net",
    "🎮 Quake Champions": "login.bethesda.net",
    "🚀 Quake Live": "login.bethesda.net",
    "🛡️ Apex Legends": "login.ea.com",
    "⚔️ Titanfall 2": "login.ea.com",
    "🎯 Titanfall": "login.ea.com",
    "🔫 Warface": "login.my.games",
    "🔥 Escape from Tarkov": "login.escapefromtarkov.com",
    "🎮 Destiny 2": "login.bungie.net",
    "💀 Destiny": "login.bungie.net",
    "🚀 Metro Exodus": "account.metrothegame.com",
    "🔫 Metro Last Light": "account.metrothegame.com",
    "⚔️ Metro 2033": "account.metrothegame.com",
    "🔥 Far Cry 6": "login.ubisoft.com",
    "🎯 Far Cry 5": "login.ubisoft.com",
    "🚀 Far Cry 4": "login.ubisoft.com",
    "🔫 Far Cry 3": "login.ubisoft.com",
    "⚔️ Left 4 Dead 2": "account.steampowered.com",
    "🔥 Left 4 Dead": "account.steampowered.com",
    "🎮 Back 4 Blood": "login.wbgames.com",
    "🚀 PAYDAY 3": "login.starbreeze.com",
    "🔫 PAYDAY 2": "login.starbreeze.com",
    "⚔️ Insurgency: Sandstorm": "account.focus-entmt.com",
    "🔥 Insurgency": "account.focus-entmt.com",
    "🎯 Squad": "account.joinsquad.com",
    "🚀 Ready or Not": "account.voidinteractive.net",
    "🔫 World War 3": "login.my.games",
    "⚔️ The Cycle: Frontier": "account.yager.de",
    "🔥 Black Mesa": "account.crowbarcollective.com",
    "🎮 Half-Life: Alyx": "account.steampowered.com",
    "🚀 Half-Life 2": "account.steampowered.com",
    "🔫 Half-Life": "account.steampowered.com",
    "⚔️ Shadow Warrior 3": "account.devolverdigital.com",
    "🔥 Shadow Warrior 2": "account.devolverdigital.com",
    "🎯 Shadow Warrior": "account.devolverdigital.com",
    "🚀 Serious Sam 4": "account.croteam.com",
    "🔫 Serious Sam 3": "account.croteam.com",
    "⚔️ Serious Sam 2": "account.croteam.com",
    "🔥 Rising Storm 2: Vietnam": "account.tripwireinteractive.com",
    "🎮 Killing Floor 2": "account.tripwireinteractive.com",
    "🚀 Killing Floor": "account.tripwireinteractive.com",
    "🔫 SWAT 4": "account.irrationalgames.com",
    "⚔️ Project Warlock": "account.buckshotsoftware.com",
    "🔥 Trepang2": "account.trepang2.com",
    "🎯 Bright Memory: Infinite": "account.playism.com",
    "🚀 Ghostrunner 2": "account.505games.com",
    "🔫 Ghostrunner": "account.505games.com",
    "⚔️ Roboquest": "account.rkadegg.com",
    "🔥 Severed Steel": "account.digerati.games",
    "🎮 Superhot: Mind Control Delete": "account.superhotgame.com",
    "🚀 Superhot": "account.superhotgame.com",
    "🔫 Amid Evil": "account.indefatigable.com",
    "⚔️ Ultrakill": "account.newblood.games",
    "🔥 Dusk": "account.newblood.games",
    "🎯 Ion Fury": "account.3drealms.com",
    "🚀 Wrath: Aeon of Ruin": "account.3drealms.com",
    "🔫 GTTOD: Get to the Orange Door": "account.hitcents.com",
    "⚔️ Desync": "account.theforegone.com",
    "🔥 Intruder": "account.superbossgames.com",
    "🎮 Midnight Ghost Hunt": "account.coffeestain.com",
    "🚀 Devil Daggers": "account.sorath.com",
    "🔫 Post Void": "account.ycjc.com",
    "⚔️ Blood: Fresh Supply": "account.nightdivestudios.com",
    "🔥 Turok 2: Seeds of Evil": "account.nightdivestudios.com",
    "🎯 Turok": "account.nightdivestudios.com",
    "🚀 PowerSlave Exhumed": "account.nightdivestudios.com",
    "🔫 Prodeus": "account.boundingboxsoftware.com",
    "⚔️ Hedon Bloodrite": "account.hedonbloodrite.com",
    "🔥 Dread Templar": "account.fulqrum.com",
    "🎮 Chasm: The Rift": "account.sneg.com",
    "🚀 Ion Fury: Aftershock": "account.3drealms.com"
},
    "🏗️ SIMULATION GAMES": {
    "🏡 The Sims 4": "login.ea.com",
    "🏠 The Sims 3": "login.ea.com",
    "🏗️ Cities: Skylines II": "account.paradoxinteractive.com",
    "🌆 Cities: Skylines": "account.paradoxinteractive.com",
    "🚜 Farming Simulator 22": "account.giants-software.com",
    "🚜 Farming Simulator 19": "account.giants-software.com",
    "✈️ Microsoft Flight Simulator": "login.xbox.com",
    "✈️ X-Plane 12": "account.x-plane.com",
    "🚀 Kerbal Space Program 2": "account.private-division.com",
    "🚀 Kerbal Space Program": "account.private-division.com",
    "🌿 Planet Zoo": "login.frontierstore.net",
    "🦕 Jurassic World Evolution 2": "login.frontierstore.net",
    "🎢 Planet Coaster": "login.frontierstore.net",
    "🎡 RollerCoaster Tycoon Classic": "account.atari.com",
    "🎢 RollerCoaster Tycoon 3": "account.frontierstore.net",
    "🏡 House Flipper": "account.empireinteractive.com",
    "🏗️ Construction Simulator": "account.astragon.com",
    "🚂 Train Simulator Classic": "account.dovetailgames.com",
    "🚅 Train Sim World 4": "account.dovetailgames.com",
    "🚌 Bus Simulator 21": "account.astragon.com",
    "🚖 Taxi Life: A City Driving Simulator": "account.simteract.com",
    "🚛 Euro Truck Simulator 2": "account.scssoft.com",
    "🚚 American Truck Simulator": "account.scssoft.com",
    "🚑 Emergency 20": "account.sixteen-tons.com",
    "🛳️ Ship Simulator Extremes": "account.paradoxinteractive.com",
    "⛵ Sailaway: The Sailing Simulator": "account.sailawaysimulator.com",
    "🚤 Fishing Planet": "account.fishingplanet.com",
    "🎣 Ultimate Fishing Simulator 2": "account.ultfishsim.com",
    "🎸 Rocksmith+ (Guitar Sim)": "login.ubisoft.com",
    "🎤 Let's Sing 2024": "account.lets-sing.com",
    "🎹 Synthesia (Piano Sim)": "account.synthesiagame.com",
    "🔬 PC Building Simulator 2": "account.epicgames.com",
    "💻 PC Creator 2": "account.ultraandre.com",
    "🚀 Spaceflight Simulator": "account.steampowered.com",
    "🔩 Car Mechanic Simulator 2021": "account.reddotgames.com",
    "🏎️ My Summer Car": "account.steampowered.com",
    "🛠️ Junkyard Simulator": "account.playway.com",
    "🏗️ Bridge Constructor Portal": "account.headupgames.com",
    "🎨 Painter Simulator": "account.nacon.com",
    "🏠 Home Designer - Makeover Blast": "account.scopely.com",
    "🛠️ Gas Station Simulator": "account.drago-entertainment.com",
    "🛠️ PowerWash Simulator": "account.square-enix.com",
    "🚀 Hardspace: Shipbreaker": "account.focus-entmt.com",
    "🛠️ Planet Crafter": "account.steampowered.com",
    "🏕️ Lumberjack’s Dynasty": "account.steampowered.com",
    "🛠️ Gold Rush: The Game": "account.steampowered.com",
    "🏍️ Motorcycle Mechanic Simulator 2021": "account.playway.com",
    "🏡 Hotel Renovator": "account.focus-entmt.com",
    "🏚️ House Builder": "account.playway.com",
    "🏚️ Demolish & Build 2018": "account.playway.com",
    "🔧 Car Detailing Simulator": "account.steampowered.com",
    "🚢 Port Royale 4": "account.kalypsomedia.com",
    "🛳️ UBOAT": "account.deepsilver.com",
    "🚀 Universe Sandbox": "account.universesandbox.com",
    "🪐 SpaceEngine": "account.steampowered.com",
    "🌍 Eco - Global Survival Game": "account.strangeloopgames.com",
    "🔬 Factorio": "account.wube.com",
    "🛰️ Dyson Sphere Program": "account.gamera.com",
    "🔋 Satisfactory": "account.coffeestain.com",
    "⚡ Power to the People": "account.steampowered.com",
    "🏗️ Factory Town": "account.steampowered.com",
    "🚜 Farm Manager 2021": "account.steampowered.com",
    "🏞️ Banished": "account.shiningrocksoftware.com",
    "?? The Wandering Village": "account.strayfawn.com",
    "🏚️ Frostpunk": "account.11bitstudios.com",
    "🌆 Surviving Mars": "account.paradoxinteractive.com",
    "⛺ The Long Dark": "account.hinterlandgames.com",
    "🏗️ Workers & Resources: Soviet Republic": "account.3division.net",
    "🌾 Tropico 6": "account.kalypsomedia.com",
    "🏝️ Stranded Deep": "account.beamteamgames.com",
    "🏗️ RimWorld": "account.ludeon.com",
    "🚀 Oxygen Not Included": "account.kleientertainment.com",
    "🐾 Zoo Tycoon": "account.xbox.com",
    "🎢 Parkitect": "account.themeparkitect.com",
    "🚜 Real Farm": "account.sodesk.com",
    "🎯 Mad Games Tycoon 2": "account.eggcodegames.com",
    "🚀 Interstellar Rift": "account.steampowered.com",
    "🏗️ Anno 1800": "login.ubisoft.com",
    "🏗️ Anno 2205": "login.ubisoft.com",
    "🏗️ Anno 2070": "login.ubisoft.com",
    "⚡ Voxel Tycoon": "account.steampowered.com",
    "🏗️ Constructor Plus": "account.system3.com",
    "🌏 The Guild 3": "account.thqnordic.com",
    "🏚️ Project Highrise": "account.kasedogames.com",
    "🚧 Big Ambitions": "account.hovgaardgames.com",
    "📦 Goods Inc.": "account.industrygames.com",
    "🏭 Little Big Workshop": "account.thqnordic.com",
    "🏗️ Evil Genius 2": "account.rebellion.com",
    "🚀 Industry Giant 2": "account.1cgames.com",
    "🚀 Space Haven": "account.bugbyte.com",
    "⚙️ Automation - The Car Company Tycoon Game": "account.camshaftsoftware.com",
    "🏗️ Software Inc.": "account.coredumping.com",
    "🎢 Park Beyond": "account.bandainamcoent.com"
},
    "🏕️ SURVIVAL GAMES": {
    "🌲 The Forest": "account.endnightgames.com",
    "🌲 Sons of the Forest": "account.endnightgames.com",
    "🐺 The Long Dark": "account.hinterlandgames.com",
    "🏝️ Stranded Deep": "account.beamteamgames.com",
    "🦕 ARK: Survival Evolved": "account.studiowildcard.com",
    "🦕 ARK: Survival Ascended": "account.studiowildcard.com",
    "🛠️ Rust": "account.facepunch.com",
    "⛏️ 7 Days to Die": "account.thefunpimps.com",
    "🚀 Oxygen Not Included": "account.kleientertainment.com",
    "🏗️ Satisfactory": "account.coffeestain.com",
    "🏗️ RimWorld": "account.ludeon.com",
    "🌿 Green Hell": "account.creepyjar.com",
    "🏝️ Raft": "account.redbeetinteractive.com",
    "🏚️ Project Zomboid": "account.theindiestone.com",
    "🌍 Eco - Global Survival": "account.strangeloopgames.com",
    "🐾 Don't Starve": "account.kleientertainment.com",
    "🐾 Don't Starve Together": "account.kleientertainment.com",
    "🛠️ Survivalist: Invisible Strain": "account.steampowered.com",
    "🔫 SCUM": "account.gamepires.com",
    "🏹 Mist Survival": "account.ratiogames.com",
    "🎯 Deadside": "account.badpixel.com",
    "👽 The Solus Project": "account.teotlstudios.com",
    "🚀 Space Engineers": "account.keenswh.com",
    "🌌 Starbound": "account.chucklefish.com",
    "⛏️ Subnautica": "account.unknownworlds.com",
    "⛏️ Subnautica: Below Zero": "account.unknownworlds.com",
    "🔬 The Planet Crafter": "account.steampowered.com",
    "🏕️ Survive the Nights": "account.a2zinteractive.com",
    "🔫 Miscreated": "account.entradainteractive.com",
    "🧟 DayZ": "account.bohemia.net",
    "🧟 State of Decay 2": "account.xbox.com",
    "🧟 State of Decay": "account.xbox.com",
    "👿 Resident Evil Village": "account.capcom.com",
    "🧟 Resident Evil 4 Remake": "account.capcom.com",
    "👹 Resident Evil 7": "account.capcom.com",
    "🧟 Dying Light": "account.techland.com",
    "🧟 Dying Light 2": "account.techland.com",
    "🔫 Metro Exodus": "account.metrothegame.com",
    "🔫 Metro Last Light": "account.metrothegame.com",
    "🌆 This War of Mine": "account.11bitstudios.com",
    "👁️ Darkwood": "account.steampowered.com",
    "🚢 Sunkenland": "account.steampowered.com",
    "🚀 No Man’s Sky": "account.nomanssky.com",
    "🛶 Breathedge": "account.redruins.com",
    "🏕️ The Wild Eight": "account.hypeTrainDigital.com",
    "🎭 CryoFall": "account.atomictorch.com",
    "🧪 Biomutant": "account.thqnordic.com",
    "🦠 Pandemic Express": "account.tinybuild.com",
    "⚰️ Graveyard Keeper": "account.lazybeargames.com",
    "🔫 Chernobylite": "account.thefarm51.com",
    "🚀 Hellion": "account.zerogravitygames.com",
    "⚡ The Infected": "account.steampowered.com",
    "🧟 Left 4 Dead 2": "account.steampowered.com",
    "🧟 Left 4 Dead": "account.steampowered.com",
    "🔫 Hunt: Showdown": "account.crytek.com",
    "💀 The Callisto Protocol": "account.krafton.com",
    "🧟 The Walking Dead: Saints & Sinners": "account.skybound.com",
    "🚀 Icarus": "account.rocketwerkz.com",
    "🛡️ Enshrouded": "account.keplerinteractive.com",
    "🏹 Medieval Dynasty": "account.toplitz-productions.com",
    "🌲 Muck": "account.dani.dev",
    "🔪 Sons of the Forest": "account.endnightgames.com",
    "🔮 Conan Exiles": "account.funcom.com",
    "🦖 Path of Titans": "account.alderongames.com",
    "🐍 Green Hell VR": "account.creepyjar.com",
    "🦖 The Isle": "account.theisle.com",
    "🚪 Phasmophobia": "account.kineticgames.com",
    "👻 Devour": "account.steampowered.com",
    "💀 Dark and Darker": "account.irongatestudio.com",
    "🦈 Depth": "account.steampowered.com",
    "🌍 V Rising": "account.stunlock.com",
    "👻 Bigfoot": "account.cyberlightgame.com",
    "🚀 Star Citizen": "account.robertsspaceindustries.com",
    "🏝️ Castaway Paradise": "account.steampowered.com",
    "🛶 Windbound": "account.deep-silver.com",
    "🐉 Outward": "account.ninedots.com",
    "🔬 Nova Lands": "account.steampowered.com",
    "🌍 Planet Crafter": "account.steampowered.com",
    "🎢 Parkasaurus": "account.washbearstudio.com",
    "⚔️ Valheim": "account.steampowered.com",
    "💣 Survarium": "account.vostokgames.com",
    "🏕️ The Survivalists": "account.team17.com",
    "🔦 Lightmatter": "account.steampowered.com",
    "💀 The Black Death": "account.smallimpactgames.com",
    "🧟 Infestation: The New Z": "account.fredawest.com",
    "🦠 Pandemic Express": "account.tinybuild.com",
    "🌌 Space Haven": "account.bugbyte.com",
    "⚙️ SCUM": "account.gamepires.com",
    "🌍 Mortal Online 2": "account.mortalonline.com",
    "🛸 Generation Zero": "account.systemicreaction.com",
    "⚡ Don't Starve Newhome": "account.tencent.com",
    "🦖 The Stomping Land": "account.steampowered.com",
    "🎭 Identity": "account.identityrpg.com"
},
   "🎨 EDITING": {
    "📷 Adobe Photoshop": "account.adobe.com",
    "📷 Adobe Lightroom": "account.adobe.com",
    "📷 Adobe Illustrator": "account.adobe.com",
    "📷 Adobe Express": "account.adobe.com",
    "📷 CorelDRAW": "account.corel.com",
    "📷 Affinity Photo": "account.serif.com",
    "📷 Affinity Designer": "account.serif.com",
    "📷 GIMP": "account.gimp.org",
    "📷 Krita": "account.krita.org",
    "📷 Canva": "account.canva.com",
    "📷 Pixlr": "account.pixlr.com",
    "📷 Fotor": "account.fotor.com",
    "📷 Photopea": "account.photopea.com",
    "📷 BeFunky": "account.befunky.com",
    "📷 Snapseed": "account.snapseed.com",
    "📷 PicsArt": "account.picsart.com",
    "📷 VSCO": "account.vsco.co",
    "📷 Toolwiz Photos": "account.toolwiz.com",
    "📷 Polarr": "account.polarr.com",
    "🎬 Adobe Premiere Pro": "account.adobe.com",
    "🎬 Adobe After Effects": "account.adobe.com",
    "🎬 DaVinci Resolve": "account.blackmagicdesign.com",
    "🎬 Final Cut Pro": "account.apple.com",
    "🎬 Sony Vegas Pro": "account.vegascreativesoftware.com",
    "🎬 Camtasia": "account.techsmith.com",
    "🎬 Filmora": "account.wondershare.com",
    "🎬 HitFilm Express": "account.fxhome.com",
    "🎬 OpenShot": "account.openshot.org",
    "🎬 Shotcut": "account.shotcut.org",
    "🎬 VSDC Free Video Editor": "account.videosoftdev.com",
    "🎬 Movavi Video Editor": "account.movavi.com",
    "🎬 CapCut": "account.capcut.com",
    "🎬 Kinemaster": "account.kinemaster.com",
    "🎬 InShot": "account.inshot.com",
    "🎬 PowerDirector": "account.cyberlink.com",
    "🎬 LumaFusion": "account.lumatouch.com",
    "🎬 WeVideo": "account.wevideo.com",
    "🎬 Magisto": "account.magisto.com",
    "🎬 Alight Motion": "account.alightcreative.com",
    "🎬 VN Video Editor": "account.vlognow.me",
    "🎬 YouCut": "account.youcut.com",
    "🎬 VivaVideo": "account.vivavideo.com",
    "🎬 ActionDirector": "account.cyberlink.com",
    "🎬 Funimate": "account.funimate.com",
    "🎬 Vinkle": "account.vinkle.com",
    "🎬 Splice": "account.splice.com",
    "🎵 Adobe Audition": "account.adobe.com",
    "🎵 FL Studio": "account.image-line.com",
    "🎵 Ableton Live": "account.ableton.com",
    "🎵 Logic Pro": "account.apple.com",
    "🎵 Pro Tools": "account.avid.com",
    "🎵 GarageBand": "account.apple.com",
    "🎵 Audacity": "account.audacityteam.org",
    "🎵 Cubase": "account.steinberg.net",
    "🎵 Studio One": "account.presonus.com",
    "🎵 Reaper": "account.reaper.fm",
    "🎵 WavePad": "account.nch.com.au",
    "🎵 BandLab": "account.bandlab.com",
    "🎵 AudioLab": "account.audiolab.com",
    "🎵 Lexis Audio Editor": "account.lexisaudio.com",
    "🖥️ Blender": "account.blender.org",
    "🖥️ Autodesk Maya": "account.autodesk.com",
    "🖥️ Autodesk 3ds Max": "account.autodesk.com",
    "🖥️ Cinema 4D": "account.maxon.net",
    "🖥️ ZBrush": "account.pixologic.com",
    "🖥️ SketchUp": "account.sketchup.com",
    "🖥️ Unity": "account.unity.com",
    "🖥️ Unreal Engine": "account.epicgames.com",
    "🖥️ Houdini": "account.sidefx.com",
    "🖥️ Modo": "account.foundry.com",
    "🖥️ Marvelous Designer": "account.marvelousdesigner.com",
    "🖥️ Substance Painter": "account.adobe.com",
    "🖥️ KeyShot": "account.keyshot.com",
    "🖥️ Moho (Anime Studio)": "account.smithmicro.com",
    "🖥️ Toon Boom Harmony": "account.toonboom.com",
    "🖼️ Figma": "account.figma.com",
    "🖼️ Sketch": "account.sketch.com",
    "🖼️ InVision": "account.invisionapp.com",
    "🖼️ Adobe XD": "account.adobe.com",
    "🖼️ Procreate": "account.procreate.art",
    "🖼️ Vectornator": "account.vectornator.io",
    "🖼️ ArtRage": "account.artrage.com",
    "🖼️ MediBang Paint": "account.medibang.com",
    "🖼️ Rebelle": "account.escapemotions.com",
    "🖼️ PaintTool SAI": "account.systemax.jp",
    "🖼️ Corel Painter": "account.corel.com",
    "📑 Adobe Acrobat": "account.adobe.com",
    "📑 Nitro PDF": "account.gonitro.com",
    "📑 Foxit PDF Editor": "account.foxit.com",
    "📑 PDFescape": "account.pdfescape.com",
    "📑 Smallpdf": "account.smallpdf.com",
    "📑 Sejda PDF Editor": "account.sejda.com",
    "📑 PDF-XChange Editor": "account.tracker-software.com"
},
    "💰TOP-UP": {
    "🔥 CodaShop": "codashop.com",
    "🔥 UniPin": "unipin.com",
    "🔥 Razer Gold": "gold.razer.com",
    "🔥 SEAGM (Southeast Asia Gaming Market)": "seagm.com",
    "🔥 OffGamers": "offgamers.com",
    "🔥 G2G Recharge": "g2g.com",
    "🔥 Ding Top-Up": "ding.com",
    "🔥 Recharge.com": "recharge.com",
    "🔥 Games Kharido": "gameskharido.in",
    "🔥 TopUp.com": "topup.com",
    "🔥 MobileRecharge": "mobilerecharge.com",
    "🔥 Kinguin Gift Cards": "kinguin.net",
    "🔥 Gamivo Recharge": "gamivo.com",
    "🔥 PlayAsia Top-Up": "play-asia.com",
    "🔥 Midasbuy": "midasbuy.com",
    "🔥 U7BUY Recharge": "u7buy.com",
    "🔥 Xsolla Recharge": "xsolla.com",
    "🔥 MyCard": "mycard520.com.tw",
    "🔥 Mobile Legends Recharge": "recharge.mobilelegends.com",
    "🔥 Free Fire Top-Up": "shop2game.com",
    "🔥 PUBG Mobile UC": "pubgmobile.com/pay",
    "🔥 Garena Shells": "shells.garena.com",
    "🔥 Riot Games Valorant Points": "pay.riotgames.com",
    "🔥 Steam Wallet Recharge": "store.steampowered.com",
    "🔥 PlayStation Store Top-Up": "store.playstation.com",
    "🔥 Xbox Live Gift Cards": "xbox.com",
    "🔥 Nintendo eShop Top-Up": "nintendo.com",
    "🔥 Apple iTunes Gift Cards": "apple.com",
    "🔥 Google Play Recharge": "play.google.com",
    "🔥 Amazon Gift Card Recharge": "amazon.com/gc",
    "🔥 Roblox Robux Recharge": "roblox.com/redeem",
    "🔥 Fortnite V-Bucks": "epicgames.com/store",
    "🔥 Call of Duty CP Recharge": "callofduty.com/redeem",
    "🔥 Apex Legends Coins": "ea.com/games/apex-legends",
    "🔥 FIFA Points Recharge": "ea.com/fifa",
    "🔥 Genshin Impact Genesis Crystals": "genshin.hoyoverse.com/en/gift",
    "🔥 Hoyoverse Recharge (Honkai, Zenless Zone Zero)": "hoyoverse.com",
    "🔥 EA Play Subscription": "ea.com/ea-play",
    "🔥 Blizzard Battle.net Balance": "battle.net",
    "🔥 Riot Games Wild Rift Recharge": "pay.riotgames.com",
    "🔥 World of Warcraft Subscription": "us.battle.net/wow",
    "🔥 Ragnarok M Eternal Love Recharge": "ro.com/recharge",
    "🔥 MU Origin 3 Recharge": "mu3.com/recharge",
    "🔥 Tower of Fantasy Recharge": "recharge.levelinfinite.com",
    "🔥 Rise of Kingdoms Recharge": "rok.lilith.com",
    "🔥 State of Survival Recharge": "stateofsurvival.com/topup",
    "🔥 Clash of Clans Recharge": "clashofclans.com",
    "🔥 Clash Royale Gems": "clashroyale.com",
    "🔥 Lords Mobile Recharge": "lordsmobile.igg.com",
    "🔥 Summoners War Recharge": "summonerswar.com",
    "🔥 Hearthstone Packs": "playhearthstone.com",
    "🔥 Diablo Immortal Orbs": "diabloimmortal.com",
    "🔥 Ragnarok X: Next Generation Recharge": "roxnextgen.com",
    "🔥 Lineage 2 Revolution Recharge": "lineage2.com",
    "🔥 Dragon Raja Recharge": "dragonraja.com",
    "🔥 Black Desert Mobile Pearls": "blackdesertm.com",
    "🔥 Mobile Legends Starlight Membership": "mobilelegends.com/starlight",
    "🔥 Arena of Valor Recharge": "aov.com",
    "🔥 Pokémon Unite Recharge": "pokemonunite.com",
    "🔥 Marvel Future Fight Recharge": "marvelfuturefight.com",
    "🔥 Dragon Ball Legends Recharge": "dragonball-legends.com",
    "🔥 Tiktok Coins": "tiktok.com/recharge",
    "🔥 Likee Diamonds": "likee.com/topup",
    "🔥 Bigo Live Recharge": "bigo.tv/topup",
    "🔥 Twitch Bits Recharge": "twitch.tv/bits",
    "🔥 VK Pay Recharge": "vkpay.ru",
    "🔥 Yandex Money Recharge": "money.yandex.ru",
    "🔥 WebMoney Top-Up": "webmoney.com",
    "🔥 PayPal Gift Cards": "paypal.com/gifts",
    "🔥 Skrill Recharge": "skrill.com",
    "🔥 Neteller Top-Up": "neteller.com",
    "🔥 Binance Gift Cards": "binance.com/giftcards",
    "🔥 Trust Wallet Crypto Recharge": "trustwallet.com",
    "🔥 Coinbase Crypto Top-Up": "coinbase.com",
    "🔥 Payoneer Balance Recharge": "payoneer.com",
    "🔥 Wise (TransferWise) Top-Up": "wise.com",
    "🔥 Alipay Recharge": "alipay.com",
    "🔥 WeChat Pay Top-Up": "wechat.com",
    "🔥 LINE Pay Recharge": "line.me/en/pay",
    "🔥 GCash Top-Up": "gcash.com",
    "🔥 Maya (PayMaya) Recharge": "maya.ph",
    "🔥 ShopeePay Top-Up": "shopee.ph/m/shopeepay",
    "🔥 Lazada Wallet Recharge": "lazada.com.ph/lazadawallet",
    "🔥 TrueMoney Wallet": "truemoney.com",
    "🔥 PayMomo Top-Up": "paymomo.com",
    "🔥 GoPay Recharge": "gopay.co.id",
    "🔥 Dana Wallet Recharge": "dana.id",
    "🔥 OVO Wallet Top-Up": "ovo.id",
    "🔥 GrabPay Recharge": "grab.com/pay",
    "🔥 M-Pesa Mobile Money": "vodacom.co.tz/mpesa",
    "🔥 Airtel Money Recharge": "airtel.com/airtel-money",
    "🔥 Orange Money Recharge": "orangemoney.com",
    "🔥 Telenor Easypaisa": "easypaisa.com.pk",
    "🔥 JazzCash Mobile Recharge": "jazzcash.com.pk"
    },
    "🚀 ON GAME": {
    "🕹️ Steam": "store.steampowered.com",
    "🎮 Epic Games": "epicgames.com",
    "🟢 Xbox Live": "xbox.com",
    "🎮 PlayStation Network": "playstation.com",
    "🎮 Nintendo Online": "nintendo.com",
    "🌀 Ubisoft Connect": "ubisoftconnect.com",
    "🔥 Battle.net": "battle.net",
    "⚡ EA Play": "ea.com/ea-play",
    "⚔️ Riot Games": "login.riotgames.com",
    "🛑 Rockstar Social Club": "socialclub.rockstargames.com",
    "🌌 Bethesda.net": "bethesda.net",
    "⚓ Wargaming (WoT, WoWS)": "wargaming.net",
    "🎭 Nexon Games": "nexon.net",
    "🛡️ Garena": "garena.com",
    "💳 Xsolla": "xsolla.com",
    "🐉 World of Warcraft": "worldofwarcraft.com",
    "🌀 Final Fantasy XIV": "secure.square-enix.com",
    "📜 Elder Scrolls Online": "account.elderscrollsonline.com",
    "⚔️ Black Desert Online": "blackdesertonline.com",
    "🏰 Guild Wars 2": "account.arena.net",
    "🎭 Runescape": "runescape.com",
    "👹 Lost Ark": "lostark.game.onstove.com",
    "🔱 Warframe": "warframe.com",
    "🔫 Destiny 2": "bungie.net",
    "🚀 Star Wars: The Old Republic": "swtor.com",
    "🐺 Monster Hunter Rise": "monsterhunter.com",
    "💀 Diablo IV": "diablo4.blizzard.com",
    "🌌 EVE Online": "secure.eveonline.com",
    "🎯 Valorant": "playvalorant.com",
    "🔫 Counter-Strike 2": "store.steampowered.com/app/730",
    "🔫 Call of Duty Warzone": "callofduty.com",
    "🔫 PUBG: Battlegrounds": "accounts.pubg.com",
    "🔫 Apex Legends": "ea.com/games/apex-legends",
    "🔫 Rainbow Six Siege": "ubisoftconnect.com",
    "🎮 Overwatch 2": "playoverwatch.com",
    "🚁 Battlefield 2042": "ea.com/games/battlefield",
    "🎯 Escape from Tarkov": "escapefromtarkov.com",
    "🔫 Crossfire": "crossfire.z8games.com",
    "🎯 Warface": "warface.com",
    "⚔️ League of Legends": "leagueoflegends.com",
    "⚔️ Dota 2": "dota2.com",
    "⚔️ Mobile Legends": "mobilelegends.com",
    "⚔️ Arena of Valor": "aov.com",
    "⚔️ Smite": "smitegame.com",
    "⚔️ Pokemon Unite": "pokemonunite.com",
    "🛠️ Minecraft": "minecraft.net",
    "🏗️ Roblox": "roblox.com",
    "🦸 Fortnite": "epicgames.com/fortnite",
    "🚜 Farming Simulator": "farming-simulator.com",
    "🏎️ Forza Horizon 5": "forzamotorsport.net",
    "🏎️ Need for Speed": "ea.com/games/need-for-speed",
    "🚀 Star Citizen": "robertsspaceindustries.com",
    "🦸 DC Universe Online": "dcuniverseonline.com",
    "💣 Team Fortress 2": "teamfortress.com",
    "🛡️ Paladins": "paladins.com",
    "🔪 Dead by Daylight": "deadbydaylight.com",
    "🌆 GTA Online": "rockstargames.com/gta-online",
    "🌍 The Sims 4": "ea.com/games/the-sims",
    "👨‍🚀 No Man’s Sky": "nomanssky.com",
    "⚔️ Elden Ring": "eldenring.com",
    "🌍 The Division 2": "ubisoftconnect.com",
    "🦾 Cyberpunk 2077": "cyberpunk.net",
    "🏰 Dragon Age": "ea.com/games/dragon-age",
    "🐉 Baldur's Gate 3": "baldursgate3.game",
    "🦾 Starfield": "bethesda.net",
    "🛸 Star Wars Jedi Survivor": "ea.com/games/starwars/jedi-survivor",
    "🌄 Red Dead Online": "rockstargames.com/reddeadonline",
    "⚔️ Elders Scrolls Legends": "elderscrollslegends.com",
    "🌀 Shadow Arena": "shadowarena.pearlabyss.com",
    "🎭 Phasmophobia": "phasmophobia.com",
    "🛡️ Chivalry 2": "chivalry2.com",
    "👑 Mount & Blade II": "mountandblade.com",
    "🔮 Magic: The Gathering Arena": "magic.wizards.com",
    "👨‍🎤 Rocksmith+": "rocksmith.com",
    "🐉 ARK: Survival Evolved": "ark.gamepedia.com",
    "💀 The Forest": "endnightgame.com",
    "🦠 Project Zomboid": "projectzomboid.com",
    "🚀 Kerbal Space Program": "kerbalspaceprogram.com",
    "🧟 7 Days to Die": "7daystodie.com",
    "👹 Hunt: Showdown": "huntshowdown.com",
    "🛸 Stellaris": "stellaris.com",
    "🗺️ Civilization VI": "civilization.com",
    "🌎 Age of Empires IV": "ageofempires.com",
    "⚔️ Total War: Warhammer III": "totalwar.com",
    "🧙‍♂️ Hogwarts Legacy": "hogwartslegacy.com",
    "🛠️ Cities Skylines II": "citiesskylines.com",
    "🕹️ Street Fighter 6": "streetfighter.com",
    "💥 Mortal Kombat 1": "mortalkombat.com",
    "🤖 Tekken 8": "tekken.com",
    "🎮 Guilty Gear Strive": "guiltygear.com",
    "🦸 Suicide Squad: Kill the Justice League": "suicidesquadgame.com"
},
    "🏅SPORT GAMES": {
    "⚽ FIFA Online": "fifa.com",
    "⚽ EA Sports FC": "ea.com/ea-sports-fc",
    "⚽ eFootball (PES)": "konami.com/efootball",
    "⚽ Football Manager": "footballmanager.com",
    "⚽ Top Eleven": "topeleven.com",
    "⚽ Dream League Soccer": "dls.com",
    "⚽ Score! Hero": "scorehero.com",
    "🏀 NBA 2K Series": "nba.2k.com",
    "🏀 NBA Live": "ea.com/games/nba-live",
    "🏀 Street Basketball Association": "sba.com",
    "🏀 Dunk Hit": "dunkhit.com",
    "🏈 Madden NFL": "ea.com/games/madden-nfl",
    "🏈 Retro Bowl": "retrobowlgame.com",
    "🏈 Axis Football": "axisgames.com",
    "⚾ MLB The Show": "mlbtheshow.com",
    "⚾ R.B.I. Baseball": "rbi.com",
    "⚾ Baseball 9": "baseball9.com",
    "⚾ Super Mega Baseball": "supermegabaseball.com",
    "🎾 Tennis Clash": "tennisclash.com",
    "🎾 Virtua Tennis": "sega.com/virtuatennis",
    "🎾 AO Tennis 2": "aotennis.com",
    "⛳ PGA Tour 2K": "pgatour.2k.com",
    "⛳ Golf Clash": "golfclash.com",
    "⛳ Mini Golf King": "minigolfking.com",
    "🏎️ F1 24": "ea.com/games/f1",
    "🏎️ Forza Horizon 5": "forzamotorsport.net",
    "🏎️ Gran Turismo 7": "gran-turismo.com",
    "🏎️ Need for Speed": "ea.com/games/need-for-speed",
    "🏎️ WRC (World Rally Championship)": "wrc.com",
    "🏎️ Real Racing 3": "realracing.com",
    "🏎️ Assetto Corsa": "assettocorsa.net",
    "🏎️ Project CARS": "projectcarsgame.com",    
    "🚴 Tour de France": "tourdefrancegame.com",
    "🚴 Pro Cycling Manager": "procymanager.com",
    "🥊 UFC 5": "ea.com/games/ufc",
    "🥊 Fight Night": "ea.com/games/fight-night",
    "🥊 Boxing Star": "boxingstar.com",
    "🤼 WWE 2K Series": "wwe.2k.com",
    "🤼 Fire Pro Wrestling": "fpw.com",
    "🤼 Wrestling Revolution": "wrestlingrevolution.com",    
    "🥋 EA Sports UFC": "ea.com/games/ufc",
    "🥋 Karate King Fight": "karateking.com",
    "🥋 Bushido Blade": "bushidoblade.com",    
    "🎳 PBA Bowling": "pba.com/bowling",
    "🎳 Bowling King": "bowlingking.com",
    "🏇 Rival Stars Horse Racing": "rivalstars.com",
    "🏇 Horse Racing Manager": "horseracingmanager.com",
    "🏒 NHL 24": "ea.com/games/nhl",
    "🏒 Hockey Nations": "hockeynations.com",
    "🏓 Table Tennis Touch": "tabletennistouch.com",
    "🏓 Ping Pong Fury": "pingpongfury.com",
    "🏹 Archery King": "archeryking.com",
    "🏹 Archery Master 3D": "archerymaster.com",
    "🎯 Darts of Fury": "dartsoffury.com",   
    "🤾 Handball 21": "handball.com",
    "🤾 Ultimate Handball Manager": "uhm.com",
    "🚣 Rowing Simulator": "rowingsim.com",
    "🚣 Rowing Clash": "rowingclash.com",  
    "🏃 Track & Field Challenge": "trackfield.com",
    "🏃 Olympic Games Tokyo 2020": "olympicvideogames.com",
    "🎿 Steep (Ski & Snowboard)": "steep.ubisoft.com",
    "🎿 Snowboarding The Fourth Phase": "snowboardgame.com",  
    "🛹 Tony Hawk's Pro Skater": "tonyhawk.com",
    "🛹 Skate City": "skatecity.com",
    "🛶 Canoe Sprint": "canoesprint.com",
    "🎮 Sports Party (Nintendo)": "sports-party.com",
    "🎮 Mario Strikers: Battle League": "mariostrikers.com",
    "🛶 Rafting Extreme": "raftingextreme.com",
    "🏀 Street Hoops": "streethoops.com",
    "⚽ Soccer Stars": "soccerstars.com",
    "🏈 Touchdown Hero": "touchdownhero.com",
    "🎯 Disc Golf Valley": "discgolfvalley.com",
    "🏌️ Golf Star": "golfstar.com",
    "🏂 Snowboard Party": "snowboardparty.com",
    "🚴 BMX Freestyle Extreme": "bmxfreestyle.com",
    "🏹 Stickman Archery": "stickmanarchery.com",
    "🥊 Real Boxing 2": "realboxing.com",
    "🏆 Ultimate Tennis": "ultimatetennis.com",
    "🏆 Rugby Challenge": "rugbychallenge.com",
    "🏊 Swim Out": "swimoutgame.com",
    "🏊 Swim Race Simulator": "swimrace.com",
    "🚣 Extreme Kayak": "extremekayak.com",
    "🏉 World Rugby Manager": "worldrugbymanager.com",   
    "🏇 Derby Quest": "derbyquest.com",
    "🎿 Ski Safari": "skisafari.com",
    "🛹 Skater XL": "skaterxl.com",
    "⚽ Freestyle Football": "freestylefootball.com"
},
    "🏎️RACING GAMES": {
    "🏁 Forza Horizon 5": "forzamotorsport.net",
    "🏁 Forza Motorsport": "forza.net",
    "🏁 Gran Turismo 7": "gran-turismo.com",
    "🏁 Need for Speed Unbound": "ea.com/games/need-for-speed/unbound",
    "🏁 Need for Speed Heat": "ea.com/games/need-for-speed/heat",
    "🏁 Need for Speed Most Wanted": "ea.com/games/need-for-speed/most-wanted",
    "🏁 Need for Speed Underground 2": "ea.com/games/need-for-speed/underground-2",
    "🏁 Need for Speed Rivals": "ea.com/games/need-for-speed/rivals",
    "🏁 WRC (World Rally Championship)": "wrc.com",
    "🏁 Dirt 5": "dirtgame.com",
    "🏁 Dirt Rally 2.0": "dirtrally2.com",
    "🏁 GRID Legends": "ea.com/games/grid/legends",
    "🏁 GRID Autosport": "gridgame.com",
    "🏁 F1 24": "ea.com/games/f1",
    "🏁 F1 Manager 2023": "f1manager.com",
    "🏁 MotoGP 23": "motogp.com",
    "🏁 Ride 5": "ridevideogame.com",
    "🏁 TT Isle of Man: Ride on the Edge 3": "ttisleofman.com",
    "🏁 Assetto Corsa": "assettocorsa.net",
    "🏁 Assetto Corsa Competizione": "assettocorsa.it",
    "🏁 Project CARS 3": "projectcarsgame.com",
    "🏁 rFactor 2": "rfactor.net",
    "🏁 Automobilista 2": "automobilista2.com",
    "🏁 iRacing": "iracing.com",
    "🏁 NASCAR Heat 5": "nascarheat.com",
    "🏁 NASCAR 21: Ignition": "motorsportgames.com/nascar-21-ignition",
    "🏁 NHRA Championship Drag Racing": "nhragame.com",
    "🏁 Monster Energy Supercross": "supercrossthegame.com",
    "🏁 MXGP 2023": "mxgpvideogame.com",
    "🏁 Extreme Drift 2": "extremedrift.com",
    "🏁 CarX Drift Racing 2": "carx-drift.com",
    "🏁 Drift Hunters": "drifthunters.com",
    "🏁 FR Legends": "frlegends.com",
    "🏁 Revhead": "revheadgame.com",
    "🏁 Hot Wheels Unleashed": "hotwheelsunleashed.com",
    "🏁 KartRider: Drift": "kartrider.nexon.net",
    "🏁 Mario Kart 8 Deluxe": "mariokart.nintendo.com",
    "🏁 Crash Team Racing Nitro-Fueled": "crashbandicoot.com/crashteamracing",
    "🏁 Team Sonic Racing": "sonicthehedgehog.com/games/team-sonic-racing",
    "🏁 Wipeout Omega Collection": "wipeoutplaystation.com",
    "🏁 Hydro Thunder": "hydrothunder.com",
    "🏁 Split/Second": "splitsecond.com",
    "🏁 Burnout Paradise Remastered": "ea.com/games/burnout/burnout-paradise-remastered",
    "🏁 Midnight Club: Los Angeles": "rockstargames.com/midnightclub",
    "🏁 Test Drive Unlimited Solar Crown": "testdriveunlimited.com",
    "🏁 The Crew 2": "thecrew-game.ubisoft.com",
    "🏁 The Crew Motorfest": "thecrew-motorfest.ubisoft.com",
    "🏁 BeamNG.drive": "beamng.com",
    "🏁 Wangan Midnight Maximum Tune": "wanganmaxi-official.com",
    "🏁 Initial D Arcade Stage": "initiald.sega.com",
    "🏁 Speed Drifters": "speeddrifters.com",
    "🏁 Offroad Outlaws": "offroadoutlaws.com",
    "🏁 Hill Climb Racing 2": "hillclimbracing.com",
    "🏁 Rush Rally 3": "rushrally.com",
    "🏁 Rebel Racing": "rebelracing.com",
    "🏁 RaceRoom Racing Experience": "raceroom.com",
    "🏁 Motorcycle Real Simulator": "motorcyclesimulator.com",
    "🏁 Mad Skills Motocross 3": "madskillsmx.com",
    "🏁 Pocket Rally": "pocketrally.com",
    "🏁 Rebel Cops: Racing Wars": "racingwars.com",
    "🏁 Madalin Stunt Cars 3": "madalincars.com",
    "🏁 Police Chase Simulator": "policechasemania.com",
    "🏁 Cyber Truck Simulator": "cybertrucksim.com",
    "🏁 Top Drives": "topdrives.com",
    "🏁 SnowRunner": "snowrunner.com",
    "🏁 MudRunner": "mudrunner.com",
    "🏁 Spintires": "spintires.com",
    "🏁 Bigfoot Monster Truck": "bigfootracing.com",
    "🏁 Bus Simulator 2023": "bussimulator.com",
    "🏁 Taxi Sim 2023": "taxisim.com",
    "🏁 Euro Truck Simulator 2": "eurotrucksimulator2.com",
    "🏁 American Truck Simulator": "americantrucksimulator.com",
    "🏁 Motocross Madness": "motocrossmadness.com",
    "🏁 Rally Fury": "rallyfury.com",
    "🏁 Superbike Racing": "superbikeracing.com",
    "🏁 Super Toy Cars": "supertoycars.com",
    "🏁 Pocket Rally Offroad": "pocketrallyoffroad.com",
    "🏁 Nitro Nation Drag Racing": "nitronation.com",
    "🏁 Thumb Drift": "thumbdrift.com",
    "🏁 No Limit Drag Racing 2": "nolimitdragracing.com",
    "🏁 Racing Xtreme 2": "racingxtreme.com",
    "🏁 Beach Buggy Racing 2": "beachbuggyracing.com",
    "🏁 Turbo League": "turboleague.com",
    "🏁 Gear.Club": "gearclub.com",
    "🏁 Hyper Drift!": "hyperdrift.com",
    "🏁 Off The Road": "offtheroad.com",
    "🏁 Drive Ahead!": "driveaheadgame.com",
    "🏁 Mad Truck Challenge": "madtruckchallenge.com",
    "🏁 Rally Horizon": "rallyhorizon.com",
    "🏁 Mini Racing Adventures": "miniracingadventures.com",
    "🏁 Reckless Getaway 2": "recklessgetaway.com",
    "🏁 Grand Prix Story 2": "grandprixstory.com"
},
    "🎭RP GAMES": {
    "🌎 Roblox": "roblox.com",
    "🏡 The Sims 4": "ea.com/games/the-sims/the-sims-4",
    "🚔 GTA RP (FiveM)": "fivem.net",
    "🏙️ Second Life": "secondlife.com",
    "🌆 IMVU": "imvu.com",
    "🎥 MovieStarPlanet 2": "moviestarplanet.com",
    "🎀 Woozworld": "woozworld.com",
    "🎭 Avakin Life": "avakin.com",
    "🌌 VRChat": "vrchat.com",
    "🏖️ Habbo Hotel": "habbo.com",
    "🎤 SingStar": "singstargame.com",
    "🛍️ Mall World": "mallworld.com",
    "🌴 Club Cooee": "clubcooee.com",
    "🚀 Space Station 13": "spacestation13.com",
    "🌆 BitLife - Life Simulator": "bitlifeapp.com",
    "🏫 High School Story": "highschoolstory.com",
    "🎬 Hollywood Story": "hollywoodstory.com",
    "🎤 Superstar Life": "superstarlife.com",
    "👑 Kingdoms Reborn": "kingdomsreborn.com",
    "🗡️ The Elder Scrolls Online": "elderscrollsonline.com",
    "🐉 World of Warcraft RP Servers": "us.battle.net/wow",
    "👨‍⚕️ Project Hospital": "projecthospital.com",
    "🏢 Cities: Skylines": "cities-skylines.com",
    "🏰 Stardew Valley RP Mods": "stardewvalley.net",
    "🚔 Emergency 4": "emergency-4.com",
    "🎭 Life is Feudal": "lifeisfeudal.com",
    "🎨 ArtLife RP": "artlife.com",
    "🧙‍♂️ Runescape RP": "runescape.com",
    "👑 Fable Anniversary": "fableanniversary.com",
    "🐎 Red Dead Online RP": "rockstargames.com/reddeadonline",
    "🔫 Fallout 76 RP": "fallout.bethesda.net",
    "⚔️ Conan Exiles RP": "conanexiles.com",
    "👕 Fashion Famous (Roblox)": "roblox.com/games/Fashion-Famous",
    "🚓 LSPD: First Response (GTA V)": "lcpdfr.com",
    "🏠 Virtual Families": "virtualfamilies.com",
    "🌟 Rising World": "risingworld.com",
    "🦖 Ark: Survival Evolved RP": "ark-survival.com",
    "🐺 Werewolf Online": "werewolf.online",
    "🏡 House Flipper": "houseflipper.com",
    "🎤 Youtubers Life": "youtuberslife.com",
    "🏝️ Tropico 6": "tropico6.com",
    "👨‍⚕️ ER: Hospital Emergency": "hospitalgame.com",
    "🔨 Medieval Dynasty": "medievaldynasty.com",
    "🎭 Sims FreePlay": "thesimsfreeplay.com",
    "👔 The Guild 3": "theguildgame.com",
    "🏕️ My Time at Portia": "mytimeatportia.com",
    "👑 Mount & Blade II: Bannerlord RP": "bannerlord.com",
    "🐴 Star Stable": "starstable.com",
    "🎓 Academagia": "academagia.com",
    "🏛️ Grepolis": "grepolis.com",
    "🌃 CyberLife RP (Detroit: Become Human)": "cyberliferp.com",
    "💼 Business Tycoon Online": "bto.com",
    "🚁 Police Simulator: Patrol Officers": "policesimulator.com",
    "🏥 Two Point Hospital": "twopointhospital.com",
    "⚖️ Suzerain": "suzerain.com",
    "🎙️ Idol Manager": "idolmanager.com",
    "💰 Trader Life Simulator": "traderlifesimulator.com",
    "🎠 Horse Riding Tales": "horseridingtales.com",
    "🎭 Virtual Villagers": "virtualvillagers.com",
    "🏰 Fable Legends": "fablelegends.com",
    "🏙️ SimCity BuildIt": "simcitybuildit.com",
    "🔨 IndustrialCraft RP": "industrialcraft.net",
    "🏹 Medieval Engineers": "medievalengineers.com",
    "🌌 Space Engineers": "spaceengineers.com",
    "🏎️ Motor Town: Behind The Wheel RP": "motortown.com",
    "🔫 SCP: Secret Laboratory RP": "scpsecretlab.com",
    "🏢 Business Magnate": "businessmagnate.com",
    "🎢 Parkitect": "parkitect.com",
    "🌏 LifeAfter": "lifeafter.game",
    "🔎 Detective Grimoire": "detectivegrimoire.com",
    "🐉 My Dragon Tycoon (Roblox)": "roblox.com/games/My-Dragon-Tycoon",
    "🏚️ The Long Dark RP": "thelongdark.com",
    "🚑 911 Operator": "911operator.com",
    "🦸 Hero Zero": "herozerogame.com",
    "⚖️ Tropico 5": "tropico5.com",
    "🎤 Music Wars": "musicwars.com",
    "🏰 Sims Medieval": "thesimsmedieval.com",
    "🕵️ Secret Government": "secretgovernment.com",
    "🎭 MapleStory RP Servers": "maplestory.com",
    "🦖 Dino Park Tycoon": "dinoparktycoon.com",
    "🏢 Empire TV Tycoon": "empiretvtycoon.com",
    "🏛️ Democracy 4": "democracy4.com",
    "🚜 Farming Simulator 22": "farming-simulator.com",
    "🚁 Rescue HQ: The Tycoon": "rescuehq.com",
    "🎥 Hollywood Tycoon": "hollywoodtycoon.com",
    "📜 Kingdom Come: Deliverance RP": "kingdomcomerpg.com",
    "🌇 Grand Hotel Mania": "grandhotelmania.com",
    "🏆 Football Manager 2024": "footballmanager.com",
    "🌃 60 Seconds! Reatomized": "60secondsgame.com",
    "🏕️ The Survivalists RP": "thesurvivalists.com",
    "🏙️ The Tenants": "thetenants.com",
    "🏫 Academia: School Simulator": "academiasimulator.com",
    "🔬 Mad Scientist Tycoon (Roblox)": "roblox.com/games/Mad-Scientist-Tycoon",
    "🦸 Villainous (RP Board Game)": "villainousgame.com",
    "🏥 Heart's Medicine - Doctor's Oath": "heartsmedicine.com",
    "🌌 No Man’s Sky RP Servers": "nomanssky.com"
},
    "🍽️FOOD-APP": {
    "🍔 McDonald's": "mcdonalds.com",
    "🍟 Burger King": "burgerking.com",
    "🌮 Taco Bell": "tacobell.com",
    "🍕 Pizza Hut": "pizzahut.com",
    "🍕 Domino’s Pizza": "dominos.com",
    "🥪 Subway": "subway.com",
    "🍗 KFC": "kfc.com",
    "🍗 Popeyes": "popeyes.com",
    "🍔 Wendy's": "wendys.com",
    "🥩 Arby’s": "arbys.com",
    "🍔 Five Guys": "fiveguys.com",
    "🍔 In-N-Out Burger": "in-n-out.com",
    "🍔 Shake Shack": "shakeshack.com",
    "🥡 Panda Express": "pandaexpress.com",
    "🥙 Chipotle": "chipotle.com",
    "🥗 Sweetgreen": "sweetgreen.com",
    "🍜 Noodles & Company": "noodles.com",
    "🍣 Sushi Tei": "sushitei.com",
    "🍱 Yoshinoya": "yoshinoya.com",
    "🍔 Hardee’s": "hardees.com",
    "🍔 Carl’s Jr.": "carlsjr.com",
    "🍕 Little Caesars": "littlecaesars.com",
    "🍕 Papa John’s": "papajohns.com",
    "🥪 Jersey Mike’s": "jerseymikes.com",
    "🥪 Firehouse Subs": "firehousesubs.com",
    "🌭 Nathan’s Famous": "nathansfamous.com",
    "🌯 Qdoba": "qdoba.com",
    "🌯 Moe’s Southwest Grill": "moes.com",
    "🥗 Cava": "cava.com",
    "🥙 Pita Pit": "pitapit.com",
    "🍲 Panera Bread": "panerabread.com",
    "🍗 Bojangles": "bojangles.com",
    "🥩 Texas Roadhouse": "texasroadhouse.com",
    "🥩 Outback Steakhouse": "outback.com",
    "🥩 LongHorn Steakhouse": "longhornsteakhouse.com",
    "🥞 IHOP": "ihop.com",
    "🍳 Denny’s": "dennys.com",
    "🍦 Dairy Queen": "dairyqueen.com",
    "🍦 Baskin-Robbins": "baskinrobbins.com",
    "🍩 Krispy Kreme": "krispykreme.com",
    "🍩 Dunkin'": "dunkindonuts.com",
    "☕ Starbucks": "starbucks.com",
    "☕ Tim Hortons": "timhortons.com",
    "☕ Peet’s Coffee": "peets.com",
    "☕ Dutch Bros Coffee": "dutchbros.com",
    "🥤 Jamba Juice": "jamba.com",
    "🥤 Smoothie King": "smoothieking.com",
    "🍪 Mrs. Fields": "mrsfields.com",
    "🍪 Insomnia Cookies": "insomniacookies.com",
    "🍪 Crumbl Cookies": "crumblcookies.com",
    "🍫 Hershey's": "hersheyland.com",
    "🍫 Nestlé": "nestle.com",
    "🍫 Mars Chocolate": "mars.com",
    "🥤 Coca-Cola": "coca-cola.com",
    "🥤 Pepsi": "pepsi.com",
    "🍹 Red Bull": "redbull.com",
    "🥤 Monster Energy": "monsterenergy.com",
    "🥤 Gatorade": "gatorade.com",
    "🥤 Powerade": "powerade.com",
    "🥛 Nesquik": "nesquik.com",
    "🍵 Lipton Tea": "lipton.com",
    "🍵 Arizona Iced Tea": "drinkarizona.com",
    "🍹 Snapple": "snapple.com",
    "🍺 Budweiser": "budweiser.com",
    "🍺 Heineken": "heineken.com",
    "🍺 Guinness": "guinness.com",
    "🍷 Barefoot Wine": "barefootwine.com",
    "🍷 Yellow Tail Wine": "yellowtailwine.com",
    "🍿 Orville Redenbacher’s": "orville.com",
    "🍿 Pop Secret": "popsecret.com",
    "🍫 Reese’s": "reeses.com",
    "🍬 M&M’s": "mms.com",
    "🍬 Skittles": "skittles.com",
    "🍬 Haribo": "haribo.com",
    "🍬 Jelly Belly": "jellybelly.com",
    "🍪 Oreo": "oreo.com",
    "🥜 Planters Peanuts": "planters.com",
    "🥣 Kellogg’s": "kelloggs.com",
    "🥣 General Mills": "generalmills.com",
    "🍞 Wonder Bread": "wonderbread.com",
    "🍞 Sara Lee": "saraleebread.com",
    "🥖 Panera Bread": "panerabread.com",
    "🧀 Kraft Heinz": "kraftheinzcompany.com",
    "🧀 Velveeta": "velveeta.com",
    "🥓 Oscar Mayer": "oscarmayer.com",
    "🍗 Tyson Foods": "tyson.com",
    "🍗 Perdue Chicken": "perdue.com",
    "🥩 Smithfield Foods": "smithfieldfoods.com",
    "🥫 Campbell’s Soup": "campbells.com",
    "🥫 Heinz": "heinz.com",
    "🌮 El Paso": "oldelpaso.com",
    "🍣 Benihana": "benihana.com",
    "🍜 Maruchan Ramen": "maruchan.com",
    "🍜 Nissin Cup Noodles": "nissinfoods.com",
    "🍯 Nutella": "nutella.com"
},
    "🎮 Online Horror Games": {
    "🔪 Dead by Daylight": "deadbydaylight.com",
    "👻 Phasmophobia": "phasmophobia.com",
    "💀 The Outlast Trials": "redbarrelsgames.com",
    "🩸 Devour": "devourgame.com",
    "🏚 The Forest": "endnightgames.com",
    "🔦 SCP: Secret Laboratory": "scpslgame.com",
    "👀 Deceit": "playdeceit.com",
    "🧟 Left 4 Dead 2": "valvesoftware.com",
    "🕵️‍♂️ Deceit 2": "deceit2.com",
    "🚪 Forewarned": "forewarnedgame.com",
    "🔮 Propnight": "propnight.com",
    "🎭 Hide and Shriek": "funcom.com",
    "🩸 Identity V": "identityvgame.com",
    "🎞 Home Sweet Home: Survive": "homesweethomegame.com",
    "😱 White Noise 2": "whitenoise2.com",
    "🏚 Pacify": "pacifygame.com",
    "👻 Ghost Watchers": "ghostwatchers.com",
    "🔪 Friday the 13th: The Game": "f13game.com",
    "💀 Stay Out": "stayoutgame.com",
    "🚨 Poppy Playtime (Multiplayer Mods)": "poppyplaytime.com",
    "🔦 The Blackout Club": "blackoutclubgame.com",
    "👀 Hide or Die": "hideordiegame.com",
    "🧛 Midnight Ghost Hunt": "midnightghosthunt.com",
    "👹 In Silence": "insilencegame.com",
    "👻 Boo Men": "boomen.com",
    "😱 Dark and Darker": "darkanddarker.com",
    "🩸 Bloodhunt": "bloodhunt.com",
    "🕵️‍♂️ The Mortuary Assistant (Multiplayer Mod)": "mortuaryassistant.com",
    "👀 V Rising": "playvrising.com",
    "💀 GTFO": "gtfothegame.com",
    "🎭 Labyrinthine": "labyrinthinegame.com",
    "👻 Fears to Fathom (Co-op)": "fearstofathomgame.com",
    "🧟 No More Room in Hell": "nomoreroominhell.com",
    "🎞 After Hours": "afterhoursgame.com",
    "👹 Contagion": "contagion-game.com",
    "🏚 The Dark Occult (Multiplayer)": "thedarkoccult.com",
    "😈 Occult": "occultgame.com",
    "🩸 Curse of Aros": "curseofaros.com",
    "👻 Demonologist": "demonologistgame.com",
    "🔪 Resident Evil Re:Verse": "residentevil.com/reverse",
    "🦇 Nosgoth": "nosgoth.com",
    "🩸 The Evil Dead: The Game": "evildeadthegame.com",
    "🏹 Hunt: Showdown": "huntshowdown.com",
    "🔦 Project: Playtime": "projectplaytime.com",
    "🕵️‍♂️ The Anacrusis": "theanacrusis.com",
    "🎭 Dark Deception: Monsters & Mortals": "darkdeception.com",
    "🧟 Back 4 Blood": "back4blood.com",
    "💀 Hide The Corpse": "hidethecorpse.com",
    "🔪 The Texas Chain Saw Massacre": "txchainsawgame.com",
    "😱 The Hauntings": "thehauntings.com",
    "🚪 Visage (Multiplayer Mod)": "visagegame.com",
    "👹 Revenant": "revenantgame.com",
    "🦇 Nosferatu: The Wrath of Malachi": "nosferatu.com",
    "👀 Cry of Fear (Multiplayer)": "cryoffear.com",
    "🏚 Shadows of Kepler": "shadowsofkepler.com",
    "🔦 F.E.A.R. Online": "fearonline.com",
    "🧛 Dracula: Vampires vs Werewolves": "draculagame.com",
    "🔪 Don’t Starve Together (Horror Mods)": "dontstarvetogether.com",
    "🎞 Darkwood (Co-op Mods)": "darkwoodgame.com",
    "🚪 Tormented Souls (Multiplayer Mod)": "tormentedsoulsgame.com",
    "🔮 Elden Ring (Horror PvP Mods)": "eldenring.com",
    "😱 Escape the Ayuwoki": "ayuwokigame.com",
    "💀 Welcome to the Game II": "welcometothegame.com",
    "🧟 DayZ": "dayz.com",
    "🔪 Killing Floor 2": "killingfloor2.com",
    "🏚 Unfortunate Spacemen": "unfortunatespacemen.com",
    "👀 Haunt Chaser": "hauntchaser.com",
    "🎭 The Conjuring House (Multiplayer)": "theconjuringhouse.com",
    "🚨 Night of the Dead": "nightofthedeadgame.com",
    "🔦 Maid of Sker (Co-op Mode)": "maidofsker.com",
    "💀 Desolate": "desolategame.com",
    "👻 Outlast 2 (Multiplayer Mod)": "outlastgame.com",
    "🔪 Shadows of Doubt": "shadowsofdoubt.com",
    "🚪 The Sinking City (Online)": "thesinkingcity.com",
    "🧟 Infestation: The New Z": "infestationthenewz.com",
    "👹 Fear the Dark Unknown": "fearthedarkunknown.com",
    "🏚 Chernobylite (Co-op Mode)": "chernobylitegame.com",
    "🔦 Hello Neighbor Multiplayer": "helloneighborgame.com",
    "💀 Scorn (Horror Multiplayer Mod)": "scorn-game.com",
    "🕵️‍♂️ Coldside": "coldsidegame.com",
    "👀 The Beast Inside (Multiplayer)": "thebeastinsidegame.com",
    "🎭 Blight: Survival": "blightsurvival.com",
    "🔪 Evil Dead VR": "evildeadvrsurvival.com",
    "💀 The Boogeyman Returns": "boogeymanreturns.com",
    "🚨 Inside the Backrooms": "insidethebackrooms.com",
    "👻 Haunting Ground (Online Mods)": "hauntingground.com",
    "🎞 Slender: The Arrival (Multiplayer Mod)": "slenderarrival.com",
    "👹 S.T.A.L.K.E.R. Online": "stalker-online.com",
    "🔪 Resident Evil Village (Multiplayer Mod)": "residentevil.com",
    "🏚 Fear Therapy": "feartherapy.com",
    "😈 Night of Horror": "nightofhorrorgame.com",
    "🎭 Mad Experiments: Escape Room": "madexperimentsgame.com",
    "💀 The Complex Found Footage": "complexfoundfootage.com",
    "🔦 Nightmare House 2 (Online Co-op)": "moddb.com",
    "🚪 The Haunting of Crestview High": "crestviewhigh.com",
    "👀 Dead Realm": "deadrealmgame.com",
    "🏹 Dark Fracture (Multiplayer)": "darkfracture.com"
},
    "🛍 Online Shopping": {
    "🛒 Amazon": "amazon.com",
    "🏬 eBay": "ebay.com",
    "🏡 Walmart": "walmart.com",
    "🏷 AliExpress": "aliexpress.com",
    "🏭 Alibaba": "alibaba.com",
    "📦 Target": "target.com",
    "🏁 Best Buy": "bestbuy.com",
    "📱 Newegg": "newegg.com",
    "👟 Nike": "nike.com",
    "🎽 Adidas": "adidas.com",
    "👜 Zalando": "zalando.com",
    "🎀 Shein": "shein.com",
    "👗 Fashion Nova": "fashionnova.com",
    "🕶 ASOS": "asos.com",
    "💄 Sephora": "sephora.com",
    "🧴 Ulta Beauty": "ulta.com",
    "⌚ Fossil": "fossil.com",
    "🎧 Bose": "bose.com",
    "🎮 GameStop": "gamestop.com",
    "🔧 Home Depot": "homedepot.com",
    "🛏 Wayfair": "wayfair.com",
    "🖥 Apple Store": "apple.com",
    "📺 Samsung Store": "samsung.com",
    "🔋 Lenovo": "lenovo.com",
    "💻 Dell": "dell.com",
    "🖨 HP Store": "hp.com",
    "🔌 Banggood": "banggood.com",
    "🎭 Etsy": "etsy.com",
    "📀 CDJapan": "cdjapan.co.jp",
    "🧵 Joann": "joann.com",
    "👶 Babylist": "babylist.com",
    "🚗 AutoZone": "autozone.com",
    "⛺ REI": "rei.com",
    "🩳 Uniqlo": "uniqlo.com",
    "🎽 Puma": "puma.com",
    "🏀 Under Armour": "underarmour.com",
    "🥾 Timberland": "timberland.com",
    "👢 Dr. Martens": "drmartens.com",
    "🧥 The North Face": "thenorthface.com",
    "🛴 Decathlon": "decathlon.com",
    "📚 Barnes & Noble": "barnesandnoble.com",
    "📚 Book Depository": "bookdepository.com",
    "📚 ThriftBooks": "thriftbooks.com",
    "🎼 Guitar Center": "guitarcenter.com",
    "📻 Sweetwater": "sweetwater.com",
    "🎨 Michaels": "michaels.com",
    "✂️ Cricut": "cricut.com",
    "🔨 Lowe’s": "lowes.com",
    "🛋 IKEA": "ikea.com",
    "🛒 Costco": "costco.com",
    "🥩 Omaha Steaks": "omahasteaks.com",
    "🍣 Goldbelly": "goldbelly.com",
    "🥦 Instacart": "instacart.com",
    "🍕 Uber Eats": "ubereats.com",
    "🥡 DoorDash": "doordash.com",
    "🥩 ButcherBox": "butcherbox.com",
    "🧂 Thrive Market": "thrivemarket.com",
    "🍷 Drizly": "drizly.com",
    "🥤 Coca-Cola Store": "coca-colastore.com",
    "🥜 Nuts.com": "nuts.com",
    "🧁 Milk Bar Store": "milkbarstore.com",
    "🍰 Junior’s Cheesecake": "juniorscheesecake.com",
    "🎂 Carlo’s Bakery": "carlosbakery.com",
    "🏹 Bass Pro Shops": "basspro.com",
    "🎣 Cabela’s": "cabelas.com",
    "🦴 Chewy": "chewy.com",
    "🐶 Petco": "petco.com",
    "🐕 PetSmart": "petsmart.com",
    "🐦 My Bird Store": "mybirdstore.com",
    "🧴 Lush": "lush.com",
    "🛁 Bath & Body Works": "bathandbodyworks.com",
    "💍 Tiffany & Co.": "tiffany.com",
    "💎 Swarovski": "swarovski.com",
    "⏱ Rolex": "rolex.com",
    "💎 Blue Nile": "bluenile.com",
    "📿 Pandora": "pandora.net",
    "👠 Christian Louboutin": "christianlouboutin.com",
    "👗 Dior": "dior.com",
    "💄 Chanel Beauty": "chanel.com",
    "👜 Gucci": "gucci.com",
    "🕶 Ray-Ban": "ray-ban.com",
    "👓 Warby Parker": "warbyparker.com",
    "🎀 Victoria’s Secret": "victoriassecret.com",
    "💃 Savage X Fenty": "savagex.com",
    "👜 Coach": "coach.com",
    "🎩 Hugo Boss": "hugoboss.com",
    "🛍 Nordstrom": "nordstrom.com",
    "🛒 Macy’s": "macys.com",
    "👜 Bloomingdale’s": "bloomingdales.com",
    "🛍 Saks Fifth Avenue": "saksfifthavenue.com",
    "👠 Zappos": "zappos.com",
    "👞 Clarks": "clarks.com",
    "👗 Express": "express.com",
    "👖 Levi’s": "levi.com",
    "🎩 Ralph Lauren": "ralphlauren.com",
    "👟 Foot Locker": "footlocker.com",
    "👟 JD Sports": "jdsports.com",
    "👞 Aldo": "aldoshoes.com",
    "👕 H&M": "hm.com",
    "🛒 Forever 21": "forever21.com"
},
    "🌍 MMORPG Games": {
    "⚔️ World of Warcraft": "worldofwarcraft.com",
    "🛡️ Final Fantasy XIV": "na.finalfantasyxiv.com",
    "🐉 The Elder Scrolls Online": "elderscrollsonline.com",
    "🏹 Guild Wars 2": "guildwars2.com",
    "🦄 Black Desert Online": "blackdesertonline.com",
    "👹 Lost Ark": "playlostark.com",
    "💀 RuneScape": "runescape.com",
    "🧙‍♂️ Old School RuneScape": "oldschool.runescape.com",
    "🐲 Lineage 2": "lineage2.com",
    "🛡️ Aion": "aiononline.com",
    "🦊 TERA": "tera.gameforge.com",
    "🧝‍♀️ ArcheAge": "archeage.com",
    "🦄 Blade & Soul": "bladeandsoul.com",
    "🛡️ RIFT": "gamigo.com/rift",
    "🏛️ Star Wars: The Old Republic": "swtor.com",
    "👽 EVE Online": "eveonline.com",
    "🐉 Albion Online": "albiononline.com",
    "👹 Warframe": "warframe.com",
    "🧙‍♂️ Dungeons & Dragons Online": "ddo.com",
    "🦇 DC Universe Online": "dcuniverseonline.com",
    "🔥 Path of Exile": "pathofexile.com",
    "🏰 Neverwinter": "playneverwinter.com",
    "🐲 Vindictus": "vindictus.nexon.net",
    "🛡️ Cabal Online": "cabal.com",
    "⚡ MapleStory": "maplestory.nexon.net",
    "🐉 Mabinogi": "mabinogi.nexon.net",
    "⚔️ Ragnarok Online": "ragnarokonline.com",
    "🦅 Silkroad Online": "joymax.com",
    "💀 MU Online": "muonline.webzen.com",
    "👹 Fiesta Online": "fiesta.gamigo.com",
    "🔮 Aura Kingdom": "aurakingdom.aeriagames.com",
    "🦸 Champions Online": "champions-online.com",
    "🌍 Skyforge": "sf.my.games",
    "👁️ Secret World Legends": "secretworldlegends.com",
    "🏯 Swords of Legends Online": "solo.gameforge.com",
    "🐲 Dragon Nest": "dragonnest.com",
    "⚔️ Perfect World": "arcgames.com/en/games/pwi",
    "🛡️ Forsaken World": "forsakenworld.arcgames.com",
    "🔱 Rohan Online": "playrohan.com",
    "🐉 Dragona Online": "dragona.com",
    "⚔️ Atlantica Online": "atlantica.nexon.net",
    "👑 Legend of Mir": "legendofmir.com",
    "⚡ Twelve Sky 2": "12sky2.com",
    "💀 Seal Online": "sealonline.com",
    "🦄 Flyff": "flyff.webzen.com",
    "👹 Karos Online": "karos.game-entity.com",
    "⚔️ RF Online": "rfonline.webzen.com",
    "🐲 Age of Wushu": "ageofwushu.com",
    "👁️ Metin2": "metin2.gameforge.com",
    "🛡️ 9Dragons": "9dragons.gamescampus.com",
    "🐉 Runes of Magic": "runesofmagic.com",
    "🏹 Granado Espada": "ge.t3fun.com",
    "⚔️ Crossout": "crossout.net",
    "👽 WildStar": "wildstar-online.com",
    "🔮 Elyon": "elyon.playkakaogames.com",
    "🦇 Legend of Ares": "legendofares.com",
    "⚡ Crowfall": "crowfall.com",
    "👁️ Dark Age of Camelot": "darkageofcamelot.com",
    "🐉 EverQuest II": "everquest2.com",
    "⚔️ Myth of Empires": "mythofempires.com",
    "💀 Gloria Victis": "gloriavictisgame.com",
    "🏯 Wurm Online": "wurmonline.com",
    "🐲 Mortal Online 2": "mortalonline2.com",
    "👑 Ashes of Creation": "ashesofcreation.com",
    "⚡ Pantheon: Rise of the Fallen": "pantheonmmo.com",
    "💀 Project Gorgon": "projectgorgon.com",
    "🏹 Saga of Lucimia": "sagaoflucimia.com",
    "👽 The Repopulation": "therepopulation.com",
    "🦄 Tibia": "tibia.com",
    "⚔️ Warhammer Online: Return of Reckoning": "returnofreckoning.com",
    "🐉 Dragon Raja": "dragonraja.com",
    "⚡ Avabel Online": "avabelonline.com",
    "💀 Toram Online": "toram-online.com",
    "🏯 Crusaders of Light": "crusadersoflight.com",
    "🦇 Rebirth Online": "rebirth.online",
    "⚔️ Sword Art Online: Integral Factor": "saoif.com",
    "👹 V4": "v4.nexon.com",
    "🐲 Noah’s Heart": "noahsheart.com",
    "💀 MIR4": "mir4global.com",
    "🏯 Ragnarok X: Next Generation": "roxnextgen.com",
    "👁️ Summoners War: Chronicles": "summonerswar.com",
    "⚡ Gran Saga": "gransaga.com",
    "🐉 Dragon Blood": "dragonblood.com",
    "⚔️ A3: Still Alive": "a3stillalive.com",
    "💀 Arcane Legends": "spacetimestudios.com/arcanelegends",
    "🏹 Adventure Quest 3D": "aq3d.com",
    "🛡️ Order & Chaos Online": "orderandchaos.com",
    "🐲 Crystal Saga": "crystalsaga.com",
    "⚡ Seraphic Blue": "seraphicblue.com",
    "💀 World of Kings": "worldofkings.com",
    "🏯 Ys Online: The Ark of Napishtim": "ys-online.com",
    "👹 Blade Reborn": "bladereborn.com",
    "🦄 Celtic Heroes": "celticheroes.com",
    "⚔️ Light of Thel": "lightofthel.com",
    "💀 Darkness Rises": "darknessrises.com",
    "🏯 Heroes of Skyrealm": "heroesofskyrealm.com",
    "👁️ Cabal Mobile": "cabalmmobile.com",
    "⚡ Spiritwish": "spiritwish.com",
    "🐲 Kingdom Under Fire 2": "kuf2.com",
    "⚔️ EverQuest": "everquest.com",
    "💀 Shaiya": "shaiya.aeriagames.com"
},
    "⚔️ RPG Games": {
    "🐉 The Witcher 3: Wild Hunt": "thewitcher.com",
    "⚔️ Skyrim": "elderscrolls.bethesda.net",
    "🏹 Dark Souls III": "darksouls3.com",
    "🔥 Elden Ring": "eldenring.com",
    "🛡️ Bloodborne": "playstation.com/bloodborne",
    "🦄 Dragon Age: Inquisition": "dragonage.com",
    "👑 Divinity: Original Sin 2": "divinity.game",
    "🐲 Monster Hunter: World": "monsterhunter.com",
    "👹 Nioh 2": "teamninja-studio.com/nioh2",
    "💀 Diablo IV": "diablo.com",
    "🏯 Sekiro: Shadows Die Twice": "sekirothegame.com",
    "🧙‍♂️ Baldur’s Gate 3": "baldursgate3.game",
    "🌎 Fallout: New Vegas": "fallout.bethesda.net",
    "⚡ Cyberpunk 2077": "cyberpunk.net",
    "🛡️ Horizon Zero Dawn": "playstation.com/horizon",
    "🔥 Ghost of Tsushima": "playstation.com/ghostoftsushima",
    "🔮 Persona 5 Royal": "atlus.com/persona5",
    "👹 Shin Megami Tensei V": "atlus.com/smt5",
    "🐉 Yakuza: Like a Dragon": "yakuza.sega.com",
    "⚔️ Final Fantasy VII Remake": "ffvii-remake.com",
    "🦸‍♂️ Marvel’s Midnight Suns": "midnightsuns.2k.com",
    "👽 Mass Effect: Legendary Edition": "masseffect.com",
    "💎 The Outer Worlds": "outerworlds.obsidian.net",
    "🎭 Disco Elysium": "discoelysium.com",
    "🐲 Octopath Traveler II": "octopathtraveler.com",
    "💀 Kingdom Come: Deliverance": "kingdomcomerpg.com",
    "🎮 Starfield": "starfieldgame.com",
    "🦄 Tales of Arise": "talesofarise.com",
    "🛡️ GreedFall": "greedfall.com",
    "🔮 The Legend of Zelda: Breath of the Wild": "zelda.com",
    "⚔️ Fire Emblem: Three Houses": "fireemblem.nintendo.com",
    "🎎 Xenoblade Chronicles 3": "xenobladechronicles.com",
    "🏹 Dragon’s Dogma": "dragonsdogma.com",
    "👹 NieR: Automata": "nier-automata.com",
    "🛡️ Code Vein": "codevein.com",
    "⚡ Dying Light 2": "dyinglightgame.com",
    "🐲 Pathfinder: Wrath of the Righteous": "pathfinderwrath.com",
    "🧙‍♂️ Hogwarts Legacy": "hogwartslegacy.com",
    "🏹 Biomutant": "biomutant.com",
    "⚔️ Outward": "outward.game",
    "👀 Shadow of Mordor": "shadowofmordor.com",
    "🌎 Elex 2": "elexgame.com",
    "🎭 Vampire: The Masquerade – Bloodlines 2": "vampirethemasquerade.com",
    "🦸‍♂️ Gotham Knights": "gothamknightsgame.com",
    "🐉 Pillars of Eternity II: Deadfire": "pillarsofeternity.com",
    "⚔️ Wasteland 3": "wasteland.com",
    "🏰 GreedFall 2: The Dying World": "greedfall.com",
    "🔥 Steelrising": "steelrising.com",
    "🔮 Battle Chasers: Nightwar": "battlechasers.com",
    "🦄 Ruined King: A League of Legends Story": "ruinedking.com",
    "🛡️ Star Wars Jedi: Survivor": "starwars.com/jedi",
    "🎭 The Surge 2": "thesurge-game.com",
    "👽 Everspace 2": "everspace.com",
    "🐲 Granblue Fantasy: Relink": "granbluefantasy.com",
    "⚡ Warhammer 40,000: Rogue Trader": "warhammer40000.com",
    "🎎 Trials of Mana": "trialsofmana.com",
    "🛡️ Soul Hackers 2": "atlus.com/soulhackers2",
    "🐉 Blue Protocol": "blue-protocol.com",
    "⚔️ Forspoken": "forspoken.com",
    "🦄 Genshin Impact": "genshin.mihoyo.com",
    "🔥 Tower of Fantasy": "toweroffantasy.com",
    "⚡ Chrono Trigger": "square-enix.com/chronotrigger",
    "🎭 Bravely Default II": "bravelydefault.com",
    "🛡️ Honkai: Star Rail": "honkai.mihoyo.com",
    "🐲 Infinity Strash: Dragon Quest": "dragonquest.com",
    "🏹 Persona 4 Golden": "atlus.com/persona4",
    "🔮 Atelier Ryza 3": "ateliergames.com",
    "⚔️ Scarlet Nexus": "scarletnexus.com",
    "🔥 Valkyrie Elysium": "valkyrieelysium.com",
    "🧙‍♂️ Dragon Quest XI S": "dragonquest.com",
    "🐉 Nioh: The Complete Edition": "nioh.com",
    "⚡ SaGa: Emerald Beyond": "square-enix.com/saga",
    "🔮 Fate/Extella Link": "fate-extella.com",
    "🦄 CrossCode": "crosscode.com",
    "🛡️ Ys IX: Monstrum Nox": "ys-ix.com",
    "🐲 Chained Echoes": "chainedechoes.com",
    "⚔️ Bug Fables: The Everlasting Sapling": "bugfables.com",
    "🔥 Shadow Hearts": "shadowhearts.com",
    "🔮 Indivisible": "indivisiblegame.com",
    "🦄 Grandia HD Collection": "grandiahd.com",
    "🏹 Edge of Eternity": "edgeofeternity.com",
    "⚡ Oninaki": "oninaki.com",
    "🧙‍♂️ Death’s Gambit: Afterlife": "deathsgambit.com",
    "🐉 Nier Replicant ver.1.22474487139": "nier-replicant.com",
    "⚔️ Sea of Stars": "seaofstars.com",
    "🔥 Live A Live": "livealive.com",
    "🔮 Shin Megami Tensei III Nocturne HD": "atlus.com/smt3",
    "🛡️ Legends of Heroes: Trails into Reverie": "legendofheroes.com",
    "🐲 Eastward": "eastwardgame.com",
    "⚔️ Octopath Traveler": "octopathtraveler.com",
    "🔥 Triangle Strategy": "triangle-strategy.com",
    "🔮 Alundra": "alundra.com",
    "🦄 Lunar Silver Star Story": "lunarstory.com",
    "🛡️ Azure Saga: Pathfinder": "azuresaga.com",
    "🐲 The Last Remnant": "thelastremnant.com",
    "⚔️ Chrono Cross: The Radical Dreamers Edition": "square-enix.com/chronocross"
    },
    "🎯 Battle Royale Games": {
    "🔫 Call of Duty: Warzone": "callofduty.com/warzone",
    "🔥 Apex Legends": "ea.com/games/apex-legends",
    "🎭 Fortnite": "fortnite.com",
    "💀 PUBG: Battlegrounds": "pubg.com",
    "🚁 Battlefield 2042 (Hazard Zone)": "ea.com/games/battlefield",
    "👽 Super People": "geegee.net/en/superpeople",
    "🦸‍♂️ Naraka: Bladepoint": "narakathegame.com",
    "⚡ The Finals": "thefinals.com",
    "🎯 Ring of Elysium": "roe.garena.com",
    "🎃 H1Z1: King of the Kill": "h1z1.com",
    "🌪️ Hyper Scape": "hyperscape.ubisoft.com",
    "🔫 Realm Royale": "realmroyale.com",
    "💣 Spellbreak": "playspellbreak.com",
    "👹 Fear the Wolves": "fearthewolves.com",
    "🦅 Islands of Nyne": "islandsofnyne.com",
    "🚀 Planetside Arena": "planetsidearena.com",
    "🎭 Super Animal Royale": "animalroyale.com",
    "🛡️ Totally Accurate Battlegrounds": "landfall.se/tabg",
    "🔪 Bloodhunt": "bloodhunt.com",
    "🏹 CRSED: F.O.A.D.": "crsed.net",
    "🦊 Darwin Project": "darwinproject.com",
    "⚔️ My Hero Ultra Rumble": "ultrarumble.com",
    "🐉 Ashes of Creation: Apocalypse": "ashesofcreation.com",
    "💥 CrossfireX (Battle Royale Mode)": "crossfirex.com",
    "👀 Survivor Royale": "survivorroyale.com",
    "🔫 Cyber Hunter": "cyberhunter.game",
    "💣 Rules of Survival": "rulesofsurvival.com",
    "🚗 Ride Out Heroes": "rideoutheroes.com",
    "👊 Z1 Battle Royale": "z1battle-royale.com",
    "🎭 Knives Out": "knivesoutgame.com",
    "🛡️ Warface: Battle Royale Mode": "warface.com",
    "🔥 Battlelands Royale": "battlelandsroyale.com",
    "🚀 Farlight 84": "farlight84.com",
    "🔫 Shadow Arena": "shadowarena.pearlabyss.com",
    "💀 Last Man Standing": "lastmanstanding.com",
    "🎯 Mini Royale: Nations": "miniroyale.io",
    "🦸‍♀️ Hero Hunters": "herohunters.com",
    "💣 Sausage Man": "sausageman.game",
    "🕵️‍♂️ The Culling": "theculling.com",
    "🏹 Battlerite Royale": "battlerite.com",
    "💥 Project X": "projectx.game",
    "🔪 Bombergrounds: Battle Royale": "bombergrounds.com",
    "👽 Galaxy Combat Wargames": "galaxycombat.com",
    "⚡ Last Tide": "lasttide.com",
    "🎭 Mech Royale Online": "mechroyale.com",
    "🚁 Pilot Royale": "pilotroyale.com",
    "🎮 King Battle Royale": "kingbattle.com",
     },
    "🥋 Fighting Games": {
    "🔥 Tekken 8": "tekken.com",
    "💥 Street Fighter 6": "streetfighter.com",
    "⚡ Mortal Kombat 1": "mortalkombat.com",
    "🐉 Dragon Ball FighterZ": "dragonballfighterz.com",
    "🦸‍♂️ Injustice 2": "injustice.com",
    "🎭 Guilty Gear Strive": "guiltygear.com",
    "⚔️ Soulcalibur VI": "soulcalibur.com",
    "👊 The King of Fighters XV": "snk-corp.co.jp/kof",
    "🐢 Teenage Mutant Ninja Turtles: Shredder’s Revenge": "shreddersrevenge.com",
    "🕹 Brawlhalla": "brawlhalla.com",
    "?? Killer Instinct": "killerinstinct.com",
    "🤜 Super Smash Bros. Ultimate": "supersmashbros.com",
    "💪 UFC 5": "ea.com/games/ufc",
    "🔮 BlazBlue: Cross Tag Battle": "blazblue.com",
    "💢 Dead or Alive 6": "teamninja-studio.com/doa",
    "🕹 Skullgirls": "skullgirls.com",
    "⚡ Marvel vs. Capcom: Infinite": "marvelvscapcom.com",
    "🔥 Power Rangers: Battle for the Grid": "battleforthegrid.com",
    "🥷 Naruto Shippuden: Ultimate Ninja Storm 4": "narutogames.com",
    "🎭 One Piece: Burning Blood": "onepiece-game.com",
    "⚔️ Jump Force": "jumpforcegame.com",
    "🦸 My Hero One’s Justice 2": "myheroacademiagame.com",
    "🐉 JoJo’s Bizarre Adventure: All-Star Battle R": "jojos-game.com",
    "⚡ Virtua Fighter 5 Ultimate Showdown": "virtuafigther.com",
    "🩸 Mortal Kombat XL": "mortalkombatxl.com",
    "👊 Fight Night Champion": "ea.com/games/fightnight",
    "🥋 WWE 2K23": "wwe.2k.com",
    "💣 Lethal League Blaze": "lethalleague.com",
    "🎮 Rivals of Aether": "rivalsofaether.com",
    "🐍 Shaq Fu: A Legend Reborn": "shaqfu.com",
    "⚔️ Samurai Shodown": "samuraishodown.com",
    "🤖 Override 2: Super Mech League": "overridegame.com",
    "🔥 Nickelodeon All-Star Brawl 2": "nickelodeonallstarbrawl.com",
    "🦸‍♀️ Wonder Woman: Battle for Justice": "wonderwomangame.com",
    "🕵 Punch Planet": "punchplanet.com",
    "👽 Mutant Fighter": "mutantfighter.com",
    "💥 Street Fighter Alpha 3": "streetfighteralpha.com",
    "🐉 Dragon Ball Z: Budokai Tenkaichi 4": "dragonballzgame.com",
    "⚡ Divekick": "divekickgame.com",
    "🦸 DC Unchained": "dcunchained.com",
    "🔥 Melty Blood: Type Lumina": "meltyblood.com",
    "⚔️ Fighting EX Layer": "fightingexlayer.com",
    "👊 Battle Fantasia": "battlefantasia.com",
    "💢 Under Night In-Birth": "under-night.com",
    "🥋 Bushido Blade": "bushidoblade.com",
    "🐊 Primal Rage": "primalrage.com",
    "🦵 Arcana Heart 3": "arcanaheart.com",
    "🎭 Capcom vs. SNK 2": "capcomvssnk.com",
    "🕹 Fight of Gods": "fightofgods.com",
    "💣 Bloody Roar 4": "bloodyroar.com",
    "🦸 Tatsunoko vs. Capcom: Ultimate All-Stars": "tatsunokovscapcom.com",
    "🔥 Fighting Vipers": "fightingvipers.com",
    "👹 Darkstalkers Resurrection": "darkstalkers.com",
    "🛡 Power Instinct": "powerinstinct.com",
    "🎮 Chaos Code - New Sign of Catastrophe": "chaoscode.com",
    "🤜 Slam Masters": "slammasters.com",
    "💀 Yatagarasu: Attack on Cataclysm": "yatagarasu.com",
    "🔥 The Rumble Fish 2": "rumblefish.com",
    "👊 Urban Reign": "urbanreign.com",
    "🦸‍♂️ Avengers: Battle for Earth": "avengersbattle.com",
    "⚡ Rage of the Dragons": "rageofthedragons.com",
    "🐉 Dragon Ball Xenoverse 2": "dragonballxenoverse.com",
    "🤼‍♂️ Wrestling Empire": "wrestlingempire.com",
    "🎮 Double Dragon IV": "doubledragongame.com",
    "💢 Ultimate Muscle: Legends vs. New Generation": "ultimatemuscle.com",
    "🥷 Nidhogg 2": "nidhogg.com",
    "🔮 Magical Drop V": "magicaldrop.com",
    "🤼 Fire Pro Wrestling World": "fireprowrestling.com",
    "🎭 Senran Kagura: Estival Versus": "senrankagura.com",
    "🔥 Deadliest Warrior: The Game": "deadliestwarrior.com",
    "⚡ One Must Fall: 2097": "onemustfall.com",
    "🤜 Mighty Morphin Power Rangers: Mega Battle": "powerrangersmegabattle.com",
    "🥊 Real Steel World Robot Boxing": "realsteelgame.com",
    "🛡 Rage of Bahamut Duel": "rageofbahamut.com",
    "💥 Dragon Ball Super Card Game: Battle Hour": "dragonballsuper.com",
    "👊 Shrek SuperSlam": "shreksuperslam.com",
    "🥷 The Last Blade 2": "lastblade.com",
    "🦾 Cyberbots: Full Metal Madness": "cyberbots.com",
    "🤜 Hulk: Ultimate Destruction": "hulkultimatedestruction.com",
    "🔥 Granblue Fantasy Versus": "granbluefantasy.com",
    "⚡ Hyper Street Fighter II": "hyperstreetfighter.com",
    "👊 Kung Fu Chaos": "kungfuchaos.com",
    "🎭 War Gods": "wargods.com",
    "💀 Deadliest Warrior: Legends": "deadliestwarriorlegends.com",
    "🦸‍♀️ X-Men: Next Dimension": "xmennextdimension.com",
    "🤜 Beast Wrestler": "beastwrestler.com",
    "🎮 Bio F.R.E.A.K.S.": "biofreaks.com",
    "🔥 Mace: The Dark Age": "macethegame.com",
    "💢 Shaolin vs. Wutang": "shaolinwutang.com",
    "🛡 Red Earth": "redearthgame.com",
    "🎭 The Warriors: Street Brawl": "thewarriors.com",
    "💀 Slap City": "slapcity.com",
    "🔥 Fatal Fury: King of Fighters": "fatalfury.com",
    "🎮 Pocket Rumble": "pocketrumble.com"
},
    "🎮 Platformer Games": {
    "🍄 Super Mario Odyssey": "supermario.com",
    "🦔 Sonic Mania": "sonic.com",
    "🦇 Hollow Knight": "hollowknight.com",
    "🔥 Celeste": "celestegame.com",
    "🐵 Donkey Kong Country: Tropical Freeze": "donkeykong.com",
    "👻 Luigi’s Mansion 3": "luigismansion.com",
    "🐾 Crash Bandicoot 4: It’s About Time": "crashbandicoot.com",
    "🦊 Spyro Reignited Trilogy": "spyrothedragon.com",
    "🔨 Shovel Knight": "shovelknight.com",
    "🦉 Ori and the Blind Forest": "orithegame.com",
    "🌌 Ori and the Will of the Wisps": "orithegame.com",
    "🐙 Octodad: Dadliest Catch": "octodadgame.com",
    "🔫 Mega Man 11": "megaman.com",
    "🐇 Rayman Legends": "rayman.com",
    "👀 Limbo": "playdead.com/limbo",
    "🎭 Inside": "playdead.com/inside",
    "🎩 A Hat in Time": "ahatintime.com",
    "🎩 Super Lucky’s Tale": "superluckystale.com",
    "🐣 Yooka-Laylee": "yookalaylee.com",
    "🦄 Yooka-Laylee and the Impossible Lair": "yookalaylee.com",
    "🕵 Little Nightmares": "little-nightmares.com",
    "😱 Little Nightmares II": "little-nightmares.com",
    "💥 Katana Zero": "katanazero.com",
    "🧩 Fez": "fezgame.com",
    "🦊 Fox n Forests": "foxnforests.com",
    "🚀 Astro’s Playroom": "astrosplayroom.com",
    "🐦 Angry Birds Journey": "angrybirds.com",
    "🐲 Monster Boy and the Cursed Kingdom": "monsterboy.com",
    "🏴‍☠️ Captain Toad: Treasure Tracker": "captaintoad.com",
    "🐙 Guacamelee! Super Turbo Championship Edition": "guacamelee.com",
    "👽 Oddworld: New ‘n’ Tasty": "oddworld.com",
    "🎪 Cuphead": "cupheadgame.com",
    "🦎 Gex 3D: Enter the Gecko": "gexgame.com",
    "🌵 SteamWorld Dig 2": "steamworld.com",
    "🧱 Spelunky 2": "spelunkyworld.com",
    "💀 Dead Cells": "deadcells.com",
    "💣 Bomb Chicken": "bombchicken.com",
    "🐭 Ghost of a Tale": "ghostofatale.com",
    "👹 Psychonauts 2": "psychonauts.com",
    "⚡ Freedom Planet": "freedomplanet.com",
    "🕹 Kirby and the Forgotten Land": "kirby.com",
    "👑 Prince of Persia: The Lost Crown": "princeofpersia.com",
    "🏃‍♂️ Speedrunners": "tinybuild.com/speedrunners",
    "🏰 Castle of Illusion Starring Mickey Mouse": "disney.com",
    "🎭 Trine 4: The Nightmare Prince": "trine4.com",
    "👹 Blasphemous": "blasphemousgame.com",
    "🛡 Rogue Legacy 2": "roguelegacy.com",
    "⚔️ Mark of the Ninja": "markoftheninja.com",
    "🕹 Braid": "braid-game.com",
    "🐦 Flappy Bird": "flappybird.com",
    "🧠 Super Meat Boy": "supermeatboy.com",
    "🩸 Super Meat Boy Forever": "supermeatboy.com",
    "🦘 Kao the Kangaroo": "kaothekangaroo.com",
    "🐌 Slime Rancher 2": "slimerancher.com",
    "💀 Ghostrunner": "ghostrunnergame.com",
    "🔮 The Messenger": "themessengergame.com",
    "🚀 Axiom Verge": "axiomverge.com",
    "👹 Salt and Sanctuary": "saltandsanctuary.com",
    "🎢 Jet Set Radio": "jetsetradio.com",
    "🕹 Viewtiful Joe": "viewtifuljoe.com",
    "🌑 Blackthorne": "blackthornegame.com",
    "🏴‍☠️ Shantae: Half-Genie Hero": "shantae.com",
    "🌊 Ecco the Dolphin": "eccothedolphin.com",
    "🚁 Choplifter HD": "choplifter.com",
    "🌲 Kaze and the Wild Masks": "kaze.com",
    "💎 DuckTales Remastered": "ducktalesgame.com",
    "🎩 Wario Land 4": "warioland.com",
    "🐧 Tux Racer": "tuxracer.com",
    "🧙‍♂️ Alwa’s Awakening": "alwasawakening.com",
    "🕹 Freedom Fall": "freedomfallgame.com",
    "🌟 Klonoa: Door to Phantomile": "klonoa.com",
    "🦆 Dynamite Headdy": "dynamiteheaddy.com",
    "🎭 Celestial Pixels": "celestialpixels.com",
    "🦄 Equinox": "equinoxgame.com",
    "🐉 Dragon’s Trap": "dragonstrap.com",
    "⚡ Adventure Island": "adventureisland.com",
    "🦜 Donkey Kong 64": "donkeykong.com",
    "⚔️ The Lost Vikings": "thelostvikings.com",
    "🕵 Bonk’s Adventure": "bonksadventure.com",
    "🌈 Rayman Origins": "rayman.com",
    "🔫 Sunset Riders": "sunsetriders.com",
    "🎭 TwinBee: Rainbow Bell Adventures": "twinbee.com",
    "🛸 Earthworm Jim": "earthwormjim.com",
    "🎮 VVVVVV": "vvvvvvgame.com",
    "🌑 Another World": "anotherworldgame.com",
    "🔑 Hollow Knight: Silksong": "hollowknightsilksong.com",
    "🔥 1001 Spikes": "1001spikes.com",
    "🎩 Wonder Boy: The Dragon’s Trap": "wonderboy.com",
    "🚀 Super Bomberman R": "superbomberman.com",
    "🐲 Fire & Ice": "fireandicegame.com",
    "👻 Ghosts 'n Goblins Resurrection": "ghostsgoblins.com",
    "🌍 Contra: Hard Corps": "contragame.com",
    "⚡ Celestial Requiem": "celestialrequiem.com",
    "🐒 Toki: Retroland": "tokigame.com",
    "🎭 AeternoBlade II": "aeternoblade.com",
    "🛹 Ollie King": "ollieking.com"
},
    "🎵 Music Games": {
    "🎸 Guitar Hero": "guitarhero.com",
    "🥁 Rock Band": "rockband.com",
    "🎹 Piano Tiles": "pianotiles.com",
    "🔴 Beat Saber": "beatsaber.com",
    "🎶 Just Dance": "justdance.com",
    "🎼 Muse Dash": "musedash.com",
    "🎧 Audiosurf": "audiosurf.com",
    "🎤 SingStar": "singstar.com",
    "📀 Dance Dance Revolution": "ddr.com",
    "🎵 Cytus": "cytusgame.com",
    "🔊 VOEZ": "voezgame.com",
    "🎚️ Arcaea": "arcaeagame.com",
    "🕹️ Tap Tap Revenge": "taptaprevenge.com",
    "🎤 Karaoke Revolution": "karaokerevolution.com",
    "💿 DJMax Respect": "djmaxrespect.com",
    "🔷 osu!": "osu.ppy.sh",
    "🎛️ Beatmania IIDX": "beatmania.com",
    "🕹️ StepMania": "stepmania.com",
    "🔵 Incredibox": "incredibox.com",
    "🎭 Rhythm Heaven": "rhythmheaven.com",
    "🕺 Elite Beat Agents": "elitebeatagents.com",
    "🎚️ Super Hexagon": "superhexagon.com",
    "💃 Pump It Up": "pumpitup.com",
    "🕹️ Taiko no Tatsujin": "taikonotatsujin.com",
    "🎵 Deemo": "deemo.com",
    "🎶 Lanota": "lanotagame.com",
    "🎼 Thumper": "thumpergame.com",
    "🎮 Fuser": "fuser.com",
    "🎙️ Theatrhythm Final Fantasy": "theatrhythm.com",
    "🎧 Sound Voltex": "soundvoltex.com",
    "🎛️ O2Jam": "o2jam.com",
    "🎶 Groove Coaster": "groovecoaster.com",
    "🕹️ Spin Rhythm XD": "spinrhythmgame.com",
    "🔊 A Dance of Fire and Ice": "adofai.com",
    "🕺 AVICII Invector": "aviciiinvector.com",
    "🎤 Let's Sing": "letssing.com",
    "🎧 Project Diva": "projectdiva.com",
    "🎸 Guitar Flash": "guitarflash.com",
    "🎶 Dynamix": "dynamixgame.com",
    "🎼 Sound Shapes": "soundshapes.com",
    "🎹 Magic Tiles 3": "magictiles.com",
    "🥁 BEAT MP3": "beatmp3.com",
    "🎵 Dancing Line": "dancingline.com",
    "💃 Magic Dance Line": "magicdanceline.com",
    "🎼 Lost in Harmony": "lostinharmony.com",
    "🎤 SongPop": "songpop.com",
    "🎧 Clone Hero": "clonehero.net",
    "🎶 NotITG": "notitg.com",
    "🎸 Rocksmith": "rocksmith.com",
    "🎤 Ultrastar Deluxe": "ultrastardx.com",
    "🎼 Cytus II": "cytus2.com",
    "🎶 Deemo II": "deemo2.com",
    "🔵 Malody": "malody.com",
    "🎧 Vectronom": "vectronom.com",
    "🔊 Audition Online": "auditiononline.com",
    "🎼 Everhood": "everhoodgame.com",
    "🎶 Rhythmic Gymnastics": "rhythmicgym.com",
    "🎚️ Music Racer": "musicracer.com",
    "🎵 Lyrica": "lyricagame.com",
    "🎼 Melatonin": "melatonin.com",
    "🎧 Zyon": "zyongame.com",
    "🎤 Shining Nikki": "shiningnikki.com",
    "🎶 ReRave": "rerave.com",
    "🔊 Vib-Ribbon": "vib-ribbon.com",
    "🎵 Rez Infinite": "rezinfinite.com",
    "🎼 Inside My Radio": "insidemyradio.com",
    "🎸 Frets on Fire": "fretsonfire.com",
    "🎧 Musynx": "musynx.com",
    "🎚️ BEAT FEVER": "beatfever.com",
    "🕹️ Rhythm Doctor": "rhythmdoctor.com",
    "🔊 Drum Pad Machine": "drumpadmachine.com",
    "🎶 Tapsonic Top": "tapsonictop.com",
    "🎵 Symphonica": "symphonica.com",
    "🎼 Infinity Beats": "infinitybeats.com",
    "🎧 Spin the Beat": "spinthebeat.com",
    "🎶 Pianista": "pianista.com",
    "🔊 Lost Piano": "lostpiano.com",
    "🎼 Pianist Master": "pianistmaster.com",
    "🎵 Song of Bloom": "songofbloom.com",
    "🎹 Keys & Beats": "keysandbeats.com",
    "🎧 Electro Pads": "electropads.com",
    "🎼 ORG 2023": "org2023.com",
    "🔊 Tap the Beat": "tapthebeat.com",
    "🎶 RaveDJ": "ravedj.com",
    "🎧 Rock Life: Guitar Legend": "rocklife.com",
    "🎼 Rhythmetallic": "rhythmetallic.com",
    "🎵 Bouncing Notes": "bouncingnotes.com",
    "🎶 Tune Up!": "tuneup.com",
    "🔊 Boom Boom Music": "boomboommusic.com",
    "🎼 Friday Night Funkin'": "fridaynightfunkin.com",
    "🎧 DJ Hero": "djhero.com",
    "🎚️ Just Shapes & Beats": "justshapesandbeats.com",
    "🎵 Magic Piano by Smule": "smule.com",
    "🎧 Sing It!": "singitgame.com",
    "🎼 Dub Dash": "dubdash.com",
    "🔊 No Straight Roads": "nostraightroads.com",
    "🎤 Superstar BTS": "superstarbts.com",
    "🎼 Pop Star Magic": "popstarmagic.com",
    "🎶 Rytmos": "rytmos.com",
    "🎧 Melody's Escape": "melodysescape.com"
    }
} 


# -----------------------------
# Regex Patterns for Accounts 📧
# -----------------------------
EMAIL_PATTERN = re.compile(r"([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})[|:]([^\s]+)")
USERNAME_PATTERN = re.compile(r"([a-zA-Z0-9_]{6,})[|:]([^\s]+)")

# -----------------------------
# Thread Pool for Performance 🚀
# -----------------------------
executor = ThreadPoolExecutor(max_workers=5)

# -----------------------------
# Data Loading & Saving Functions 💾
# -----------------------------
def load_data():
    global keys, ALLOWED_USERS, generation_history
    try:
        with open(DATA_FILE, "rb") as f:
            data = pickle.load(f)
            keys = data.get("keys", {})
            ALLOWED_USERS = data.get("allowed_users", set())
            generation_history = data.get("generation_history", {})
    except FileNotFoundError:
        logging.warning("Data file not found. Starting with empty data. 🚧")
    except Exception as e:
        logging.error(f"Error loading data: {e}")

def save_data():
    try:
        with open(DATA_FILE, "wb") as f:
            pickle.dump({"keys": keys, "allowed_users": ALLOWED_USERS, "generation_history": generation_history}, f)
        logging.info("Data saved successfully. 💾")
    except Exception as e:
        logging.error(f"Error saving data: {e}")

def load_existing_accounts():
    saved_accounts = set()
    for file_path in SAVE_DIR.rglob("*.txt"):
        try:
            with file_path.open("r", errors="ignore") as f:
                saved_accounts.update(line.strip() for line in f)
        except Exception as e:
            logging.error(f"Error reading {file_path}: {e}")
    return saved_accounts

# -----------------------------
# Email Validation Function
# -----------------------------
def validate_emails_in_file(file_name):
    file_path = SAVE_DIR / file_name
    if not file_path.exists():
        return None, None, None
    with file_path.open("r", errors="ignore") as f:
        lines = f.readlines()
    valid_count = 0
    invalid_count = 0
    invalid_emails = []
    email_validator_pattern = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    for line in lines:
        line = line.strip()
        if not line:
            continue
        parts = line.split(":")
        if parts:
            email = parts[0].strip()
            if email_validator_pattern.match(email):
                valid_count += 1
            else:
                invalid_count += 1
                invalid_emails.append(email)
    return valid_count, invalid_count, invalid_emails

# -----------------------------
# User and Key Validation Functions 🔍
# -----------------------------
def is_user_allowed(user_id):
    return user_id == ADMIN_ID or user_id in ALLOWED_USERS

def is_key_valid(user_id):
    if user_id in paused_users:
        return False
    if user_id == ADMIN_ID:
        return True
    if user_id in ALLOWED_USERS:
        if user_id in keys:
            expiration_time = keys[user_id]
            if datetime.now() < expiration_time:
                return True
            else:
                del keys[user_id]
                ALLOWED_USERS.remove(user_id)
                if user_id in generation_history:
                    del generation_history[user_id]
                save_data()
                return False
        else:
            ALLOWED_USERS.remove(user_id)
            if user_id in generation_history:
                del generation_history[user_id]
            save_data()
            return False
    return False

# -----------------------------
# Helper: Generate Custom Key (Format: 143-626-716)
# -----------------------------
def generate_custom_key():
    part1 = random.randint(100, 999)
    part2 = random.randint(100, 999)
    part3 = random.randint(100, 999)
    return f"{part1}-{part2}-{part3}"

# -----------------------------
# Decorators 🛡️
# -----------------------------
def check_key(func):
    async def wrapper(update: Update, context: CallbackContext):
        user = update.effective_user
        if not is_user_allowed(user.id) and not is_key_valid(user.id):
            custom_message = (
                "✨ ᴡᴇʟᴄᴏᴍᴇ ᴍʏ ᴘʀᴇᴍᴜɪᴍ ᴜsᴇʀ✨\n\n"
                "🔐 ᴀᴄᴄᴇss ᴅᴇɴɪᴇᴅ sᴛᴜᴘɪᴅ, ʙᴜʏ ɴᴇᴡ ᴋᴇʏ\n"
                "ɪғ ʏᴏᴜ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ ᴠᴀʟɪᴅ ᴋᴇʏ, ᴛʜᴇɴ sᴏʀʀʏ ғᴏʀ ʏᴏᴜ.\n\n"
                "📩 ɪғ ʏᴏᴜ ᴡᴀɴᴛ ᴀᴄᴄᴇss ᴊᴜsᴛ ʙᴜʏ ᴏʀ sᴡᴀᴘ ғᴏʀ ᴋᴇʏ\n\n"
                "✨ ᴡʜʏ ᴅᴏ ʏᴏᴜ ɴᴇᴇᴅ ᴀ ᴋᴇʏ?:\n"
                "🚀 ғᴀsᴛ ᴀɴ ɴᴏ ʟɪᴍɪᴛ\n"
                "🔒 sᴀғᴇ ᴀɴᴅ ᴘʀɪᴠᴀᴛᴇ\n"
                "📆 ᴀʟᴡᴀʏs ᴜᴘᴅᴀᴛᴇᴅ sᴏ ɴᴏ ᴡᴏʀʀɪᴇs\n"
                "💡 24/7 ᴏʀ ɪᴅᴋ sᴏᴍᴇᴛɪᴍᴇs ᴄʀᴀsʜ\n\n"
                "📌ᴀʟʀᴇᴀᴅʏ ʜᴀᴠᴇ ᴀ ᴋᴇʏ? ᴛʏᴘᴇ `/redeem <YourKey>` ɪғ ʏᴏᴜ ʜᴀᴠᴇ ᴀ ᴋᴇʏ!"
            )
            if update.effective_message:
                await update.effective_message.reply_text(custom_message, parse_mode="Markdown")
            elif update.callback_query:
                await update.callback_query.answer(custom_message, show_alert=True)
            return
        return await func(update, context)
    return wrapper

def admin_only(func):
    async def wrapper(update: Update, context: CallbackContext):
        user = update.effective_user
        if user.id != ADMIN_ID:
            await update.effective_message.reply_text("❌ You don't have permission to use this command. 🚫")
            return
        return await func(update, context)
    return wrapper

# -----------------------------
# Admin Pause/Resume Functions ⏸️▶️
# -----------------------------
async def admin_pause_key(update: Update, context: CallbackContext):
    await update.effective_message.reply_text("⏸️ Please send the user ID to PAUSE the key.", parse_mode="Markdown")
    context.user_data["admin_action"] = "pause"

async def admin_resume_key(update: Update, context: CallbackContext):
    await update.effective_message.reply_text("▶️ Please send the user ID to RESUME the key.", parse_mode="Markdown")
    context.user_data["admin_action"] = "resume"

# -----------------------------
# Help Menu Command
# -----------------------------
@check_key
async def menu_help(update: Update, context: CallbackContext):
    help_text = (
        "🤖 **ʙᴏᴛ ʜᴇʟᴘ ᴍᴇɴᴜ ғᴏʀ sᴛᴜᴘɪᴅ ᴘᴇᴏᴘʟᴇ!**\n\n"
        "• **🔍 Generate Txt:** ᴊᴜsᴛ ɢᴇɴᴇʀᴀᴛᴇ ɴᴇᴡ ᴛxᴛ.\n"
        "• **✍️ Custom Keyword:** ᴄᴜsᴛᴏᴍ ᴋᴇʏ ᴡᴏʀᴅ ɪғ ʏᴏᴜ ᴅᴏɴ'ᴛ ᴡᴀɴᴛ ᴀɴʏ .\n"
        "• **🔑 Check Key Time:** ʏᴏᴜ ᴄᴀɴ ᴠɪᴇᴡ ʜᴏᴡ ᴍᴜᴄʜ ᴠᴀʟɪᴅ ᴛɪᴍᴇ ʏᴏᴜ ʜᴀᴠᴇ ʟᴇғᴛ .\n"
        "• **🔄 Start Again:** ᴊᴜsᴛ sᴛᴀʀᴛ ᴀɴᴅ ɢᴇɴᴇʀᴀᴛᴇ ɴᴇᴡ.\n"
        "• **💰 Price Of Key:** ᴄʜᴇᴄᴋ ᴘʀɪᴄᴇ ᴄᴀɴ ᴅᴏ ᴘʀᴏᴍᴏ sᴏᴍᴇᴛɪᴍᴇs.\n\n"
        "Additional commands:\n"
        "• **/keywordsleft <keyword>**: Returns the number of available lines for the given keyword (e.g., `/keywordsleft garena.com`).\n\n"
        "For further assistance, please contact @Xairuu1 ."
    )
    await update.effective_message.reply_text(help_text, parse_mode="Markdown")

# -----------------------------
# Updated /keywordsleft Command
# -----------------------------
@check_key
async def keywords_left(update: Update, context: CallbackContext):
    message = update.effective_message
    if len(context.args) != 1:
        await message.reply_text("Usage: /keywordsleft <keyword>", parse_mode="Markdown")
        return
    search_keyword = context.args[0].lower()
    total = 0
    for file_path in LOGS_DIR.rglob("*.txt"):
        try:
            with file_path.open("r", errors="ignore") as f:
                for line in f:
                    if search_keyword in line.lower():
                        total += 1
        except Exception as e:
            logging.error(f"Error reading {file_path}: {e}")
    deducted = 0
    for file_path in SAVE_DIR.rglob("*.txt"):
        try:
            with file_path.open("r", errors="ignore") as f:
                for line in f:
                    if search_keyword in line.lower():
                        deducted += 1
        except Exception as e:
            logging.error(f"Error reading {file_path}: {e}")
    available = total - deducted
    await message.reply_text(f"Keyword `{search_keyword}` appears in {available} available lines.", parse_mode="Markdown")

# -----------------------------
# New: Report Appeal Feature
# -----------------------------
async def report_appeal_prompt(update: Update, context: CallbackContext):
    query = update.callback_query
    context.user_data["state"] = "awaiting_report"
    await query.message.reply_text("🚨 Please describe the issue you encountered with the bot:", parse_mode="Markdown")

# -----------------------------
# New: Admin Send Message Feature
# -----------------------------
@admin_only
async def admin_send_message_prompt(update: Update, context: CallbackContext):
    await update.effective_message.reply_text("📨 Please provide the target user's ID or username:", parse_mode="Markdown")
    context.user_data["state"] = "awaiting_send_message_target"

# -----------------------------
# New: Admin Announcement Feature
# -----------------------------
@admin_only
async def admin_announcement_prompt(update: Update, context: CallbackContext):
    await update.effective_message.reply_text("📢 Please provide the announcement message to broadcast to all users:", parse_mode="Markdown")
    context.user_data["state"] = "awaiting_announcement"

# -----------------------------
# New: Email Validator Prompt
# -----------------------------
@check_key
async def email_validator_prompt(update: Update, context: CallbackContext):
    await update.effective_message.reply_text("📧 Please send the filename (e.g. Results.txt) from the Generated Results folder to validate email accounts:", parse_mode="Markdown")
    context.user_data["state"] = "awaiting_email_validator_filename"

# -----------------------------
# Main Menu and Other Bot Commands 🎉
# -----------------------------
@check_key
async def start(update: Update, context: CallbackContext):
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    import uuid
    
    user = update.effective_user
    current_commands[user.id] = uuid.uuid4()
    message = update.effective_message

    keyboard = [
        [InlineKeyboardButton("🎯FILES", callback_data="choose_keyword"),
         InlineKeyboardButton("🏆CUSTOM-F", callback_data="custom_keyword"),
         InlineKeyboardButton("E-VALID", callback_data="email_validator")],

        [InlineKeyboardButton("🚧CHECK-KEY", callback_data="check_key_time"),
         InlineKeyboardButton("KEY-P", callback_data="price_of_key"),
         InlineKeyboardButton("REPORT", callback_data="report_appeal")],

        [InlineKeyboardButton("⚡RESTART", callback_data="start_again"),
         InlineKeyboardButton("💢WHAT-CAN-DO", callback_data="what_bot_can_do"),
         InlineKeyboardButton("DEV", callback_data="developer")],

        [InlineKeyboardButton("🔊ᴊᴏɪɴ-ʜᴇʀᴇ", callback_data="join_here"),
         InlineKeyboardButton("🚀HELP", callback_data="menu_help"),
         InlineKeyboardButton("🩸BACK", callback_data="exit")]
    ]

    if user.id == ADMIN_ID:
        keyboard.insert(0, [InlineKeyboardButton("🛠️ ᴀᴅᴍɪɴ ᴘᴀɴᴇʟ", callback_data="admin_panel")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await message.reply_text("🔑 **ᴡᴇʟᴄᴏᴍᴇ ᴛᴏ xaii premium bot!**\nᴄʜᴏᴏsᴇ ᴀɴ ᴏᴘᴛɪᴏɴ: 🚀", reply_markup=reply_markup, parse_mode="Markdown")

@check_key
async def check_key_time(update: Update, context: CallbackContext):
    message = update.effective_message
    user = update.effective_user
    if user.id in keys:
        expiration_time = keys[user.id]
        time_remaining = expiration_time - datetime.now()
        days = time_remaining.days
        hours, remainder = divmod(time_remaining.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        await message.reply_text(f"ʏᴏᴜʀ ᴋᴇʏ ɪs sᴛɪʟʟ ᴠᴀʟɪᴅ!!\n════════════════════════\n📅 ᴇxᴘɪʀᴀᴛɪᴏɴ ᴛɪᴍᴇ:\n⏳ {days} DAYS | {hours} HOURS | {minutes} MINUTES | {seconds} SECONDS\n════════════════════════", parse_mode="Markdown")
    else:
        await message.reply_text("❌ **No active key found for your user ID.**", parse_mode="Markdown")

# -----------------------------
# /genkey Command (Admin Only) with Custom Key Format 🔑
# -----------------------------
@admin_only
async def genkey(update: Update, context: CallbackContext):
    message = update.effective_message
    if len(context.args) < 1:
        await message.reply_text("❌ Usage: /genkey <duration> (e.g., /genkey 1hours) ⏰")
        return
    duration_str = " ".join(context.args)
    try:
        duration = parse_duration(duration_str)
    except ValueError as e:
        await message.reply_text(f"❌ Invalid duration: {e} 🚫")
        return
    expiration_time = datetime.now() + duration
    custom_key = generate_custom_key()
    keys[custom_key] = expiration_time
    save_data()
    expiration_str = expiration_time.strftime("%Y-%m-%d %H:%M:%S")
    await message.reply_text(f"sᴜᴄᴄᴇssғᴜʟʟʏ ɢᴇɴᴇʀᴀᴛᴇᴅ ᴋᴇʏ!: `{custom_key}`\nExpires at: `{expiration_str}` 🔐", parse_mode="Markdown")

# -----------------------------
# Extend and Deduct Key Commands (Admin Only) ⏳
# -----------------------------
@admin_only
async def extendkey(update: Update, context: CallbackContext):
    message = update.effective_message
    if len(context.args) != 2:
        await message.reply_text("❌ Usage: /extendkey <user_id> <duration> ⏰")
        return
    try:
        user_id_to_extend = int(context.args[0])
        duration_str = context.args[1]
        duration = parse_duration(duration_str)
    except ValueError:
        await message.reply_text("❌ Invalid user ID or duration format. 🚫")
        return
    if user_id_to_extend in keys:
        expiration_time = keys[user_id_to_extend]
        keys[user_id_to_extend] = expiration_time + duration
        new_expiration_time = expiration_time + duration
        new_expiration_str = new_expiration_time.strftime("%Y-%m-%d %H:%M:%S")
        await message.reply_text(f"✅ Key for User {user_id_to_extend} extended.\nNew expiration: `{new_expiration_str}` ⏳", parse_mode="Markdown")
    else:
        await message.reply_text(f"❌ No active key found for User {user_id_to_extend}.", parse_mode="Markdown")
    save_data()

@admin_only
async def deductkey(update: Update, context: CallbackContext):
    message = update.effective_message
    if len(context.args) != 2:
        await message.reply_text("❌ Usage: /deductkey <user_id> <duration> ⏰", parse_mode="Markdown")
        return
    try:
        user_id_to_deduct = int(context.args[0])
        duration_str = context.args[1]
        duration = parse_duration(duration_str)
    except ValueError:
        await message.reply_text("❌ Invalid user ID or duration format. 🚫", parse_mode="Markdown")
        return
    if user_id_to_deduct in keys:
        expiration_time = keys[user_id_to_deduct]
        keys[user_id_to_deduct] = expiration_time - duration
        new_expiration_time = expiration_time - duration
        new_expiration_str = new_expiration_time.strftime("%Y-%m-%d %H:%M:%S")
        await message.reply_text(f"✅ Key for User {user_id_to_deduct} reduced.\nNew expiration: `{new_expiration_str}` ⏳", parse_mode="Markdown")
    else:
        await message.reply_text(f"❌ No active key found for User {user_id_to_deduct}.", parse_mode="Markdown")
    save_data()

# -----------------------------
# /history Command (Admin Only) 📊
# -----------------------------
@admin_only
async def history(update: Update, context: CallbackContext):
    message = update.effective_message
    if len(context.args) != 1:
        await message.reply_text("❌ Usage: /history <user_id> 🔍", parse_mode="Markdown")
        return
    try:
        target_user = int(context.args[0])
    except ValueError:
        await message.reply_text("❌ Invalid user_id. Please enter a number. 🚫", parse_mode="Markdown")
        return
    if target_user in generation_history:
        data = generation_history[target_user]
        username = data.get("username", "N/A").replace("_", "\\_")
        generated_count = data.get("generated_count", 0)
        total_lines = data.get("total_lines", 0)
        msg = f"📊 **Generation History for User {target_user} (@{username}):**\n• Generated Count: `{generated_count}`\n• Total Lines Generated: `{total_lines}`"
        await message.reply_text(msg, parse_mode="Markdown")
    else:
        await message.reply_text("❌ No history found for that user. 📭", parse_mode="Markdown")

# -----------------------------
# Admin Panel Menu (Admin Only) with Additional Buttons ⏸️▶️
# -----------------------------
@admin_only
async def admin_panel(update: Update, context: CallbackContext):
    query = update.callback_query
    keyboard = [
        [InlineKeyboardButton("👥 List Users", callback_data="list_users"),
         InlineKeyboardButton("📊 Generation History", callback_data="generation_history")],
        [InlineKeyboardButton("⏱️ Deduct Key Time", callback_data="deduct_key_time"),
         InlineKeyboardButton("➕ Extend Key Time", callback_data="extend_key_time")],
        [InlineKeyboardButton("❌ Revoke User", callback_data="revoke_user")],
        [InlineKeyboardButton("⏸️ Pause Key", callback_data="pause_key"),
         InlineKeyboardButton("▶️ Resume Key", callback_data="resume_key")],
        [InlineKeyboardButton("📨 Send Message", callback_data="send_message")],
        [InlineKeyboardButton("📢 Announcement", callback_data="announcement")],
        [InlineKeyboardButton("🔙 Back", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("🛠️ **Admin Panel**\nChoose an admin command:", reply_markup=reply_markup, parse_mode="Markdown")

# -----------------------------
# Keyword Selection and Account Generation 💎
# -----------------------------
@check_key
async def choose_keyword(update: Update, context: CallbackContext):
    user = update.effective_user
    current_commands[user.id] = uuid.uuid4()
    query = update.callback_query
    keyboard = []
    row = []
    for category in KEYWORDS_CATEGORIES.keys():
        button = InlineKeyboardButton(category, callback_data=f"cat_{category}")
        row.append(button)
        if len(row) == 3:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton("✍️ Custom Keyword", callback_data="custom_keyword")])
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="main_menu")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("📌 **ᴘɪᴄᴋ ᴏɴᴇ:**", reply_markup=reply_markup, parse_mode="Markdown")

async def show_keywords_for_category(update: Update, context: CallbackContext, category):
    user = update.effective_user
    current_commands[user.id] = uuid.uuid4()
    query = update.callback_query
    keywords = KEYWORDS_CATEGORIES.get(category, {})
    keyboard = []
    row = []
    for name, keyword in keywords.items():
        button = InlineKeyboardButton(name, callback_data=f"kw_{keyword}")
        row.append(button)
        if len(row) == 3:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="main_menu")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(f"📌 **sᴇʟᴇᴄᴛ ᴀ ᴋᴇʏᴡᴏʀᴅ ғʀᴏᴍ {category}:**", reply_markup=reply_markup, parse_mode="Markdown")

@check_key
async def handle_keyword_selection(update: Update, context: CallbackContext):
    user = update.effective_user
    current_commands[user.id] = uuid.uuid4()
    query = update.callback_query
    data = query.data
    if data == "custom_keyword_confirm":
        keyword = context.user_data.get("custom_keyword")
    else:
        keyword = data.split("_", 1)[1]
    context.user_data["keyword"] = keyword
    context.user_data["state"] = "awaiting_number"
    await query.answer()
    await query.edit_message_text("✅ ɢᴏᴏᴅ ᴛᴏ ɢᴏ\n──────────────\nʜᴏᴡ ᴍᴀɴʏ ʟɪɴᴇs ʏᴏᴜ ᴡᴀɴᴛ? (ᴇx.100) ᴛɪᴘ: ᴛʜᴇ ʟᴏɴɢᴇʀ ᴛʜᴇ ʟɪɴᴇs ᴛʜᴇ sʟᴏᴡᴇʀ ᴛʜᴇ ɢᴇɴᴇʀᴀᴛᴇ sᴏ ᴛʜɪɴᴋ ᴡɪsᴇʟʏ\n", parse_mode="Markdown")

@check_key
async def handle_user_input(update: Update, context: CallbackContext):
    user = update.effective_user
    current_commands[user.id] = uuid.uuid4()
    message = update.effective_message
    state = context.user_data.get("state")
    if user.id == ADMIN_ID and context.user_data.get("admin_action") in ["pause", "resume"]:
        try:
            target_user = int(message.text)
            if context.user_data["admin_action"] == "pause":
                paused_users.add(target_user)
                await message.reply_text(f"⏸️ User {target_user}'s key has been paused.", parse_mode="Markdown")
            elif context.user_data["admin_action"] == "resume":
                if target_user in paused_users:
                    paused_users.remove(target_user)
                    await message.reply_text(f"▶️ User {target_user}'s key has been resumed.", parse_mode="Markdown")
                else:
                    await message.reply_text("User is not paused.", parse_mode="Markdown")
            context.user_data["admin_action"] = None
            return
        except ValueError:
            await message.reply_text("❌ Please send a valid user ID number.", parse_mode="Markdown")
            return

    if state == "awaiting_send_message_target":
        target = message.text.strip()
        context.user_data["target"] = target
        context.user_data["state"] = "awaiting_send_message_content"
        await message.reply_text("📨 Please type the message you want to send to the user:", parse_mode="Markdown")
        return
    elif state == "awaiting_send_message_content":
        message_to_send = message.text.strip()
        target = context.user_data.get("target")
        try:
            if target.startswith("@"):
                target = target
            else:
                try:
                    target = int(target)
                except ValueError:
                    target = target
            chat = await context.bot.get_chat(target)
            await context.bot.send_message(chat_id=chat.id, text=message_to_send)
            await message.reply_text(f"✅ Message successfully sent to {chat.username or chat.id}.", parse_mode="Markdown")
        except Exception as e:
            await message.reply_text(f"❌ Failed to send message: {e}", parse_mode="Markdown")
        context.user_data["state"] = None
        return

    if state == "awaiting_announcement":
        announcement_text = message.text.strip()
        count = 0
        for user_id in ALLOWED_USERS:
            try:
                await context.bot.send_message(chat_id=user_id, text=f"📢 Announcement:\n\n{announcement_text}")
                count += 1
            except Exception as e:
                logging.error(f"Error sending announcement to {user_id}: {e}")
        await message.reply_text(f"✅ Announcement sent to {count} users.", parse_mode="Markdown")
        context.user_data["state"] = None
        return

    if state == "awaiting_email_validator_filename":
        file_name = message.text.strip()
        valid_count, invalid_count, invalid_emails = validate_emails_in_file(file_name)
        if valid_count is None:
            await message.reply_text("❌ File not found. Please check the filename and try again.", parse_mode="Markdown")
        else:
            reply = f"✅ Email Validation Complete!\nValid Emails: {valid_count}\nInvalid Emails: {invalid_count}"
            if invalid_emails and len(invalid_emails) <= 10:
                reply += "\nInvalid: " + ", ".join(invalid_emails)
            await message.reply_text(reply, parse_mode="Markdown")
        context.user_data["state"] = None
        return

    if state == "awaiting_number":
        try:
            num_accounts = int(message.text)
            if num_accounts <= 0:
                raise ValueError
            context.user_data["num_accounts"] = num_accounts
            context.user_data["state"] = "awaiting_filename"
            await message.reply_text("✅ᴀʟʀɪɢʜᴛ ɢᴏᴏᴅ ᴛᴏ ɢᴏ!\n────────────────────────\nᴍᴀᴋᴇ ʏᴏᴜʀ ᴏᴡɴ ғɪʟᴇɴᴀᴍᴇ ɴᴏᴡ.\n💾 (`ᴇx. ᴘʀᴇᴍᴜɪᴍ.ᴛxᴛ`)\n───────────────────────", parse_mode="Markdown")
        except ValueError:
            await message.reply_text("❌ Invalid number. Please send a valid number. 🚫", parse_mode="Markdown")
    elif state == "awaiting_filename":
        filename = message.text.strip()
        context.user_data["filename"] = filename
        context.user_data["state"] = None
        await generate_accounts(update, context)
    elif state == "awaiting_custom_keyword":
        custom_keyword = message.text.strip()
        context.user_data["custom_keyword"] = custom_keyword
        keyboard = [[InlineKeyboardButton("✅ Confirm", callback_data="custom_keyword_confirm")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await message.reply_text(f"You entered: `{custom_keyword}`\nConfirm?", reply_markup=reply_markup, parse_mode="Markdown")
        context.user_data["state"] = None
    else:
        await generate_accounts(update, context)

@check_key
async def generate_accounts(update: Update, context: CallbackContext):
    user = update.effective_user
    command_id = uuid.uuid4()
    current_commands[user.id] = command_id
    message = update.effective_message
    keyword = context.user_data.get("keyword")
    num_accounts = context.user_data.get("num_accounts")
    filename = context.user_data.get("filename")
    file_path = SAVE_DIR / filename
    await message.reply_text("🔍🚀 sᴇᴀʀᴄʜɪɴɢ ғᴏʀ ʏᴏᴜ...\n ᴊᴜsᴛ ᴡᴀɪᴛ ᴀ sᴇᴄᴏɴᴅ.. ʏᴏᴜ ɢᴇɴᴇʀᴀᴛᴇᴅ ᴍᴏʀᴇ ᴛʜᴀɴ 100 ᴍᴀʏʙᴇ", parse_mode="Markdown")
    
    saved_accounts = load_existing_accounts()
    loop = asyncio.get_running_loop()
    extracted_results = await loop.run_in_executor(
        executor, extract_accounts_fast, keyword, num_accounts, saved_accounts, command_id, user.id
    )
    if extracted_results is None:
        await message.reply_text("⚠️ Previous command was canceled. New command will take over.", parse_mode="Markdown")
        return

    try:
        SAVE_DIR.mkdir(parents=True, exist_ok=True)
        content_to_write = "\n".join(extracted_results)
        file_path.write_text(content_to_write)
        # Wait for 1 seconds before sending the results
        await asyncio.sleep(1)
        current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        total_lines = len(extracted_results)
        summary_message = f"""
✅ SEARCH COMPLETE! ✅  
════════════════════════  
🪪NAME: `{filename}`  
🗓️DATE & TIME: `{current_datetime}`  
🔎TOTAL LINES: `{total_lines}` Out of 2069279 
════════════════════════  
🥳ɴɪᴄᴇ, ʏᴏᴜ ᴜsᴇᴅ ɪᴛ ʀɪɢʜᴛ ᴜɴʟɪᴋᴇ ᴛʜᴇ ᴏᴛʜᴇʀs... 
🖥️ᴍᴀᴅᴇ ʙʏ @Xairuu1, ᴄᴏɴᴛᴀᴄᴛ ʜɪᴍ ɪғ ʏᴏᴜ ᴡᴀɴᴛ ᴀ ᴋᴇʏ
        """
        try:
            with open(file_path, "rb") as document:
                await message.reply_document(document=document, filename=filename)
            await message.reply_text(summary_message, parse_mode="Markdown")
            keyboard = [[InlineKeyboardButton("🔙 Choose Again Keyword", callback_data="choose_keyword")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await message.reply_text("Select a new keyword:", reply_markup=reply_markup)
        except FileNotFoundError:
            await message.reply_text("❌ Error: The generated file could not be found.", parse_mode="Markdown")
            logging.error(f"File not found: {file_path}")
        except Exception as e:
            await message.reply_text(f"❌ Error sending document: {e}", parse_mode="Markdown")
            logging.exception("Error sending document:")
        username = user.username if user.username else "N/A"
        update_generation_history(user.id, username, total_lines)
    except Exception as e:
        await message.reply_text(f"❌ Error writing to file: {e}", parse_mode="Markdown")
        logging.exception("Error writing to file:")

def extract_accounts_fast(keyword, num_lines, saved_accounts, command_id, user_id):
    file_paths = list(SAVE_DIR.rglob("*.txt")) + list(LOGS_DIR.rglob("*.txt"))
    file_paths = sorted(file_paths, key=lambda p: p.stat().st_mtime, reverse=True)
    results = set()

    def process_file(file_path):
        if current_commands.get(user_id) != command_id:
            return None
        local_results = set()
        try:
            with file_path.open("r", errors="ignore") as f:
                for line in f:
                    if current_commands.get(user_id) != command_id:
                        return None
                    if keyword.lower() in line.lower():
                        match = EMAIL_PATTERN.search(line) or USERNAME_PATTERN.search(line)
                        if match:
                            account = f"{match.group(1)}:{match.group(2)}"
                            if account not in saved_accounts and account not in local_results:
                                local_results.add(account)
                                if len(local_results) >= num_lines:
                                    break
            return list(local_results)
        except Exception as e:
            logging.error(f"Error reading {file_path}: {e}")
            return []

    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = {pool.submit(process_file, fp): fp for fp in file_paths}
        for future in as_completed(futures):
            if current_commands.get(user_id) != command_id:
                return None
            local_result = future.result()
            if local_result:
                results.update(local_result)
            if len(results) >= num_lines:
                break
    return list(results)[:num_lines]

def parse_duration(duration_str):
    pattern = re.compile(r"(?:(\d+)\s*days?)?\s*(?:(\d+)\s*hours?)?\s*(?:(\d+)\s*minutes?)?\s*(?:(\d+)\s*seconds?)?", re.IGNORECASE)
    match = pattern.fullmatch(duration_str.strip())
    if not match:
        raise ValueError("Invalid duration format. Use formats like '1days', '1hours', '1minutes', etc.")
    days = int(match.group(1)) if match.group(1) else 0
    hours = int(match.group(2)) if match.group(2) else 0
    minutes = int(match.group(3)) if match.group(3) else 0
    seconds = int(match.group(4)) if match.group(4) else 0
    if all(v == 0 for v in [days, hours, minutes, seconds]):
        raise ValueError("Duration must have at least one nonzero value.")
    return timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)

def redeem_key(key, user_id):
    if key in keys:
        expiration_time = keys[key]
        if datetime.now() < expiration_time:
            keys[user_id] = expiration_time
            ALLOWED_USERS.add(user_id)
            used_keys.add(key)
            del keys[key]
            save_data()
            return "success"
        else:
            used_keys.add(key)
            del keys[key]
            save_data()
            return "wrong_key"
    else:
        if key in used_keys:
            return "already_redeemed"
        else:
            return "wrong_key"

async def redeem(update: Update, context: CallbackContext):
    message = update.effective_message
    user = update.effective_user
    key = context.args[0] if context.args else None
    if not key:
        await message.reply_text("ᴅᴏɴᴛ ʙᴇ sᴛᴜᴘɪᴅ, ᴘʟᴇᴀsᴇ ʀᴇᴀᴅ ғɪʀsᴛ!.", parse_mode="Markdown")
        return
    result = redeem_key(key, user.id)
    if result == "success":
        expiry_date = keys[user.id].strftime('%Y-%m-%d %H:%M:%S')
        username = user.username if user.username else "N/A"
        username = username.replace("_", "\\_")
        await message.reply_text(
            f"ᴄᴏɴɢʀᴀᴛᴜʟᴀᴛɪᴏɴs, ʏᴏᴜ ᴍᴀᴅᴇ ɪᴛ ᴛᴏ ᴠɪᴘ!✅\n───────────────────────\n👤 USERNAME: @{username}\n⏳ ᴀᴄᴄᴇss ᴇxᴘɪʀᴇs: {expiry_date}\n───────────────────────\nᴜsᴇ ɴᴇ ɴᴏᴡ ɪғ ʏᴏᴜ ᴡᴀɴᴛ ᴀ ᴛxᴛ! 🚀 ᴛʏᴘᴇ `/start` ᴛᴏ ɢᴇɴᴇʀᴀᴛᴇ, ᴜsᴇ ᴍᴇ ᴡɪsᴇʟʏ.",
            parse_mode="Markdown"
        )
        await context.bot.send_message(chat_id=ADMIN_ID, text=f"🎉 ɴᴇᴡ ᴜsᴇʀ ʜᴀᴠᴇ ᴇɴᴛᴇʀᴇᴅ {username} (ID: {user.id})")
    elif result == "already_redeemed":
        await message.reply_text(
            "⚠️ sᴛᴜᴘɪᴅ! ʏᴏᴜ ᴀʟʀᴇᴀᴅʏ ᴜsᴇᴅ ᴛʜᴀᴛ\n"
            "🔑 ᴊᴏɪɴ ᴍʏ ᴄʜᴀɴɴᴇʟ sᴏᴍᴇᴛɪᴍᴇs ɪ ɢɪᴠᴇᴀᴡᴀʏ ᴋᴇʏs.\n"
            "💡 ᴘʟᴇᴀsᴇ ᴇɴsᴜʀᴇ ʏᴏᴜ ʜᴀᴠᴇ ᴀ ᴠᴀʟɪᴅ ᴋᴇʏ ᴛᴏ ʀᴇᴅᴇᴇᴍ.\n"
            "📲 ʙᴜʏ ᴏʀ sᴡᴀᴘ ɴᴇᴡ ᴋᴇʏ ᴅᴍ @Xairuu1 .",
            parse_mode="Markdown"
        )
    elif result == "wrong_key":
        await message.reply_text(
            "🚫 ᴛʜᴀᴛ's ᴡʀᴏɴɢ sᴛᴜᴘɪᴅ\n"
            "❗ ᴅᴏɴ'ᴛ ᴛʀʏ ᴛᴏ ᴄʜᴇᴀᴛ ᴛʜᴇ sʏsᴛᴇᴍ.\n"
            "🔍 ᴍᴀᴋᴇ sᴜʀᴇ ʏᴏᴜ ʀᴇᴅᴇᴇᴍ ᴀ ᴠᴀʟɪᴅ ᴋᴇʏ!.\n"
            "📲 ʙᴜʏ ᴋᴇʏ ᴏʀ sᴡᴀᴘ @Xairuu1.",
            parse_mode="Markdown"
        )
    save_data()

@admin_only
async def revoke(update: Update, context: CallbackContext):
    message = update.effective_message
    if context.args:
        user_id_to_revoke = int(context.args[0])
        ALLOWED_USERS.discard(user_id_to_revoke)
        if user_id_to_revoke in keys:
            del keys[user_id_to_revoke]
        await message.reply_text(f"✅ User {user_id_to_revoke} revoked.", parse_mode="Markdown")
        save_data()
    else:
        await message.reply_text("❌ ᴘʟᴇᴀsᴇ sᴘᴇᴄɪғʏ ᴀɴ ɪᴅ ᴛᴏ ʀᴇᴠᴏᴋᴇ ᴀ ᴜsᴇʀ. 🚫", parse_mode="Markdown")

@admin_only
async def list_users(update: Update, context: CallbackContext):
    message = update.effective_message
    all_users = ALLOWED_USERS.union({ADMIN_ID})
    active_users = set()
    for user_id in all_users:
        if user_id == ADMIN_ID or is_key_valid(user_id):
            active_users.add(user_id)
    user_list = "📋 **ᴀᴄᴛɪᴠᴇ ᴜsᴇʀs (Active Keys Only):**\n════════════════════════\n"
    for user_id in active_users:
        try:
            user = await context.bot.get_chat(user_id)
            username = user.username if user.username else "N/A"
            full_name = f"{user.first_name} {user.last_name}" if user.last_name else user.first_name
            username = username.replace("_", "\\_")
            full_name = full_name.replace("_", "\\_")
        except Exception as e:
            username = "N/A"
            full_name = "N/A"
            logging.error(f"Error getting chat for user {user_id}: {e}")
        expiration_str = keys[user_id].strftime("%Y-%m-%d %H:%M:%S") if user_id in keys else "N/A"
        user_list += (
            f"👤 User ID: `{user_id}`\n"
            f"🔗 Username: @{username}\n"
            f"📝 Name: {full_name}\n"
            f"⏳ Key Expiration: `{expiration_str}`\n"
            "─────────────────────────\n"
        )
    if not user_list.strip():
        user_list = "❌ **No Active Users Found.**"
    await update.callback_query.message.reply_text(user_list, parse_mode="Markdown")

@admin_only
async def generation_history_command(update: Update, context: CallbackContext):
    query = update.callback_query
    report = "📊 **ɢᴇɴᴇʀᴀᴛɪᴏɴ ʜɪsᴛᴏʀʏ ʀᴇᴘᴏʀᴛ:**\n══════════════════════\n"
    if not generation_history:
        report += "❌ **No generation history found.**"
    else:
        for user_id, data in generation_history.items():
            username = data.get("username", "N/A").replace("_", "\\_")
            generated_count = data.get("generated_count", 0)
            total_lines = data.get("total_lines", 0)
            report += f"👤 User ID: `{user_id}`\n🔗 Username: @{username}\n📈 Generated Count: `{generated_count}`\n📝 Total Lines Generated: `{total_lines}`\n─────────────────────────────\n"
    await query.message.reply_text(report, parse_mode="Markdown")

@admin_only
async def deduct_key_time(update: Update, context: CallbackContext):
    await update.callback_query.message.reply_text("Please send the user ID and the duration to deduct in the format: `/deductkey <user_id> <duration>`", parse_mode="Markdown")

@admin_only
async def extend_key_time(update: Update, context: CallbackContext):
    await update.callback_query.message.reply_text("Please send the user ID and the duration to extend in the format: `/extendkey <user_id> <duration>`", parse_mode="Markdown")

def update_generation_history(user_id, username, total_lines):
    if user_id in generation_history:
        generation_history[user_id]["generated_count"] += 1
        generation_history[user_id]["total_lines"] += total_lines
    else:
        generation_history[user_id] = {"username": username, "generated_count": 1, "total_lines": total_lines}
    save_data()

@admin_only
async def price_of_key(update: Update, context: CallbackContext):
    query = update.callback_query
    price_message = (
        "🔥ᴘʀɪᴄᴇ ʟɪsᴛ ᴏғ ᴋᴇʏs 🔥\n"
        "────────────\n"
        "✅ 200 - LifeTime\n"
        "✅ 𝟷80 - 2 𝚆𝙴𝙴𝙺𝚂\n"
        "✅ 120 - 𝟷 𝚆𝙴𝙴𝙺𝚂\n"
        "✅ 80 - 2 𝙳𝙰𝚈𝚂\n"
        "✅ 50 - 𝟷 𝙳𝙰𝚈𝚂\n"
        "✅ 25  - 1 𝙷𝙾𝚄𝚁𝚂\n"
        "────────────\n"
        "☎️ 𝙲𝙾𝙽𝚃𝙰𝙲𝚃 - @Xairuu1\n"
        "𝚃𝙾 𝙰𝚅𝙰𝙸𝙻 𝙺𝙴𝚈 🗝️"
    )
    await query.edit_message_text(price_message, parse_mode="Markdown")

async def button(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    user = query.from_user
    if not is_user_allowed(user.id):
        await query.answer("🚫 ᴀᴄᴄᴇss ᴅᴇɴɪᴇᴅ!\n❌ ʏᴏᴜʀ ᴋᴇʏ ɪs ᴇxᴘɪʀᴇᴅ ᴏʀ ᴘᴀᴜsᴇᴅ.\n🔑 ᴘʟᴇᴀsᴇ ᴄᴏɴᴛᴀᴄᴛ @Xairuu1 ɪᴍᴍᴇᴅɪᴀᴛᴇʟʏ.", show_alert=True)
        return
    if not is_key_valid(user.id):
        await query.answer("⛔ ɪɴᴠᴀʟɪᴅ ᴋᴇʏ!\n❌ ʏᴏᴜʀ ᴋᴇʏ ɪs ɴᴏ ʟᴏɴɢᴇʀ ᴠᴀʟɪᴅ ᴏʀ ᴘᴀᴜsᴇᴅ.\n🔑 ᴘʟᴇᴀsᴇ ᴄᴏɴᴛᴀᴄᴛ @Xairuu1 ғᴏʀ ᴀ ɴᴇᴡ ᴋᴇʏ.", show_alert=True)
        return

    if query.data == "choose_keyword":
        await choose_keyword(update, context)
    elif query.data.startswith("cat_"):
        category = query.data.split("_", 1)[1]
        await show_keywords_for_category(update, context, category)
    elif query.data == "custom_keyword":
        context.user_data["state"] = "awaiting_custom_keyword"
        await query.message.reply_text("✍️ ᴡʀɪᴛᴇ ᴀ ᴄᴏsᴛᴜᴍᴇ ᴡᴏʀᴅ: 💬", parse_mode="Markdown")
    elif query.data == "custom_keyword_confirm":
        await handle_keyword_selection(update, context)
    elif query.data.startswith("kw_"):
        await handle_keyword_selection(update, context)
    elif query.data == "start_again":
        await start(update, context)
    elif query.data == "check_key_time":
        await check_key_time(update, context)
    elif query.data == "exit":
        await query.message.edit_text("👋 ᴜsᴇ ᴍᴇ sᴏᴍᴇᴛɪᴍᴇs ʙᴀʙʏ ʙʏᴇᴇ 👋", parse_mode="Markdown")
    elif query.data == "main_menu":
        await start(update, context)
    elif query.data == "list_users":
        await list_users(update, context)
    elif query.data == "generation_history":
        await generation_history_command(update, context)
    elif query.data == "deduct_key_time":
        await deduct_key_time(update, context)
    elif query.data == "extend_key_time":
        await extend_key_time(update, context)
    elif query.data == "menu_help":
        await menu_help(update, context)
    elif query.data == "admin_panel":
        await admin_panel(update, context)
    elif query.data == "pause_key":
        await admin_pause_key(update, context)
    elif query.data == "resume_key":
        await admin_resume_key(update, context)
    elif query.data == "join_here":
        keyboard = [
            [InlineKeyboardButton("📣 Telegram Channel", url="https://t.me/Xaiilaro")],
            [InlineKeyboardButton("💬 Telegram Discussion", url="https://t.me/xaiiidc")],
            [InlineKeyboardButton("💬 My Store", url="https://t.me/Store_Tempest")],
            [InlineKeyboardButton("🔙 Back", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.edit_text("Join our community: 🤝", reply_markup=reply_markup)
    elif query.data == "developer":
        await query.message.edit_text("👨‍💻 **Developer Info**\n\nᴍᴀᴅᴇ ʙʏ @Xairuu1 💻 \n\nᴡᴀɴɴᴀ ᴍᴀᴋᴇ ʏᴏᴜʀ ᴏᴡɴ ʙᴏᴛ? ᴅᴍ @Xairuu1", parse_mode="Markdown")
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="main_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text("Return to main menu:", reply_markup=reply_markup)
    elif query.data == "what_bot_can_do":
        message_text = (
            "🤖 **What This Bot Can Do:**\n\n"
            "• Generate premium accounts based on selected keywords. 💎\n"
            "• Allow custom keyword searches. 🔍\n"
            "• Manage key validity and access control. 🔐\n"
            "• Show generation history (admin only). 📊\n"
            "• Provide various Telegram community links. 🔗\n"
            "• And more features as updated by the developer. 🚀"
        )
        await query.message.edit_text(message_text, parse_mode="Markdown")
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="main_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text("Return to main menu:", reply_markup=reply_markup)
    elif query.data == "price_of_key":
        await price_of_key(update, context)
    elif query.data == "revoke_user":
        await query.edit_message_text("Please use the command `/revoke <user_id>` to revoke a user. 🚫", parse_mode="Markdown")
    elif query.data == "report_appeal":
        await report_appeal_prompt(update, context)
    elif query.data == "send_message":
        await admin_send_message_prompt(update, context)
    elif query.data == "announcement":
        await admin_announcement_prompt(update, context)
    elif query.data == "email_validator":
        await email_validator_prompt(update, context)
    else:
        await query.answer("Unrecognized command. 🚫")

async def error_handler(update: Update, context: CallbackContext):
    logging.error(msg="Exception while handling an update:", exc_info=context.error)
    await context.bot.send_message(ADMIN_ID, text=f"Exception:\n{context.error}")

def main():
    load_data()
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("genkey", genkey))
    app.add_handler(CommandHandler("redeem", redeem))
    app.add_handler(CommandHandler("revoke", revoke))
    app.add_handler(CommandHandler("extendkey", extendkey))
    app.add_handler(CommandHandler("deductkey", deductkey))
    app.add_handler(CommandHandler("history", history))
    app.add_handler(CommandHandler("keywordsleft", keywords_left))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_user_input))
    app.add_handler(CallbackQueryHandler(button))
    app.add_error_handler(error_handler)

    app.run_polling()

if __name__ == "__main__":
    main()