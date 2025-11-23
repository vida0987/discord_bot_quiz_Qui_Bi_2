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


# Class để quản lý battle với buttons
class BattleView(discord.ui.View):
    def __init__(self, player1, player2, player1_name, player2_name):
        super().__init__(timeout=60)
        self.player1 = player1
        self.player2 = player2
        self.player1_name = player1_name
        self.player2_name = player2_name
        self.player1_hp = 30
        self.player2_hp = 30
        self.player1_action = None
        self.player2_action = None
        self.current_turn = 1  # 1 = player1, 2 = player2
        self.battle_log = []
        self.message = None
        self.action_message = None

    async def check_both_ready(self):
        if self.player1_action is not None and self.player2_action is not None:
            # Disable buttons khi cả 2 đã chọn
            if hasattr(self, 'action_message') and self.action_message:
                for item in self.view.children:
                    item.disabled = True
                try:
                    await self.action_message.edit(view=self.view)
                except:
                    pass  # Message có thể đã bị xóa hoặc không thể edit
            await self.execute_round()

    async def execute_round(self):
        # Tính sát thương cho player1
        if self.player1_action == "light":
            damage1 = random.randint(1, 4) + random.randint(1, 4)
            action1_text = f"Đánh nhẹ (2d4 = {damage1})"
        elif self.player1_action == "medium":
            damage1 = random.randint(1, 8)
            action1_text = f"Đánh trung bình (1d8 = {damage1})"
        else:  # heavy
            damage1 = random.randint(1, 12)
            recoil1 = random.randint(1, 4)
            self.player1_hp -= recoil1
            action1_text = f"Đánh mạnh (1d12 = {damage1}, tự nhận {recoil1} sát thương)"
            if self.player1_hp < 0:
                self.player1_hp = 0

        # Tính sát thương cho player2
        if self.player2_action == "light":
            damage2 = random.randint(1, 4) + random.randint(1, 4)
            action2_text = f"Đánh nhẹ (2d4 = {damage2})"
        elif self.player2_action == "medium":
            damage2 = random.randint(1, 8)
            action2_text = f"Đánh trung bình (1d8 = {damage2})"
        else:  # heavy
            damage2 = random.randint(1, 12)
            recoil2 = random.randint(1, 4)
            self.player2_hp -= recoil2
            action2_text = f"Đánh mạnh (1d12 = {damage2}, tự nhận {recoil2} sát thương)"
            if self.player2_hp < 0:
                self.player2_hp = 0

        # Áp dụng sát thương
        self.player2_hp -= damage1
        self.player1_hp -= damage2
        
        if self.player1_hp < 0:
            self.player1_hp = 0
        if self.player2_hp < 0:
            self.player2_hp = 0

        # Tạo embed kết quả lượt đánh
        round_embed = discord.Embed(
            title=f"⚔️ Lượt đánh #{self.current_turn}",
            color=discord.Color.red()
        )
        round_embed.add_field(
            name=f"👤 {self.player1_name}",
            value=f"{action1_text}\n💚 HP: {self.player1_hp}/30",
            inline=False
        )
        round_embed.add_field(
            name=f"👤 {self.player2_name}",
            value=f"{action2_text}\n💚 HP: {self.player2_hp}/30",
            inline=False
        )

        await self.message.channel.send(embed=round_embed)

        # Kiểm tra kết thúc
        if self.player1_hp <= 0 or self.player2_hp <= 0:
            await self.end_battle()
            return

        # Reset actions và tiếp tục lượt tiếp theo
        self.player1_action = None
        self.player2_action = None
        self.current_turn += 1

        # Gửi buttons cho lượt tiếp theo
        await self.send_action_buttons()

    async def send_action_buttons(self):
        embed = discord.Embed(
            title=f"⚔️ Lượt đánh #{self.current_turn} - Chọn hành động!",
            description=f"**{self.player1_name}** vs **{self.player2_name}**\n\n"
                       f"💚 **{self.player1_name}:** {self.player1_hp}/30 HP\n"
                       f"💚 **{self.player2_name}:** {self.player2_hp}/30 HP",
            color=discord.Color.orange()
        )
        embed.add_field(
            name="📋 Hành động:",
            value="⚔️ **Đánh nhẹ:** 2d4 (2-8 sát thương)\n"
                  "🗡️ **Đánh trung bình:** 1d8 (1-8 sát thương)\n"
                  "💥 **Đánh mạnh:** 1d12 (1-12 sát thương) + tự nhận 1d4 (1-4 sát thương)",
            inline=False
        )

        # Tạo view với buttons cho cả 2 người chơi
        view = discord.ui.View(timeout=60)
        
        async def light_attack_callback(interaction: discord.Interaction):
            if interaction.user == self.player1 and self.player1_action is None:
                self.player1_action = "light"
                await interaction.response.send_message("✅ Bạn đã chọn **Đánh nhẹ** (2d4)", ephemeral=True)
            elif interaction.user == self.player2 and self.player2_action is None:
                self.player2_action = "light"
                await interaction.response.send_message("✅ Bạn đã chọn **Đánh nhẹ** (2d4)", ephemeral=True)
            else:
                if interaction.user not in [self.player1, self.player2]:
                    await interaction.response.send_message("❌ Bạn không phải người chơi trong battle này!", ephemeral=True)
                else:
                    await interaction.response.send_message("❌ Bạn đã chọn hành động rồi!", ephemeral=True)
                return
            
            await self.check_both_ready()

        async def medium_attack_callback(interaction: discord.Interaction):
            if interaction.user == self.player1 and self.player1_action is None:
                self.player1_action = "medium"
                await interaction.response.send_message("✅ Bạn đã chọn **Đánh trung bình** (1d8)", ephemeral=True)
            elif interaction.user == self.player2 and self.player2_action is None:
                self.player2_action = "medium"
                await interaction.response.send_message("✅ Bạn đã chọn **Đánh trung bình** (1d8)", ephemeral=True)
            else:
                if interaction.user not in [self.player1, self.player2]:
                    await interaction.response.send_message("❌ Bạn không phải người chơi trong battle này!", ephemeral=True)
                else:
                    await interaction.response.send_message("❌ Bạn đã chọn hành động rồi!", ephemeral=True)
                return
            
            await self.check_both_ready()

        async def heavy_attack_callback(interaction: discord.Interaction):
            if interaction.user == self.player1 and self.player1_action is None:
                self.player1_action = "heavy"
                await interaction.response.send_message("✅ Bạn đã chọn **Đánh mạnh** (1d12 + tự nhận 1d4)", ephemeral=True)
            elif interaction.user == self.player2 and self.player2_action is None:
                self.player2_action = "heavy"
                await interaction.response.send_message("✅ Bạn đã chọn **Đánh mạnh** (1d12 + tự nhận 1d4)", ephemeral=True)
            else:
                if interaction.user not in [self.player1, self.player2]:
                    await interaction.response.send_message("❌ Bạn không phải người chơi trong battle này!", ephemeral=True)
                else:
                    await interaction.response.send_message("❌ Bạn đã chọn hành động rồi!", ephemeral=True)
                return
            
            await self.check_both_ready()

        light_btn = discord.ui.Button(label="⚔️ Đánh nhẹ (2d4)", style=discord.ButtonStyle.primary)
        light_btn.callback = light_attack_callback
        view.add_item(light_btn)

        medium_btn = discord.ui.Button(label="🗡️ Đánh trung bình (1d8)", style=discord.ButtonStyle.success)
        medium_btn.callback = medium_attack_callback
        view.add_item(medium_btn)

        heavy_btn = discord.ui.Button(label="💥 Đánh mạnh (1d12 + tự nhận 1d4)", style=discord.ButtonStyle.danger)
        heavy_btn.callback = heavy_attack_callback
        view.add_item(heavy_btn)

        self.view = view
        action_message = await self.message.channel.send(embed=embed, view=view)
        self.action_message = action_message

    async def end_battle(self):
        winner_embed = discord.Embed(
            title="🏆 KẾT QUẢ BATTLE 🏆",
            color=discord.Color.gold()
        )

        if self.player1_hp <= 0 and self.player2_hp <= 0:
            winner_embed.description = "🤝 Hòa! Cả 2 đều hết máu cùng lúc! 🤝"
            winner_embed.color = discord.Color.blue()
        elif self.player1_hp <= 0:
            winner_embed.description = f"🎉 **{self.player2_name}** là người chiến thắng! 🎉"
            winner_embed.color = discord.Color.green()
        elif self.player2_hp <= 0:
            winner_embed.description = f"🎉 **{self.player1_name}** là người chiến thắng! 🎉"
            winner_embed.color = discord.Color.green()

        winner_embed.add_field(
            name=f"👤 {self.player1_name}",
            value=f"💚 HP: {self.player1_hp}/30",
            inline=True
        )
        winner_embed.add_field(
            name=f"👤 {self.player2_name}",
            value=f"💚 HP: {self.player2_hp}/30",
            inline=True
        )

        await self.message.channel.send(embed=winner_embed)
        self.stop()


