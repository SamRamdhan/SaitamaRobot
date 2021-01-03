import html
import re
import os
import requests
import subprocess

from telethon.tl.functions.channels import GetFullChannelRequest
from telethon.tl.types import ChannelParticipantsAdmins
from telethon import events

from telegram import MAX_MESSAGE_LENGTH, ParseMode, Update
from telegram.ext import CallbackContext, CommandHandler
from telegram.ext.dispatcher import run_async
from telegram.error import BadRequest
from telegram.utils.helpers import escape_markdown, mention_html

from SaitamaRobot import (DEV_USERS, OWNER_ID, DRAGONS, DEMONS, TIGERS, WOLVES,
                          INFOPIC, dispatcher, sw)
from SaitamaRobot.__main__ import STATS, TOKEN, USER_INFO
import SaitamaRobot.modules.sql.userinfo_sql as sql
from SaitamaRobot.modules.disable import DisableAbleCommandHandler
from SaitamaRobot.modules.sql.global_bans_sql import is_user_gbanned
from SaitamaRobot.modules.sql.afk_sql import is_afk, check_afk_status
from SaitamaRobot.modules.sql.users_sql import get_user_num_chats
from SaitamaRobot.modules.helper_funcs.chat_status import sudo_plus
from SaitamaRobot.modules.helper_funcs.extraction import extract_user
from SaitamaRobot import telethn as SaitamaTelethonClient, TIGERS, DRAGONS, DEMONS


def no_by_per(totalhp, percentage):
    """
    rtype: num of `percentage` from total
    eg: 1000, 10 -> 10% of 1000 (100)
    """
    return totalhp * percentage / 100


def get_percentage(totalhp, earnedhp):
    """
    rtype: percentage of `totalhp` num
    eg: (1000, 100) will return 10%
    """

    matched_less = totalhp - earnedhp
    per_of_totalhp = 100 - matched_less * 100.0 / totalhp
    per_of_totalhp = str(int(per_of_totalhp))
    return per_of_totalhp


def hpmanager(user):
    total_hp = (get_user_num_chats(user.id) + 10) * 10

    if not is_user_gbanned(user.id):

        # Assign new var `new_hp` since we need `total_hp` in
        # end to calculate percentage.
        new_hp = total_hp

        # if no username decrease 25% of hp.
        if not user.username:
            new_hp -= no_by_per(total_hp, 25)
        try:
            dispatcher.bot.get_user_profile_photos(user.id).photos[0][-1]
        except IndexError:
            # no profile photo ==> -25% of hp
            new_hp -= no_by_per(total_hp, 25)
        # if no /setme exist ==> -20% of hp
        if not sql.get_user_me_info(user.id):
            new_hp -= no_by_per(total_hp, 20)
        # if no bio exsit ==> -10% of hp
        if not sql.get_user_bio(user.id):
            new_hp -= no_by_per(total_hp, 10)

        if is_afk(user.id):
            afkst = check_afk_status(user.id)
            # if user is afk and no reason then decrease 7%
            # else if reason exist decrease 5%
            if not afkst.reason:
                new_hp -= no_by_per(total_hp, 7)
            else:
                new_hp -= no_by_per(total_hp, 5)

        # fbanned users will have (2*number of fbans) less from max HP
        # Example: if HP is 100 but user has 5 diff fbans
        # Available HP is (2*5) = 10% less than Max HP
        # So.. 10% of 100HP = 90HP


# Commenting out fban health decrease cause it wasnt working and isnt needed ig.
#_, fbanlist = get_user_fbanlist(user.id)
#new_hp -= no_by_per(total_hp, 2 * len(fbanlist))

# Bad status effects:
# gbanned users will always have 5% HP from max HP
# Example: If HP is 100 but gbanned
# Available HP is 5% of 100 = 5HP

    else:
        new_hp = no_by_per(total_hp, 5)

    return {
        "earnedhp": int(new_hp),
        "totalhp": int(total_hp),
        "percentage": get_percentage(total_hp, new_hp)
    }


