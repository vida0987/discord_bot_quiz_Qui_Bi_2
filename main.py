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
        await interaction.response.send_message("❌ Không đủ câu hỏi để bắt đầu quiz!", ephemeral=True)
        return

    await interaction.response.send_message(
        f"🎯 Quiz bắt đầu với {NUM_QUESTIONS} câu hỏi! Bạn có {QUESTION_TIMEOUT} giây cho mỗi câu.\n"
        f"Trả lời bằng cách gõ **A, B, C, D** hoặc **a, b, c, d** vào chat",
        ephemeral=False
    )

    selected_questions = random.sample(all_questions, NUM_QUESTIONS)
    score = 0
    user_answers = []
    correct_answers = []

    for i, q in enumerate(selected_questions, 1):
        # Embed câu hỏi
        embed = discord.Embed(
            title=f"❓ Câu hỏi {i}/{NUM_QUESTIONS}",
            description=q["question"],
            color=discord.Color.blue()
        )
        options_text = ""
        for option, text in q["options"].items():
            options_text += f"**{option}.** {text}\n"
        embed.add_field(name="📋 Các lựa chọn:", value=options_text, inline=False)
        embed.set_footer(text=f"⏰ Thời gian: {QUESTION_TIMEOUT} giây | Gõ A, B, C, D để trả lời")

        # Gửi câu hỏi
        question_msg = await interaction.channel.send(embed=embed)

        # Chờ câu trả lời từ chat
        def check(message):
            return (
                message.author == interaction.user
                and message.channel == interaction.channel
                and message.content.upper() in ["A", "B", "C", "D"]
            )

        try:
            user_message = await bot.wait_for("message", timeout=QUESTION_TIMEOUT, check=check)
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

        # Lưu câu trả lời
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

        # Chờ 1 giây trước câu hỏi tiếp theo
        await asyncio.sleep(1)

    # Kết quả cuối cùng
    percentage = round((score / NUM_QUESTIONS) * 100, 1)
    wrong_count = NUM_QUESTIONS - score
    
    # Thông báo kết quả tổng quan
    result_message = f"🎯 **Kết quả Quiz:**\n"
    result_message += f"✅ Câu đúng: {score}\n"
    result_message += f"❌ Câu sai: {wrong_count}\n"
    result_message += f"📊 Tỷ lệ: {percentage}%\n\n"
    
    # Chi tiết từng câu trả lời
    result_message += "📝 **Chi tiết câu trả lời:**\n"
    for i, answer in enumerate(user_answers, 1):
        status = "✅" if answer["is_correct"] else "❌"
        result_message += f"{status} **Câu {i}:** Bạn chọn {answer['user_answer']}, đáp án đúng là {answer['correct_answer']}\n"
    
    await interaction.channel.send(result_message)


if __name__ == "__main__":
    if not TOKEN:
        print("❌ Lỗi: Không tìm thấy DISCORD_TOKEN!")
        print("📝 Vui lòng tạo file .env và thêm DISCORD_TOKEN=your_token_here")
        print("📝 Hoặc cài đặt biến môi trường DISCORD_TOKEN")
    else:
        print("🚀 Đang khởi động bot...")
        try:
            bot.run(TOKEN)
        except discord.LoginFailure:
            print("❌ Lỗi đăng nhập: Token Discord không hợp lệ!")
        except Exception as e:
            print(f"❌ Lỗi khởi động bot: {e}")