@bot.tree.command(name="battle_qui_bi", description="Đấu với người khác - ai hết máu trước thì thua!")
@app_commands.describe(
    opponent="Người bạn muốn thách đấu",
)
async def battle(
    interaction: discord.Interaction,
    opponent: discord.Member,
    player1_name: str = None,
    player2_name: str = None
):
    # Kiểm tra không được tự đấu với chính mình
    if opponent.id == interaction.user.id:
        await interaction.response.send_message(
            "❌ Bạn không thể đấu với chính mình!", ephemeral=True
        )
        return
    
    # Kiểm tra không được đấu với bot
    if opponent.bot:
        await interaction.response.send_message(
            "❌ Bạn không thể đấu với bot!", ephemeral=True
        )
        return

    # Sử dụng tên được cung cấp hoặc tên Discord
    p1_name = player1_name if player1_name else interaction.user.display_name
    p2_name = player2_name if player2_name else opponent.display_name

    # Defer interaction
    await interaction.response.defer()

    # Tạo embed bắt đầu battle
    start_embed = discord.Embed(
        title="⚔️ BATTLE BẮT ĐẦU ⚔️",
        description=f"**{p1_name}** vs **{p2_name}**\n\n"
                   f"💚 Mỗi người có **30 HP**\n"
                   f"⚔️ Chọn hành động để tấn công đối thủ!\n\n"
                   f"📋 **Các hành động:**\n"
                   f"⚔️ Đánh nhẹ: 2d4 (2-8 sát thương)\n"
                   f"🗡️ Đánh trung bình: 1d8 (1-8 sát thương)\n"
                   f"💥 Đánh mạnh: 1d12 (1-12 sát thương) + tự nhận 1d4 (1-4 sát thương)",
        color=discord.Color.red()
    )

    message = await interaction.followup.send(embed=start_embed)

    # Tạo battle view
    battle_view = BattleView(interaction.user, opponent, p1_name, p2_name)
    battle_view.message = message

    # Bắt đầu lượt đầu tiên
    await battle_view.send_action_buttons()


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