def make_bar(per):
    done = min(round(per / 10), 10)
    return "■" * done + "□" * (10 - done)


@run_async
def get_id(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    message = update.effective_message
    chat = update.effective_chat
    msg = update.effective_message
    user_id = extract_user(msg, args)

    if user_id:

        if msg.reply_to_message and msg.reply_to_message.forward_from:

            user1 = message.reply_to_message.from_user
            user2 = message.reply_to_message.forward_from

            msg.reply_text(
                f"<b>ID Telegram:</b>,"
                f"• {html.escape(user2.first_name)} - <code>{user2.id}</code>.\n"
                f"• {html.escape(user1.first_name)} - <code>{user1.id}</code>.",
                parse_mode=ParseMode.HTML)

        else:

            user = bot.get_chat(user_id)
            msg.reply_text(
                f"id {html.escape(user.first_name)} adalah <code>{user.id}</code>.",
                parse_mode=ParseMode.HTML)

    else:

        if chat.type == "private":
            msg.reply_text(
                f"ID anda adalah <code>{chat.id}</code>.",
                parse_mode=ParseMode.HTML)

        else:
            msg.reply_text(
                f"ID grup ini adalah <code>{chat.id}</code>.",
                parse_mode=ParseMode.HTML)


@SaitamaTelethonClient.on(
    events.NewMessage(
        pattern='/ginfo ',
        from_users=(TIGERS or []) + (DRAGONS or []) + (DEMONS or [])))
async def group_info(event) -> None:
    chat = event.text.split(' ', 1)[1]
    try:
        entity = await event.client.get_entity(chat)
        totallist = await event.client.get_participants(
            entity, filter=ChannelParticipantsAdmins)
        ch_full = await event.client(GetFullChannelRequest(channel=entity))
    except:
        await event.reply(
            "Tidak bisa karena alasan tertentu, mungkin disana pribadi atau saya tidak diizinkan disana."
        )
        return
    msg = f"**ID**: `{entity.id}`"
    msg += f"\n**Title**: `{entity.title}`"
    msg += f"\n**Datacenter**: `{entity.photo.dc_id}`"
    msg += f"\n**Video PFP**: `{entity.photo.has_video}`"
    msg += f"\n**Supergroup**: `{entity.megagroup}`"
    msg += f"\n**Restricted**: `{entity.restricted}`"
    msg += f"\n**Scam**: `{entity.scam}`"
    msg += f"\n**Slowmode**: `{entity.slowmode_enabled}`"
    if entity.username:
        msg += f"\n**Username**: {entity.username}"
    msg += "\n\n**Member Stats:**"
    msg += f"\n`Admins:` `{len(totallist)}`"
    msg += f"\n`Users`: `{totallist.total}`"
    msg += "\n\n**Admins List:**"
    for x in totallist:
        msg += f"\n• [{x.id}](tg://user?id={x.id})"
    msg += f"\n\n**Description**:\n`{ch_full.full_chat.about}`"
    await event.reply(msg)


@run_async
def gifid(update: Update, context: CallbackContext):
    msg = update.effective_message
    if msg.reply_to_message and msg.reply_to_message.animation:
        update.effective_message.reply_text(
            f"ID gif-nya adalah:\n<code>{msg.reply_to_message.animation.file_id}</code>",
            parse_mode=ParseMode.HTML)
    else:
        update.effective_message.reply_text(
            "Harap balas gif untuk menampilkan ID-nya.")


@run_async
def info(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    message = update.effective_message
    chat = update.effective_chat
    user_id = extract_user(update.effective_message, args)

    if user_id:
        user = bot.get_chat(user_id)

    elif not message.reply_to_message and not args:
        user = message.from_user

    elif not message.reply_to_message and (
            not args or
        (len(args) >= 1 and not args[0].startswith("@") and
         not args[0].isdigit() and
         not message.parse_entities([MessageEntity.TEXT_MENTION]))):
        message.reply_text("Saya tidak dapat ekstrak pengguna dari ini.")
        return

    else:
        return

    rep = message.reply_text(
        "<code>Menilai...</code>", parse_mode=ParseMode.HTML)

    text = (f"╒═══「<b> Hasil penilaian:</b> 」\n"
            f"ID: <code>{user.id}</code>\n"
            f"Nama Depan: {html.escape(user.first_name)}")

    if user.last_name:
        text += f"\nNama Belakang: {html.escape(user.last_name)}"

    if user.username:
        text += f"\nUsername: @{html.escape(user.username)}"

    text += f"\nLink Akun: {mention_html(user.id, 'link')}"

    if chat.type != "private" and user_id != bot.id:
        _stext = "\nKedudukan: <code>{}</code>"

        afk_st = is_afk(user.id)
        if afk_st:
            text += _stext.format("AFK")
        else:
            status = status = bot.get_chat_member(chat.id, user.id).status
            if status:
                if status in {"left", "kicked"}:
                    text += _stext.format("Mantan Anggota Grup")
                elif status == "member":
                    text += _stext.format("Warga Setempat")
                elif status in {"administrator", "creator"}:
                    text += _stext.format("Staff Grup")
    if user_id not in [bot.id, 777000, 1087968824]:
        userhp = hpmanager(user)
        text += f"\n\n<b>Siapa dia?</b> <code>{userhp['earnedhp']}/{userhp['totalhp']}</code>\n[<i>{make_bar(int(userhp['percentage']))} </i>{userhp['percentage']}%]"

    try:
        spamwtc = sw.get_ban(int(user.id))
        if spamwtc:
            text += "\n\n<b>Pengguna ini spammer!</b>"
            text += f"\nAlasan: <pre>{spamwtc.reason}</pre>"
            text += "\nLakukan banding di @SpamWatchSupport"
        else:
            pass
    except:
        pass  # don't crash if api is down somehow...

    disaster_level_present = False

    if user.id == OWNER_ID:
        text += "\n\nJabatan pengguna ini adalah <b>Ketua RT</b>."
        disaster_level_present = True
    elif user.id in DEV_USERS:
        text += "\n\nJulukan pengguna ini adalah <b>Dewa</b>."
        disaster_level_present = True
    elif user.id in DRAGONS:
        text += "\n\nPengguna ini adalah <b>Preman Kampung</b>."
        disaster_level_present = True
    elif user.id in DEMONS:
        text += "\n\nJulukan pengguna ini adalah <b>Orang Spesial</b>."
        disaster_level_present = True
    elif user.id in TIGERS:
        text += "\n\nJulukan pengguna ini adalah <b>Warga Lama</b>."
        disaster_level_present = True
    elif user.id in WOLVES:
        text += "\n\nJulukan pengguna ini adalah <b>Warga Teladan</b>."
        disaster_level_present = True

    if disaster_level_present:
        text += ' [<a href="https://t.me/canzu/30">???</a>]'.format(
            bot.username)

    try:
        user_member = chat.get_member(user.id)
        if user_member.status == 'administrator':
            result = requests.post(
                f"https://api.telegram.org/bot{TOKEN}/getChatMember?chat_id={chat.id}&user_id={user.id}"
            )
            result = result.json()["result"]
            if "custom_title" in result.keys():
                custom_title = result['custom_title']
                text += f"\n\nTitle:\n<b>{custom_title}</b>"
    except BadRequest:
        pass

    for mod in USER_INFO:
        try:
            mod_info = mod.__user_info__(user.id).strip()
        except TypeError:
            mod_info = mod.__user_info__(user.id, chat.id).strip()
        if mod_info:
            text += "\n\n" + mod_info

    if INFOPIC:
        try:
            profile = context.bot.get_user_profile_photos(user.id).photos[0][-1]
            _file = bot.get_file(profile["file_id"])
            _file.download(f"{user.id}.png")

            message.reply_document(
                document=open(f"{user.id}.png", "rb"),
                caption=(text),
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True)

            os.remove(f"{user.id}.png")
        # Incase user don't have profile pic, send normal text
        except IndexError:
            message.reply_text(
                text, parse_mode=ParseMode.HTML, disable_web_page_preview=True)

    else:
        message.reply_text(
            text, parse_mode=ParseMode.HTML, disable_web_page_preview=True)

    rep.delete()


@run_async
def about_me(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    message = update.effective_message
    user_id = extract_user(message, args)

    if user_id:
        user = bot.get_chat(user_id)
    else:
        user = message.from_user

    info = sql.get_user_me_info(user.id)

    if info:
        update.effective_message.reply_text(
            f"*{user.first_name}*:\n{escape_markdown(info)}",
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True)
    elif message.reply_to_message:
        username = message.reply_to_message.from_user.first_name
        update.effective_message.reply_text(
            f"{username} belum mengatur informasi tentang dirinya!")
    else:
        update.effective_message.reply_text(
            "Tidak ada informasi, gunakan /setme untuk menambahkan informasi.")


@run_async
def set_about_me(update: Update, context: CallbackContext):
    message = update.effective_message
    user_id = message.from_user.id
    if user_id in [777000, 1087968824]:
        message.reply_text("Error! Unauthorized")
        return
    bot = context.bot
    if message.reply_to_message:
        repl_message = message.reply_to_message
        repl_user_id = repl_message.from_user.id
        if repl_user_id in [bot.id, 777000, 1087968824] and (user_id
                                                             in DEV_USERS):
            user_id = repl_user_id
    text = message.text
    info = text.split(None, 1)
    if len(info) == 2:
        if len(info[1]) < MAX_MESSAGE_LENGTH // 4:
            sql.set_user_me_info(user_id, info[1])
            if user_id in [777000, 1087968824]:
                message.reply_text("Authorized...Information updated!")
            elif user_id == bot.id:
                message.reply_text(
                    "I have updated my info with the one you provided!")
            else:
                message.reply_text("Information updated!")
        else:
            message.reply_text(
                "The info needs to be under {} characters! You have {}.".format(
                    MAX_MESSAGE_LENGTH // 4, len(info[1])))


@run_async
@sudo_plus
def stats(update: Update, context: CallbackContext):
    process = subprocess.Popen(
        "neofetch --stdout", shell=True, text=True, stdout=subprocess.PIPE)
    output = process.communicate()[0]
    stats = "<b>Current stats:</b>\n" + "\n" + output + "\n".join(
        [mod.__stats__() for mod in STATS])
    result = re.sub(r'(\d+)', r'<code>\1</code>', stats)
    update.effective_message.reply_text(result, parse_mode=ParseMode.HTML)


@run_async
def about_bio(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    message = update.effective_message

    user_id = extract_user(message, args)
    if user_id:
        user = bot.get_chat(user_id)
    else:
        user = message.from_user

    info = sql.get_user_bio(user.id)

    if info:
        update.effective_message.reply_text(
            "*{}*:\n{}".format(user.first_name, escape_markdown(info)),
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True)
    elif message.reply_to_message:
        username = user.first_name
        update.effective_message.reply_text(
            f"{username} belum mengatur biografinya!\nGunakan /setbio untuk menambahkan biografi"
        )
    else:
        update.effective_message.reply_text(
            "Anda belum mengatur biografi anda!")


@run_async
def set_about_bio(update: Update, context: CallbackContext):
    message = update.effective_message
    sender_id = update.effective_user.id
    bot = context.bot

    if message.reply_to_message:
        repl_message = message.reply_to_message
        user_id = repl_message.from_user.id

        if user_id == message.from_user.id:
            message.reply_text(
                "Hah, anda tidak bisa menambahkan biografi anda sendiri! Suruh orang lain disini melakukan itu..."
            )
            return

        if user_id in [777000, 1087968824] and sender_id not in DEV_USERS:
            message.reply_text("You are not authorised")
            return

        if user_id == bot.id and sender_id not in DEV_USERS:
            message.reply_text(
                "Hah... yeah, hanya Dewa yang bisa mengatur bio Saya!")
            return

        text = message.text
        bio = text.split(
            None, 1
        )  # use python's maxsplit to only remove the cmd, hence keeping newlines.

        if len(bio) == 2:
            if len(bio[1]) < MAX_MESSAGE_LENGTH // 4:
                sql.set_user_bio(user_id, bio[1])
                message.reply_text("Updated {}'s bio!".format(
                    repl_message.from_user.first_name))
            else:
                message.reply_text(
                    "Bio needs to be under {} characters! You tried to set {}."
                    .format(MAX_MESSAGE_LENGTH // 4, len(bio[1])))
    else:
        message.reply_text("Reply to someone to set their bio!")


def __user_info__(user_id):
    bio = html.escape(sql.get_user_bio(user_id) or "")
    me = html.escape(sql.get_user_me_info(user_id) or "")
    result = ""
    if me:
        result += f"<b>Tentang Pengguna:</b>\n{me}\n"
    if bio:
        result += f"<b>Apa yang orang katakan:</b>\n{bio}\n"
    result = result.strip("\n")
    return result


__help__ = """
*ID:*
 • /id*:* menampilkan id pengguna atau id grup
 • /gifid*:* balas gif untuk menampilkan id

*Informasi yang ditambahkan sendiri:* 
 • /setme <teks>*:* mengatur informasi tentang anda
 • /me*:* menampilkan informasi anda atau orang lain
Contoh:
 `/setme Aku adalah anak gembala.`
 `/me @username(akan menampilkan info pengguna)`

*Informasi yang ditambahkan orang lain kepada anda:* 
 • /bio*:* menampilkan biografi anda atau orang lain (ini tidak dapat ditambahkan sendiri)
 • /setbio <teks>*:* akan menambahkan bio orang lain (ketika membalas pesan orang lain)
Contoh:
 /bio @username(akan mengarah ke biografi anda jika tidak mengarah ke pengguna yang spesifik).
 `/setbio Pengguna ini adalah mantan pacar saya` (balas pesan pengguna tersebut)

*Semua informasi tentang anda:*
 • /info*:* menampilkan informasi pengguna. 
 
*Apa itu jabatan dan julukan?*
 Silahkan anda [Lihat disini](https://t.me/canzu/30)
"""

SET_BIO_HANDLER = DisableAbleCommandHandler("setbio", set_about_bio)
GET_BIO_HANDLER = DisableAbleCommandHandler("bio", about_bio)

STATS_HANDLER = CommandHandler("stats", stats)
ID_HANDLER = DisableAbleCommandHandler("id", get_id)
GIFID_HANDLER = DisableAbleCommandHandler("gifid", gifid)
INFO_HANDLER = DisableAbleCommandHandler(("info", "book"), info)

SET_ABOUT_HANDLER = DisableAbleCommandHandler("setme", set_about_me)
GET_ABOUT_HANDLER = DisableAbleCommandHandler("me", about_me)

dispatcher.add_handler(STATS_HANDLER)
dispatcher.add_handler(ID_HANDLER)
dispatcher.add_handler(GIFID_HANDLER)
dispatcher.add_handler(INFO_HANDLER)
dispatcher.add_handler(SET_BIO_HANDLER)
dispatcher.add_handler(GET_BIO_HANDLER)
dispatcher.add_handler(SET_ABOUT_HANDLER)
dispatcher.add_handler(GET_ABOUT_HANDLER)

__mod_name__ = "Info"
__command_list__ = ["setbio", "bio", "setme", "me", "info"]
__handlers__ = [
    ID_HANDLER, GIFID_HANDLER, INFO_HANDLER, SET_BIO_HANDLER, GET_BIO_HANDLER,
    SET_ABOUT_HANDLER, GET_ABOUT_HANDLER, STATS_HANDLER
]
