import asyncio
import json
import os
import openpyxl
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, F, Router
from aiogram.enums import ParseMode
from aiogram.types import Message, CallbackQuery, Contact, FSInputFile
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import Command
from aiogram.types import InputFile
from dotenv import load_dotenv
import pandas as pd

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNELS = os.getenv("CHANNELS").split(',')
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
DATABASE = "database.json"
KONKURS_END_TIME = datetime(2025, 7, 9, 22, 0, 0)  # 9-iyul 22:00
# 🕐 Konkurs tugash vaqti
KONKURS_END = datetime(2025, 7, 9, 22, 0, 0)

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()
router = Router()

def load_users():
    try:
        with open(DATABASE, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_users(data):
    with open(DATABASE, 'w') as f:
        json.dump(data, f)

async def is_subscribed(user_id):
    for ch in CHANNELS:
        try:
            member = await bot.get_chat_member(chat_id=ch, user_id=user_id)
            if member.status not in ('member', 'administrator', 'creator'):
                return False
        except:
            return False
    return True

def confirm_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ A’zo boʼldim", callback_data="check_subs")
    return builder.as_markup()

def main_menu_keyboard():
    return ReplyKeyboardMarkup(
        resize_keyboard=True,
        keyboard=[
            [KeyboardButton(text="📢 Konkursda qatnashish")],
            [
                KeyboardButton(text="🎁 Sovg'alar"),
                KeyboardButton(text="🎯 Ballarim")
            ],
            [
                KeyboardButton(text="📊 Reyting"),
                KeyboardButton(text="💡 Shartlar")
            ]
        ]
    )

def konkurs_yakunlandi():
    return datetime.now() >= KONKURS_END_TIME

@router.message(F.text.startswith("/start"))
async def handle_start(message: Message):
    if konkurs_yakunlandi():
        return await message.answer("Konkurs yakunlandi! Qatnashganingiz uchun rahmat!\nNatijalar tez orada kanallarimizda e'lon qilinadi!\n✅ Kanallarimiz:\n👉 @premium_olish_2025\n👉 @TgPremium_Xizmati")

    user_id = str(message.from_user.id)
    users = load_users()
    ref_id = message.text.split(" ")[-1] if " " in message.text else None

    if user_id in users:
        await message.answer("Siz avval a'zo bo'lgansiz.", reply_markup=main_menu_keyboard())
        return

    users[user_id] = {"invited": [], "ref": ref_id, "phone": None}
    save_users(users)

    text = "Konkursda ishtirok etish uchun bizning sahifalarimizga a’zo boʼling!\n\n"
    text += "\n".join([f"👉 {ch}" for ch in CHANNELS])
    await message.answer(text, reply_markup=confirm_keyboard())

@router.callback_query(F.data == "check_subs")
async def handle_check(call: CallbackQuery):
    user_id = str(call.from_user.id)
    users = load_users()

    if await is_subscribed(user_id):
        if users.get(user_id, {}).get("joined"):
            await call.message.answer("✅ Siz allaqachon ro‘yxatdan o‘tgansiz va ishtirokchisiz.")
            return

        # Yangi foydalanuvchini tayyorlash
        users.setdefault(user_id, {})
        users[user_id]["joined"] = True
        users[user_id].setdefault("invited", [])
        users[user_id].setdefault("ref", None)
        users[user_id].setdefault("phone", None)

        ref_id = users[user_id]["ref"]
        if ref_id and ref_id in users:
            if user_id not in users[ref_id].get("invited", []):
                users[ref_id].setdefault("invited", []).append(user_id)

                # 💌 REFERALGA HABAR YUBORILADI
                try:
                    full_name = f"{call.from_user.full_name}"
                    await bot.send_message(
                        int(ref_id),
                        f"🥳 <b>Tabriklaymiz!</b>\nSizning havolangiz orqali <b>{full_name}</b> ro‘yxatdan o‘tdi.\nSizga 1 ball yozildi!"
                    )
                except Exception as e:
                    print(f"Xabar yuborishda xatolik: {e}")

        save_users(users)

        # Telefon raqamini so‘rash
        kb = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
            [KeyboardButton(text="📱 Raqamimni ulashish", request_contact=True)]
        ])
        await call.message.answer("📲 Ro'yxatdan o'tish uchun telefon raqamingizni yuboring:", reply_markup=kb)
    else:
        await call.message.answer("❗ Iltimos, barcha kanallarga obuna bo'ling!", reply_markup=confirm_keyboard())

