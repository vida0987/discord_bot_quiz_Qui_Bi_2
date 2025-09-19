import discord
from discord.ext import commands
from discord import app_commands
import random
import asyncio
import json
import os

# Config
TOKEN = 'MTQxNzE0MzYyMjQ5ODc4MzM0Mw.GBol5V.J_Mj5ROmKYX1E7X35WyU_NR2SAvxKAV8p88M18'
QUESTION_TIMEOUT = 30
NUM_QUESTIONS = 10

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Load câu hỏi từ file JSON
try:
    with open("questions.json", "r", encoding="utf-8") as f:
        all_questions = json.load(f)["questions"]
    print(f"✅ Đã tải {len(all_questions)} câu hỏi thành công!")
except Exception as e:
    print(f"❌ Lỗi khi tải questions.json: {e}")
    all_questions = []


@bot.event
async def on_ready():
    try:
        await bot.tree.sync()
        print(f"🤖 {bot.user} đã sẵn sàng với slash command /quiz")
    except Exception as e:
        print(f"❌ Lỗi sync commands: {e}")


@bot.tree.command(name="quiz", description="Bắt đầu quiz với 10 câu hỏi ngẫu nhiên")
async def quiz(interaction: discord.Interaction):
    if len(all_questions) < NUM_QUESTIONS:
        await interaction.response.send_message("❌ Không đủ câu hỏi để bắt đầu quiz!", ephemeral=True)
        return

    await interaction.response.send_message(
        f"🎯 Quiz bắt đầu với {NUM_QUESTIONS} câu hỏi! Bạn có {QUESTION_TIMEOUT} giây cho mỗi câu.\n"
        f"Chọn đáp án bằng cách click emoji 🇦 🇧 🇨 🇩",
        ephemeral=False
    )

    selected_questions = random.sample(all_questions, NUM_QUESTIONS)
    score = 0
    wrong_answers = []

    for i, q in enumerate(selected_questions, 1):
        # Embed câu hỏi
        embed = discord.Embed(
            title=f"❓ Câu hỏi {i}/{NUM_QUESTIONS}",
            description=q["question"],
            color=discord.Color.blue()
        )
        options_text = ""
        for option, text in q["options"].items():
            emoji = {"A": "🇦", "B": "🇧", "C": "🇨", "D": "🇩"}[option]
            options_text += f"{emoji} **{option}.** {text}\n"
        embed.add_field(name="📋 Các lựa chọn:", value=options_text, inline=False)
        embed.set_footer(text=f"⏰ Thời gian: {QUESTION_TIMEOUT} giây | 🎯 Điểm hiện tại: {score}")

        # Gửi câu hỏi
        question_msg = await interaction.channel.send(embed=embed)

        # Thêm reactions
        for emoji in ["🇦", "🇧", "🇨", "🇩"]:
            await question_msg.add_reaction(emoji)

        # Chờ câu trả lời
        def check(reaction, user):
            return (
                user == interaction.user
                and str(reaction.emoji) in ["🇦", "🇧", "🇨", "🇩"]
                and reaction.message.id == question_msg.id
            )

        try:
            reaction, user = await bot.wait_for("reaction_add", timeout=QUESTION_TIMEOUT, check=check)
        except asyncio.TimeoutError:
            await interaction.channel.send(
                f"⏰ Hết thời gian! Đáp án đúng: **{q['correct_answer']}. {q['options'][q['correct_answer']]}**"
            )
            wrong_answers.append(q["question"])
            continue

        # Đáp án user chọn
        emoji_to_option = {"🇦": "A", "🇧": "B", "🇨": "C", "🇩": "D"}
        user_answer = emoji_to_option.get(str(reaction.emoji), "")

        if user_answer == q["correct_answer"]:
            score += 1
            await interaction.channel.send(f"✅ Chính xác! ({score}/{i})")
        else:
            await interaction.channel.send(
                f"❌ Sai rồi! Bạn chọn {user_answer}, đáp án đúng là {q['correct_answer']}."
            )
            wrong_answers.append(q["question"])

        await asyncio.sleep(2)

    # Kết quả cuối cùng
    percentage = round((score / NUM_QUESTIONS) * 100, 1)
    result_embed = discord.Embed(
        title="📊 Kết Quả Quiz",
        description=f"🎯 Điểm số: {score}/{NUM_QUESTIONS} ({percentage}%)",
        color=discord.Color.green() if percentage >= 70 else discord.Color.red(),
    )
    await interaction.channel.send(embed=result_embed)


if __name__ == "__main__":
    bot.run(TOKEN)
