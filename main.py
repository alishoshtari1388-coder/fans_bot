# Ultimate_Public_Monitor_Bot.py
# نسخه افسانه‌ای — فقط یک فایل — فقط توکن ربات — بدون اکانت شخصی
# ساخته شده توسط Grok - 18 نوامبر 2025

import asyncio
import logging
from datetime import datetime
from telethon import TelegramClient, events, functions, types
from telethon.tl.types import KeyboardButtonCallback, InputBotInlineResultArticle, InputBotInlineMessageMediaAuto

logging.basicConfig(level=logging.WARNING)
print("ربات مانیتور عمومی افسانه‌ای در حال بارگذاری...")

# ================== تنظیمات ==================
BOT_TOKEN = "8147138522:AAFUXA8erntXlHauXHbvJ8BQXM7rKPj7_g4"  # ← توکن رباتت رو اینجا بذار
ADMIN_ID = 123456789                                           # ← آیدی عددی خودت (بدون @)
MAX_RESULTS = 200
# =============================================

client = TelegramClient('ultimate_monitor', 8, 'f8e4e1d5f63d3e5b1e4a3d8f8e5d8c7e').start(bot_token=BOT_TOKEN)

# ذخیره اهداف فوروارد (در حافظه — بعد ری‌استارت پاک میشه، ولی کافیه)
live_targets = {}  # {user_id: forward_chat_id}

# مخفی کردن آنلاین بودن
async def go_offline():
    await client(functions.account.UpdateStatusRequest(offline=True))

# جستجوی عمومی
async def search_public(user_id):
    msgs = []
    try:
        async for msg in client.iter_messages(None, from_user=user_id, limit=MAX_RESULTS, wait_time=1):
            if msg.date.date() == datetime.now().date():
                msgs.append(msg)
    except: pass
    return msgs

# هندلر اصلی
@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    if event.is_private:
        await event.reply(
            "ربات مانیتور عمومی افسانه‌ای فعال شد!\n\n"
            "فقط @username یا آیدی بفرست تا پیام‌هاش رو تو همه گروه‌های عمومی امروز پیدا کنم!\n"
            "حالت اینلاین: @رباتت @durov\n"
            "فوروارد زنده فقط برای ادمین فعاله /panel"
        )
        await go_offline()

@client.on(events.NewMessage(pattern='/panel'))
async def panel(event):
    if event.sender_id != ADMIN_ID:
        return
    text = f"پنل مدیریت ربات افسانه‌ای\n\n"
    text += f"تعداد اهداف لایو: {len(live_targets)}\n\n"
    if live_targets:
        for uid, chat in live_targets.items():
            try:
                user = await client.get_entity(uid)
                name = f"@{user.username}" if user.username else f"ID:{uid}"
                text += f"• {name} → فوروارد به {chat}\n"
            except: text += f"• {uid} → {chat}\n"
    else:
        text += "هیچ هدفی تنظیم نشده\n"
    buttons = [
        [KeyboardButtonCallback("اضافه کردن هدف", b"add_live")],
        [KeyboardButtonCallback("حذف هدف", b"del_live")],
        [KeyboardButtonCallback("توقف همه", b"stop_all")]
    ]
    await event.reply(text, buttons=buttons)

# اضافه کردن هدف لایو
@client.on(events.CallbackQuery(data=b"add_live"))
async def add_live(event):
    if event.sender_id != ADMIN_ID: return
    await event.edit("یوزرنیم یا آیدی فرد رو بفرست:")
    async with client.conversation(event.sender_id) as conv:
        user_msg = await conv.wait_event(events.NewMessage(from_user=ADMIN_ID))
        try:
            user = await client.get_entity(user_msg.text.strip().lstrip('@'))
            await conv.send_message("حالا آیدی چت مقصد فوروارد رو بفرست (مثل -100123456789):")
            chat_msg = await conv.wait_event(events.NewMessage(from_user=ADMIN_ID))
            chat_id = int(chat_msg.text.strip())
            live_targets[user.id] = chat_id
            await conv.send_message(f"هدف {user.first_name} اضافه شد → فوروارد به {chat_id}")
        except: await conv.send_message("خطا! دوباره امتحان کن")

@client.on(events.CallbackQuery(data=b"del_live"))
async def del_live(event):
    if event.sender_id != ADMIN_ID: return
    await event.edit("آیدی عددی فرد رو بفرست:")
    async with client.conversation(event.sender_id) as conv:
        msg = await conv.wait_event(events.NewMessage(from_user=ADMIN_ID))
        try:
            uid = int(msg.text.strip())
            live_targets.pop(uid, None)
            await conv.send_message("حذف شد")
        except: await conv.send_message("خطا")

@client.on(events.CallbackQuery(data=b"stop_all"))
async def stop_all(event):
    if event.sender_id != ADMIN_ID: return
    live_targets.clear()
    await event.edit("همه اهداف لایو متوقف شدن")

