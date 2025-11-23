import discord
import random


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
        damage1 = 0
        if self.player1_action == "dodge":
            # Né: tự mất 1 HP, không gây sát thương
            self.player1_hp -= 1
            action1_text = "Né (tự mất 1 HP, né được đòn tấn công)"
            if self.player1_hp < 0:
                self.player1_hp = 0
        elif self.player1_action == "heal":
            # Hồi máu: hồi 1d6 HP
            heal1 = random.randint(1, 6)
            old_hp = self.player1_hp
            self.player1_hp += heal1
            if self.player1_hp > 30:
                self.player1_hp = 30
            actual_heal = self.player1_hp - old_hp
            action1_text = f"Hồi máu (1d6 = {heal1}, hồi được {actual_heal} HP)"
        elif self.player1_action == "block":
            # Đỡ: chặn đánh nhẹ và trung bình, phản lại 1d4
            action1_text = "Đỡ (chặn đánh nhẹ/trung bình, phản lại 1d4)"
        elif self.player1_action == "light":
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
        damage2 = 0
        if self.player2_action == "dodge":
            # Né: tự mất 1 HP, không gây sát thương
            self.player2_hp -= 1
            action2_text = "Né (tự mất 1 HP, né được đòn tấn công)"
            if self.player2_hp < 0:
                self.player2_hp = 0
        elif self.player2_action == "heal":
            # Hồi máu: hồi 1d6 HP
            heal2 = random.randint(1, 6)
            old_hp = self.player2_hp
            self.player2_hp += heal2
            if self.player2_hp > 30:
                self.player2_hp = 30
            actual_heal = self.player2_hp - old_hp
            action2_text = f"Hồi máu (1d6 = {heal2}, hồi được {actual_heal} HP)"
        elif self.player2_action == "block":
            # Đỡ: chặn đánh nhẹ và trung bình, phản lại 1d4
            action2_text = "Đỡ (chặn đánh nhẹ/trung bình, phản lại 1d4)"
        elif self.player2_action == "light":
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

        # Áp dụng sát thương với xử lý né, đỡ và hồi máu
        dodge_info = ""
        block_info = ""
        
        # Xử lý sát thương từ player1 đến player2
        if self.player1_action != "heal" and self.player1_action != "block":
            if self.player2_action == "dodge":
                dodge_info += f"\n🛡️ **{self.player2_name}** đã né được đòn tấn công của **{self.player1_name}**!\n"
            elif self.player2_action == "block":
                # Đỡ: chặn đánh nhẹ và trung bình, không chặn đánh mạnh
                if self.player1_action in ["light", "medium"]:
                    # Chặn được, phản lại 1d4
                    counter_damage = random.randint(1, 4)
                    self.player1_hp -= counter_damage
                    block_info += f"\n🛡️ **{self.player2_name}** đã đỡ được đòn tấn công của **{self.player1_name}** và phản lại {counter_damage} sát thương!\n"
                    if self.player1_hp < 0:
                        self.player1_hp = 0
                else:
                    # Đánh mạnh không bị chặn
                    self.player2_hp -= damage1
                    block_info += f"\n💥 **{self.player1_name}** đánh mạnh xuyên qua đỡ của **{self.player2_name}**!\n"
            else:
                # Không né, không đỡ
                self.player2_hp -= damage1
        
        # Xử lý sát thương từ player2 đến player1
        if self.player2_action != "heal" and self.player2_action != "block":
            if self.player1_action == "dodge":
                dodge_info += f"🛡️ **{self.player1_name}** đã né được đòn tấn công của **{self.player2_name}**!\n"
            elif self.player1_action == "block":
                # Đỡ: chặn đánh nhẹ và trung bình, không chặn đánh mạnh
                if self.player2_action in ["light", "medium"]:
                    # Chặn được, phản lại 1d4
                    counter_damage = random.randint(1, 4)
                    self.player2_hp -= counter_damage
                    block_info += f"🛡️ **{self.player1_name}** đã đỡ được đòn tấn công của **{self.player2_name}** và phản lại {counter_damage} sát thương!\n"
                    if self.player2_hp < 0:
                        self.player2_hp = 0
                else:
                    # Đánh mạnh không bị chặn
                    self.player1_hp -= damage2
                    block_info += f"💥 **{self.player2_name}** đánh mạnh xuyên qua đỡ của **{self.player1_name}**!\n"
            else:
                # Không né, không đỡ
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
        if dodge_info:
            round_embed.add_field(
                name="🛡️ Thông tin né:",
                value=dodge_info.strip(),
                inline=False
            )
        if block_info:
            round_embed.add_field(
                name="🛡️ Thông tin đỡ:",
                value=block_info.strip(),
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
                  "💥 **Đánh mạnh:** 1d12 (1-12 sát thương) + tự nhận 1d4 (1-4 sát thương)\n"
                  "🛡️ **Né:** Tự mất 1 HP, né được đòn tấn công của đối thủ\n"
                  "🛡️ **Đỡ:** Chặn đánh nhẹ/trung bình, phản lại 1d4 (không chặn đánh mạnh)\n"
                  "💚 **Hồi máu:** Hồi 1d6 HP cho bản thân",
            inline=False
        )
        embed.set_footer(text="⏰ Bạn có 10 giây để chọn, nếu không sẽ tự động chọn Đánh nhẹ")

        # Tạo custom View class để xử lý timeout
        class ActionView(discord.ui.View):
            def __init__(self, battle_view):
                super().__init__(timeout=10)
                self.battle_view = battle_view
            
            async def on_timeout(self):
                # Tự động chọn "đánh nhẹ" cho người chơi chưa chọn
                auto_selected = []
                if self.battle_view.player1_action is None:
                    self.battle_view.player1_action = "light"
                    auto_selected.append(self.battle_view.player1_name)
                if self.battle_view.player2_action is None:
                    self.battle_view.player2_action = "light"
                    auto_selected.append(self.battle_view.player2_name)
                
                # Disable buttons
                for item in self.children:
                    item.disabled = True
                
                # Edit message để disable buttons
                if hasattr(self.battle_view, 'action_message') and self.battle_view.action_message:
                    try:
                        await self.battle_view.action_message.edit(view=self)
                    except:
                        pass
                
                # Thông báo nếu có người chơi tự động chọn
                if auto_selected:
                    timeout_msg = f"⏰ Hết thời gian! Tự động chọn **Đánh nhẹ** cho: {', '.join(auto_selected)}"
                    await self.battle_view.message.channel.send(timeout_msg)
                
                # Kiểm tra nếu cả 2 đã chọn thì thực hiện lượt đánh
                await self.battle_view.check_both_ready()

        view = ActionView(self)
        
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

        async def dodge_callback(interaction: discord.Interaction):
            if interaction.user == self.player1 and self.player1_action is None:
                self.player1_action = "dodge"
                await interaction.response.send_message("✅ Bạn đã chọn **Né** (tự mất 1 HP, né được đòn tấn công)", ephemeral=True)
            elif interaction.user == self.player2 and self.player2_action is None:
                self.player2_action = "dodge"
                await interaction.response.send_message("✅ Bạn đã chọn **Né** (tự mất 1 HP, né được đòn tấn công)", ephemeral=True)
            else:
                if interaction.user not in [self.player1, self.player2]:
                    await interaction.response.send_message("❌ Bạn không phải người chơi trong battle này!", ephemeral=True)
                else:
                    await interaction.response.send_message("❌ Bạn đã chọn hành động rồi!", ephemeral=True)
                return
            
            await self.check_both_ready()

        async def heal_callback(interaction: discord.Interaction):
            if interaction.user == self.player1 and self.player1_action is None:
                self.player1_action = "heal"
                await interaction.response.send_message("✅ Bạn đã chọn **Hồi máu** (1d6 HP)", ephemeral=True)
            elif interaction.user == self.player2 and self.player2_action is None:
                self.player2_action = "heal"
                await interaction.response.send_message("✅ Bạn đã chọn **Hồi máu** (1d6 HP)", ephemeral=True)
            else:
                if interaction.user not in [self.player1, self.player2]:
                    await interaction.response.send_message("❌ Bạn không phải người chơi trong battle này!", ephemeral=True)
                else:
                    await interaction.response.send_message("❌ Bạn đã chọn hành động rồi!", ephemeral=True)
                return
            
            await self.check_both_ready()

        async def block_callback(interaction: discord.Interaction):
            if interaction.user == self.player1 and self.player1_action is None:
                self.player1_action = "block"
                await interaction.response.send_message("✅ Bạn đã chọn **Đỡ** (chặn đánh nhẹ/trung bình, phản lại 1d4)", ephemeral=True)
            elif interaction.user == self.player2 and self.player2_action is None:
                self.player2_action = "block"
                await interaction.response.send_message("✅ Bạn đã chọn **Đỡ** (chặn đánh nhẹ/trung bình, phản lại 1d4)", ephemeral=True)
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

        dodge_btn = discord.ui.Button(label="🛡️ Né (tự mất 1 HP)", style=discord.ButtonStyle.secondary)
        dodge_btn.callback = dodge_callback
        view.add_item(dodge_btn)

        block_btn = discord.ui.Button(label="🛡️ Đỡ (phản lại 1d4)", style=discord.ButtonStyle.secondary)
        block_btn.callback = block_callback
        view.add_item(block_btn)

        heal_btn = discord.ui.Button(label="💚 Hồi máu (1d6)", style=discord.ButtonStyle.primary)
        heal_btn.callback = heal_callback
        view.add_item(heal_btn)

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