@router.message(F.contact)
async def handle_contact(message: Message):
    user_id = str(message.from_user.id)
    users = load_users()
    users[user_id]['phone'] = message.contact.phone_number
    save_users(users)
    await message.answer("Quyidagi menyudan kerakli boʼlimni tanlang 👇", reply_markup=main_menu_keyboard())

@router.message(F.text == "📢 Konkursda qatnashish")
async def handle_participate(message: Message):
    user_id = str(message.from_user.id)
    link = f"https://t.me/premium_konkurs2025bot?start={user_id}"
    text = (
        "<i>Assalomu alaykum va rohmatullohi va barokatuh!</i>\n"
        "<b>TELEGRAM PREMIUM ISHQIBOZLARI UCHUN 10 KUNLIK KONKURSGA START BERDIK!</b> ✅\n\n"
        "✅ <b>KONKURS SHARTLARI:</b>\n"
        "1) Botga start berib ko'rsatilgan kanallarga azo bo'lish;\n"
        "2) Botdan shaxsiy link olib uni premium olmoqchi bo'lgan do'st va yaqinlaringizga ulashish;\n"
        "3) Botga faqat real foydalanuvchilarni qo'shish (🛑 Soxta akkauntlarini taklif qilgan ishtirokchilar o'yindan chetlashtiriladi!)\n\n"
        "🔀<b> NATIJALARNI ANIQLASH:</b>\n"
        "🎁 🥇 <b><i>50 tadan ko'p odam qo'shganlar orasida eng ko'p odam qo'shgan 3 kishi kafolatlangan 3 ta sovg'a (1 oylik Telegram premiumga) ega bo'ladi!\n"
        "🥈 🎁 50 tadan kam obunachi qo'shganlar esa tasodifiy o'yinda qatnashib, 3 ta 1 oylik Premium obunasi uchun 60%, 50%, 40%-lik chegirma yoki Telegram starslarga (Chegirma yoki starsni ixtiyoriy tanlaydilar) ega bo'lishlari mumkin!</i></b>\n\n"
        "📝 <b>Konkursda ishtirok eting va ushbu sovg‘alarni yutib olish imkoniyatini boy bermang!</b>\n"
        f"Havolangiz: {link}"
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚀 ISHTIROK ETISH", url=link)]
    ])

    await message.answer(text, reply_markup=keyboard)

@router.message(F.text == "🎁 Sovg'alar")
async def handle_sovgalar(message: Message):
    text = (
        "🎁 <b>KONKURSIMIZDA QATNASHIB, QUYIDAGI SOVG'ALARNI YUTIB OLING:</b>\n\n"
        "🥇 <b>50 tadan ko'p odam taklif qilgan ishtirokchilar orasida</b>\n"
        "     eng ko'p taklif qilgan 3 kishi Telegram Premium (1 oylik) yutadi!\n\n"
        "🥈 <b>50 tadan kam odam taklif qilgan ishtirokchilar orasida</b>\n"
        "     tasodifiy tarzda 3 kishi quyidagilardan birini yutib oladi:\n"
        "     • 1 oylik Telegram Premium uchun 60%, 50%, 40% chegirma yoki 90⭐️, 75⭐️, 50⭐️ Telegram stars (Tanlash imkoniyati mavjud)\n\n"
        "🔄 <b>Natijalar 10-iyul kuni </b>e'lon qilinadi. <b>Do‘stlaringizni taklif qiling — imkoniyatni boy bermang!</b>"
    )
    await message.answer(text)

@router.message(F.text == "🎯 Ballarim")
async def handle_ballarim(message: Message):
    user_id = str(message.from_user.id)
    users = load_users()
    ball = len(users.get(user_id, {}).get("invited", []))
    await message.answer(f"Sizda {ball} ball mavjud.")

@router.message(F.text == "📊 Reyting")
async def handle_reyting(message: Message):
    users = load_users()
    ranking = sorted(users.items(), key=lambda x: len(x[1].get("invited", [])), reverse=True)
    user_id = str(message.from_user.id)
    text = "🏆 Reyting:\n\n"
    for i, (uid, data) in enumerate(ranking[:5]):
        text += f"{i+1}. <a href='tg://user?id={uid}'>Ishtirokchi</a> — {len(data.get('invited', []))} ball\n"
    user_rank = next((i+1 for i, (uid, _) in enumerate(ranking) if uid == user_id), None)
    if user_rank:
        text += f"\nSiz {user_rank}-o'rindasiz."
    await message.answer(text)