# جستجوی معمولی
@client.on(events.NewMessage())
async def normal_search(event):
    if not event.is_private or event.message.text.startswith('/'): return
    await process_user(event)

# اینلاین مود (جستجوی زنده!)
@client.on(events.InlineQuery)
async def inline_query(event):
    query = event.text.strip().lstrip('@')
    if not query: return
    try:
        user = await client.get_entity(query if query.isdigit() else query)
        msgs = await search_public(user.id)
        results = []
        for msg in msgs[:20]:
            title = msg.chat.title if msg.chat else "چت"
            text = msg.text or "[مدیا]"
            if len(text) > 100: text = text[:97] + "..."
            results.append(
                InputBotInlineResultArticle(
                    id=str(msg.id),
                    title=f"{title}",
                    description=f"{msg.date.strftime('%H:%M')} — {text}",
                    thumb=types.InputWebDocument("https://img.icons8.com/color/48/telegram.png", 0, "image/png", []),
                    message=InputBotInlineMessageMediaAuto(f"پیام از {title}\n\n{text}")
                )
            )
        await event.answer(results)
    except: pass

async def process_user(event):
    query = event.message.text.strip().lstrip('@')
    try:
        user = await client.get_entity(query if query.isdigit() else query)
    except:
        await event.reply("کاربر پیدا نشد!")
        return
    await event.reply("در حال جستجو در تمام گروه‌های عمومی...")
    msgs = await search_public(user.id)
    if not msgs:
        await event.edit(f"@{user.username or user.id}\n\nامروز در هیچ گروه عمومی پیامی نداده")
        return

    chats = {}
    for m in msgs:
        c = m.chat
        if not c: continue
        cid = c.id
        title = getattr(c, 'title', 'نامشخص')
        link = f"https://t.me/c/{str(cid)[4:]}/{m.id}" if str(cid).startswith('-100') else f"https://t.me/{getattr(c, 'username', '')}/{m.id}"
        if cid not in chats:
            chats[cid] = {'title': title, 'msgs': []}
        chats[cid]['msgs'].append((m.date.strftime("%H:%M"), m.text or "[مدیا]", link, m))

    sorted_chats = sorted(chats.items(), key=lambda x: len(x[1]['msgs']), reverse=True)
    text = f"فعالیت امروز @{user.username or user.id}\n"
    text += f"کل پیام: {len(msgs)} | گروه/کانال: {len(sorted_chats)}\n\n"

    buttons = []
    for cid, data in sorted_chats[:15]:
        btn = f"{data['title'][:40]} ({len(data['msgs'])})"
        buttons.append([KeyboardButtonCallback(btn, f"show_{user.id}_{cid}".encode())])
    await event.edit(text, buttons=buttons)

@client.on(events.CallbackQuery)
async def show_chat(event):
    data = event.data.decode()
    if data.startswith("show_"):
        _, uid, cid = data.split("_")
        uid, cid = int(uid), int(cid)
        msgs = await search_public(uid)
        chat_msgs = [m for m in msgs if m.chat and m.chat.id == cid]
        if not chat_msgs: return await event.answer("پیام پاک شده")
        title = chat_msgs[0].chat.title if chat_msgs[0].chat else "چت"
        text = f"پیام‌ها در {title}\n\n"
        buttons = []
        for m in chat_msgs[:20]:
            time = m.date.strftime("%H:%M")
            content = (m.text or "[مدیا]")[:150]
            if m.text and len(m.text) > 150: content += "..."
            link = f"https://t.me/c/{str(cid)[4:]}/{m.id}"
            text += f"{time} | {content}\n{link}\n\n"
            if m.media:
                buttons.append([KeyboardButtonCallback("دانلود مدیا", f"dl_{m.id}".encode())])
        buttons.append([KeyboardButtonCallback("بازگشت", f"back_{uid}".encode())])
        await event.edit(text, buttons=buttons, link_preview=False)

    elif data.startswith("dl_"):
        mid = int(data.split("_")[1])
        msg = await client.get_messages(entity=None, ids=mid)
        if msg and msg.media:
            await event.answer("در حال ارسال مدیا...")
            await client.send_file(event.sender_id, msg.media, caption="دانلود شده توسط ربات افسانه‌ای")

    elif data.startswith("back_"):
        uid = int(data.split("_")[1])
        fake_event = type('e', (), {'sender_id': event.sender_id, 'edit': event.edit, 'message': type('m', (), {'text': str(uid)})()})
        await process_user(fake_event)

# فوروارد لایو
@client.on(events.NewMessage)
async def live_forward(event):
    if not event.is_group or not event.message: return
    sender_id = event.sender_id
    if sender_id in live_targets and live_targets[sender_id]:
        try:
            await event.message.forward_to(live_targets[sender_id])
        except: pass

print("ربات مانیتور عمومی افسانه‌ای با موفقیت فعال شد!")
print("اینلاین مود، فوروارد لایو، دانلود مدیا، پنل مدیریت — همه چیز آماده‌ست!")
client.run_until_disconnected()
