import discord
from discord.ext import commands
from discord import app_commands
import random
import asyncio
import json
import os

# Config
import os
from dotenv import load_dotenv
from keep_alive import keep_alive

# Load environment variables
load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')
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
        await interaction.response.send_message(
            "❌ Không đủ câu hỏi để bắt đầu quiz!", ephemeral=True
        )
        return

    # ✅ Defer the interaction (acknowledge quickly)
    await interaction.response.defer()

    # Send intro as followup (not response)
    await interaction.followup.send(
        f"🎯 Quiz bắt đầu với {NUM_QUESTIONS} câu hỏi! "
        f"Bạn có {QUESTION_TIMEOUT} giây cho mỗi câu.\n"
        f"Trả lời bằng cách gõ **A, B, C, D** hoặc **a, b, c, d** vào chat"
    )

    selected_questions = random.sample(all_questions, NUM_QUESTIONS)
    score = 0
    user_answers = []

    for i, q in enumerate(selected_questions, 1):
        embed = discord.Embed(
            title=f"❓ Câu hỏi {i}/{NUM_QUESTIONS}",
            description=q["question"],
            color=discord.Color.blue()
        )
        options_text = "\n".join(
            f"**{opt}.** {txt}" for opt, txt in q["options"].items()
        )
        embed.add_field(name="📋 Các lựa chọn:", value=options_text, inline=False)
        embed.set_footer(text=f"⏰ Thời gian: {QUESTION_TIMEOUT} giây | Gõ A, B, C, D để trả lời")

        # Send question
        await interaction.channel.send(embed=embed)

        def check(message):
            return (
                message.author == interaction.user
                and message.channel == interaction.channel
                and message.content.upper() in ["A", "B", "C", "D"]
            )

        try:
            user_message = await bot.wait_for(
                "message", timeout=QUESTION_TIMEOUT, check=check
            )
            user_answer = user_message.content.upper()
        except asyncio.TimeoutError:
            await interaction.channel.send(
                f"⏰ Hết thời gian! Đáp án đúng: **{q['correct_answer']}. {q['options'][q['correct_answer']]}**"
            )
            user_answer = "Không trả lời"
            user_answers.append({
                "question": q["question"],
                "user_answer": user_answer,
                "correct_answer": q["correct_answer"],
                "correct_text": q["options"][q["correct_answer"]],
                "is_correct": False
            })
            continue

        # Save answer
        is_correct = user_answer == q["correct_answer"]
        if is_correct:
            score += 1

        user_answers.append({
            "question": q["question"],
            "user_answer": user_answer,
            "correct_answer": q["correct_answer"],
            "correct_text": q["options"][q["correct_answer"]],
            "is_correct": is_correct
        })

        await asyncio.sleep(1)

    # Final result
    percentage = round((score / NUM_QUESTIONS) * 100, 1)
    wrong_count = NUM_QUESTIONS - score

    result_message = (
        f"🎯 **Kết quả Quiz:**\n"
        f"✅ Câu đúng: {score}\n"
        f"❌ Câu sai: {wrong_count}\n"
        f"📊 Tỷ lệ: {percentage}%\n\n"
        "📝 **Chi tiết câu trả lời:**\n"
    )

    for i, ans in enumerate(user_answers, 1):
        status = "✅" if ans["is_correct"] else "❌"
        result_message += (
            f"{status} **Câu {i}:** Bạn chọn {ans['user_answer']}, "
            f"đáp án đúng là {ans['correct_answer']}\n"
        )

    await interaction.followup.send(result_message)


if __name__ == "__main__":
    if not TOKEN:
        print("❌ Lỗi: Không tìm thấy DISCORD_TOKEN!")
        print("📝 Vui lòng tạo file .env và thêm DISCORD_TOKEN=your_token_here")
        print("📝 Hoặc cài đặt biến môi trường DISCORD_TOKEN")
    else:
        print("🚀 Đang khởi động bot...")
        try:
            keep_alive()
            bot.run(TOKEN)
        except discord.LoginFailure:
            print("❌ Lỗi đăng nhập: Token Discord không hợp lệ!")
        except Exception as e:
            print(f"❌ Lỗi khởi động bot: {e}")