@router.message(F.text == "💡 Shartlar")
async def handle_shartlar(message: Message):
    text = (
        "✅ <b>KONKURSNING ASOSIY SHARTLARI:</b>\n"
        "1) Botga start berib, ko'rsatilgan 3 ta kanalga a'zo bo'lish;\n"
        "2) Botdan sizga berilgan shaxsiy havolani tanishlaringiz, do‘stlaringiz va guruhlarga ulashish;\n"
        "3) Faqat haqiqiy foydalanuvchilarni taklif qilish;\n"
        "   🛑 Soxta akkauntlar, boshqa davlat raqamlari yoki nakrutkalar taqiqlanadi!\n\n"
        "🎓 <b>BALLAR QANDAY YIG‘ILADI:</b>\n"
        "• Sizning referal havolangiz orqali botga kirgan, kanallarga a'zo bo‘lgan va “✅ A’zo bo’ldim” tugmasini bosgan har bir foydalanuvchi uchun sizga +1 ball beriladi.\n\n"
        "⏰ Muddat: <b>9-iyul soat 22:00 da </b>yakunlanadi\n"
        "📣 G‘oliblar 10-iyul kuni kanallarda e’lon qilinadi!\n\n"
        "🙂 Halol qatnashing, faol bo‘ling va sovg‘alardan birini yutib oling!\n"
        "<b>Barchaga omad, Alloh Taolonin O'zi madadkor bo‘lsin!</b>"
    )
    await message.answer(text)

@router.message(F.text == "/export")
async def export_data(message: Message):
    if (message.from_user.id) != ADMIN_ID:
        await message.answer("⛔ Sizda ruxsat yo'q.")
        return

    users = load_users()

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Foydalanuvchilar"
    ws.append(["User ID", "Username", "Telefon", "Referal ID", "Ball"])

    for uid, info in users.items():
        user_obj = await bot.get_chat(uid)
        username = user_obj.username if user_obj.username else "—"
        phone = info.get("phone", "—")
        ref = info.get("ref", "—")
        invited_count = len(info.get("invited", []))

        ws.append([uid, f"@{username}" if username != '—' else "—", phone, ref, invited_count])

    path = "users.xlsx"
    wb.save(path)
    await message.answer_document(FSInputFile(path))

@router.message(Command("top10"))
async def show_top10(message: Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔️ Sizda ruxsat yo'q.")
        return
    users = load_users()
    sorted_users = sorted(users.items(), key=lambda x: len(x[1].get("invited", [])), reverse=True)
    text = "👑 <b>TOP-10 Ishtirokchi</b>:\n\n"
    for i, (uid, data) in enumerate(sorted_users[:10], 1):
        name_link = f"<a href='tg://user?id={uid}'>Ishtirokchi {i}</a>"
        ball = len(data.get("invited", [])) + (1 if data.get("joined") else 0)
        text += f"{i}. {name_link} — {ball} ball\n"
    await message.answer(text)


@router.message(Command("timeleft"))
async def show_timeleft(message: Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔️ Sizda ruxsat yo'q.")
        return
    now = datetime.now()
    diff = KONKURS_END - now
    if diff.total_seconds() <= 0:
        await message.answer("⏰ Konkurs tugagan.")
    else:
        kunlar = diff.days
        soat = diff.seconds // 3600
        daqiqa = (diff.seconds % 3600) // 60
        await message.answer(f"⏳ Konkurs tugashiga: {kunlar} kun, {soat} soat, {daqiqa} daqiqa qoldi.")


@router.message(Command("reset"))
async def reset_database(message: Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔️ Sizda ruxsat yo'q.")
        return
    save_users({})
    await message.answer("🧹 Baza tozalandi.")


@router.message(Command("broadcast"))
async def broadcast_message(message: Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔️ Sizda ruxsat yo'q.")
        return
    await message.answer("📩 Iltimos, yubormoqchi bo‘lgan xabaringizni matn shaklida yuboring.")

    @router.message()
    async def get_broadcast_text(broadcast_msg: Message):
        text = broadcast_msg.text
        users = load_users()
        count = 0
        for uid in users:
            try:
                await bot.send_message(chat_id=int(uid), text=text)
                count += 1
            except:
                continue
        await broadcast_msg.answer(f"📤 Xabar {count} ta foydalanuvchiga yuborildi.")
        router.message.middleware_stack.middlewares.pop()  # faqat 1 martalik broadcast
@router.message()
async def unknown_message_handler(message: Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("❌ Botga yozish mumkin emas. Iltimos, pastdagi tugmalardan foydalaning.")


async def main():
    dp.include_router(router)
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())