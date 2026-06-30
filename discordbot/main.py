import disnake
from disnake.ext import commands
import aiohttp
import os

intents = disnake.Intents.default()
intents.message_content = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents,
)

URL = os.environ.get('URL', 'http://web:8000')
SECRET_BOT = os.environ.get('BOT_API_SECRET')
BOT_TOKEN = os.environ.get('BOT_TOKEN')

@bot.event
async def on_ready():
    print(f"Бот {bot.user} запущен и готов к работе!")

class NoteModal(disnake.ui.Modal):
    def __init__(self, record_id, action, original_content):
        self.record_id = record_id
        self.action = action
        self.original_content = original_content
        components = [
            disnake.ui.TextInput(
                label="Заметка (необязательно)",
                placeholder="Причина отклонения или комментарий...",
                custom_id="notes",
                style=disnake.TextInputStyle.paragraph,
                required=False,
                max_length=500,
            )
        ]
        title = "Принятие рекорда" if action == "approve" else "Отклонение рекорда"
        super().__init__(title=title, components=components)

    async def callback(self, inter: disnake.ModalInteraction):
        notes = inter.text_values["notes"]
        
        # Параметры запроса к API
        url = f"{URL}/api/records/{self.record_id}/moderate/"
        payload = {
            "secret": SECRET_BOT,
            "action": "approved" if self.action == "approve" else "rejected",
            "notes": notes,
            "moderator": str(inter.author)
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as resp:
                    data = await resp.json()
                    
                    if resp.status == 200 and (data.get("success") or data.get("status")):
                        status_text = "✅ **ПРИНЯТО**" if self.action == "approve" else "❌ **ОТКЛОНЕНО**"
                        note_text = f"\n📝 Заметка: *{notes}*" if notes else ""
                        
                        # ФОРМИРУЕМ НОВОЕ СОДЕРЖАНИЕ
                        new_content = f"{self.original_content}\n\n{status_text} модератором {inter.author.mention}{note_text}"
                        
                        # РЕДАКТИРУЕМ ИСХОДНОЕ СООБЩЕНИЕ И УДАЛЯЕМ КНОПКИ
                        # В ModalInteraction response.edit_message редактирует сообщение, вызвавшее модал
                        await inter.response.edit_message(content=new_content, components=[])
                    else:
                        error_msg = data.get('error', 'Неизвестная ошибка API')
                        await inter.response.send_message(f"⚠️ Ошибка: {error_msg}", ephemeral=True)
        except Exception as e:
            await inter.response.send_message(f"❌ Ошибка соединения: {e}", ephemeral=True)

@bot.event
async def on_button_click(inter: disnake.MessageInteraction):
    custom_id = inter.component.custom_id
    if not custom_id:
        return

    if custom_id.startswith(("approve_", "reject_", "note_")):
        parts = custom_id.split("_")
        action_prefix = parts[0]
        record_id = parts[1]

        # Запоминаем действие: одобрение или отказ
        action = "approve" if action_prefix == "approve" or action_prefix == "note" else "reject"
        
        # Передаем текущий текст сообщения, чтобы потом его дополнить
        await inter.response.send_modal(NoteModal(record_id, action, inter.message.content))

@bot.slash_command(description="Узнать место в топе ДВ Слееров")
async def rank(
    inter: disnake.ApplicationCommandInteraction,
    member: disnake.Member = commands.Param(default=None, description="Кого ищем?")
):
    await inter.response.defer()
    target = member if member else inter.author
    url = f"{URL}/api/rank/{target.id}"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                response = await resp.json()
                if response.get("success"):
                    embed = disnake.Embed(title=f"🏆 Статистика: {response['username']}", color=disnake.Color.gold())
                    embed.set_thumbnail(url=target.display_avatar.url)
                    embed.add_field(name="💻 ПК", value=f"Место: #{response['rank_pc'] or '—'}\nОчки: {response['score_pc']}", inline=True)
                    embed.add_field(name="📱 Мобайл", value=f"Место: #{response['rank_mobile'] or '—'}\nОчки: {response['score_mobile']}", inline=True)
                    await inter.edit_original_response(embed=embed)
                else:
                    await inter.edit_original_response(content=f"❌ {response.get('error', 'Игрок не найден')}")
    except Exception as e:
        await inter.edit_original_response(content=f"❌ Ошибка сервера: {e}")

@bot.slash_command(description="Посмотреть профиль игрока")
async def profile(
    inter: disnake.ApplicationCommandInteraction,
    member: disnake.Member = commands.Param(default=None, description="Кого ищем?")
):
    await inter.response.defer()
    target = member if member else inter.author
    url = f"{URL}/api/profile/{target.id}"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                response = await resp.json()
                if response.get("success"):
                    embed = disnake.Embed(
                        title=f"👤 Профиль: {response['username']}",
                        description=f"📍 Регион: **{response['region']}**",
                        color=disnake.Color.orange(),
                        url=response.get('site_url')
                    )
                    embed.set_thumbnail(url=target.display_avatar.url)

                    # Статистика
                    embed.add_field(
                        name="💻 ПК",
                        value=f"🏆 Место: `#{response['rank_pc'] or '—'}`\n🔥 Очки: `{response['score_pc']}`\n⭐ Hardest: **{response['hardest_pc']}**",
                        inline=True
                    )
                    embed.add_field(
                        name="📱 Мобайл",
                        value=f"🏆 Место: `#{response['rank_mobile'] or '—'}`\n🔥 Очки: `{response['score_mobile']}`\n⭐ Hardest: **{response['hardest_mobile']}**",
                        inline=True
                    )

                    # Достижения
                    if response.get("top_achievements"):
                        achievements_text = "\n".join([f"• {a}" for a in response["top_achievements"]])
                        embed.add_field(name="🚀 Топ достижений", value=achievements_text, inline=False)

                    # Общая инфа
                    embed.add_field(name="✅ Всего рекордов", value=f"`{response['victors_count']}`", inline=True)

                    footer_text = f"Запросил {inter.author.display_name}"
                    embed.set_footer(text=footer_text, icon_url=inter.author.display_avatar.url)

                    await inter.edit_original_response(embed=embed)
                else:
                    await inter.edit_original_response(content=f"❌ {response.get('error', 'Игрок не найден')}")
    except Exception as e:
        await inter.edit_original_response(content=f"❌ Ошибка сервера: {e}")

bot.run(BOT_TOKEN)
