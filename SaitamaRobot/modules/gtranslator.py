from emoji import UNICODE_EMOJI
from google_trans_new import LANGUAGES, google_translator
from telegram import ParseMode, Update
from telegram.ext import CallbackContext, run_async

from SaitamaRobot import dispatcher
from SaitamaRobot.modules.disable import DisableAbleCommandHandler


@run_async
def totranslate(update: Update, context: CallbackContext):
    message = update.effective_message
    problem_lang_code = []
    for key in LANGUAGES:
        if "-" in key:
            problem_lang_code.append(key)

    try:
        if message.reply_to_message:
            args = update.effective_message.text.split(None, 1)
            if message.reply_to_message.text:
                text = message.reply_to_message.text
            elif message.reply_to_message.caption:
                text = message.reply_to_message.caption

            try:
                source_lang = args[1].split(None, 1)[0]
            except (IndexError, AttributeError):
                source_lang = "id"

        else:
            args = update.effective_message.text.split(None, 2)
            text = args[2]
            source_lang = args[1]

        if source_lang.count('-') == 2:
            for lang in problem_lang_code:
                if lang in source_lang:
                    if source_lang.startswith(lang):
                        dest_lang = source_lang.rsplit("-", 1)[1]
                        source_lang = source_lang.rsplit("-", 1)[0]
                    else:
                        dest_lang = source_lang.split("-", 1)[1]
                        source_lang = source_lang.split("-", 1)[0]
        elif source_lang.count('-') == 1:
            for lang in problem_lang_code:
                if lang in source_lang:
                    dest_lang = source_lang
                    source_lang = None
                    break
            if dest_lang is None:
                dest_lang = source_lang.split("-")[1]
                source_lang = source_lang.split("-")[0]
        else:
            dest_lang = source_lang
            source_lang = None

        exclude_list = UNICODE_EMOJI.keys()
        for emoji in exclude_list:
            if emoji in text:
                text = text.replace(emoji, '')

        trl = google_translator()
        if source_lang is None:
            detection = trl.detect(text)
            trans_str = trl.translate(text, lang_tgt=dest_lang)
            return message.reply_text(
                f"Terjemahan dari bahasa `{detection[0]}` ke bahasa `{dest_lang}`:\n`{trans_str}`",
                parse_mode=ParseMode.MARKDOWN)
        else:
            trans_str = trl.translate(
                text, lang_tgt=dest_lang, lang_src=source_lang)
            message.reply_text(
                f"Diterjemahkan dari bahasa `{source_lang}` ke bahasa `{dest_lang}`:\n`{trans_str}`",
                parse_mode=ParseMode.MARKDOWN)

    except IndexError:
        update.effective_message.reply_text(
            "Balas pesan atau tulis pesan dari bahasa lain ​​untuk menerjemahkan ke bahasa yang diinginkan\n\n"
            "Contoh: `/tr en-id` untuk menerjemahkan dari bahasa Inggris ke Bahasa Indonesia\n"
            "Atau gunakan: `/tr id` untuk otomatis menerjemahkan ke bahasa Indonesia.\n"
            "Lihat [disini](t.me/canzu/20) untuk melihat semua daftar bahasa yang tersedia.",
            parse_mode="markdown",
            disable_web_page_preview=True)
    except ValueError:
        update.effective_message.reply_text(
            "Bahasa yang dimaksud tidak ditemukan!")
    else:
        return


__help__ = """
• `/tr` atau `/tl` (kode bahasa) dengan membalas pesan yang ingin diterjemahkan
*Contoh:* 
  `/tr id`*:* terjemahkan pesan ke bahasa Indonesia
  `/tr en-id`*:* menerjemahkan dari bahasa Inggris ke bahasa Indonesia
"""

TRANSLATE_HANDLER = DisableAbleCommandHandler(["tr", "tl"], totranslate)

dispatcher.add_handler(TRANSLATE_HANDLER)

__mod_name__ = "Kamus"
__command_list__ = ["tr", "tl"]
__handlers__ = [TRANSLATE_HANDLER]
