import discord
import random


# Battle: turn-based, mỗi lượt roll 6d6, được đổ lại (chọn viên) tối đa 2 lần, tổng = sát thương
class BattleView(discord.ui.View):
    def __init__(self, player1, player2, player1_name, player2_name):
        super().__init__(timeout=90)
        self.player1 = player1
        self.player2 = player2
        self.player1_name = player1_name
        self.player2_name = player2_name
        self.player1_hp = 30
        self.player2_hp = 30
        self.current_turn = 1
        self.message = None

    def _current_player(self):
        return self.player1 if self.current_turn == 1 else self.player2

    def _current_name(self):
        return self.player1_name if self.current_turn == 1 else self.player2_name

    def _opponent_hp_attr(self):
        return "player2_hp" if self.current_turn == 1 else "player1_hp"

    async def send_turn(self):
        embed = discord.Embed(
            title=f"⚔️ Lượt của **{self._current_name()}**",
            description=f"💚 **{self.player1_name}:** {self.player1_hp}/30 HP\n"
                       f"💚 **{self.player2_name}:** {self.player2_hp}/30 HP\n\n"
                       f"🎲 Bấm **Roll 6d6** → được đổ lại viên tùy chọn **tối đa 2 lần**, tổng = sát thương.",
            color=discord.Color.orange(),
        )
        embed.set_footer(text="⏰ 90 giây để thực hiện lượt")

        class RollStartView(discord.ui.View):
            def __init__(self, battle_view):
                super().__init__(timeout=90)
                self.battle_view = battle_view

            @discord.ui.button(label="🎲 Roll 6d6", style=discord.ButtonStyle.primary)
            async def roll_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
                if interaction.user != self.battle_view._current_player():
                    await interaction.response.send_message("❌ Không phải lượt của bạn!", ephemeral=True)
                    return
                dice = [random.randint(1, 6) for _ in range(6)]
                emb, view = _dice_embed_and_view(self.battle_view, dice, re_rolls_left=2, marked=set())
                await interaction.response.edit_message(embed=emb, view=view)
                view.message = interaction.message

            async def on_timeout(self):
                for item in self.children:
                    item.disabled = True
                try:
                    await self.message.edit(view=self)
                except Exception:
                    pass
                await self.battle_view.message.channel.send(
                    f"⏰ **{self.battle_view._current_name()}** hết thời gian, mất lượt!"
                )
                self.battle_view.current_turn = 2 if self.battle_view.current_turn == 1 else 1
                await self.battle_view.send_turn()

        def _dice_embed_and_view(bv, dice, re_rolls_left, marked):
            total = sum(dice)
            desc = (
                f"💚 **{bv.player1_name}:** {bv.player1_hp}/30 HP\n"
                f"💚 **{bv.player2_name}:** {bv.player2_hp}/30 HP\n\n"
                f"🎲 **6 súc sắc:** {' | '.join(str(d) for d in dice)} → **Tổng = {total}** sát thương\n"
                f"🔄 Đổ lại còn: **{re_rolls_left}** lần. Chọn viên (bấm nút) rồi bấm **Đổ lại**."
            )
            if marked:
                desc += f"\nĐã chọn đổ lại: viên số {', '.join(str(i+1) for i in sorted(marked))}."
            emb = discord.Embed(
                title=f"⚔️ Lượt của **{bv._current_name()}**",
                description=desc,
                color=discord.Color.orange(),
            )
            emb.set_footer(text="⏰ 90 giây")

            class DiceActionView(discord.ui.View):
                def __init__(self, battle_view, dice_list, rerolls, marked_set):
                    super().__init__(timeout=90)
                    self.battle_view = battle_view
                    self.dice = list(dice_list)
                    self.re_rolls_left = rerolls
                    self.marked = set(marked_set)

                async def _refresh(self, interaction: discord.Interaction, new_dice=None, new_rerolls=None, new_marked=None):
                    if new_dice is not None:
                        self.dice = new_dice
                    if new_rerolls is not None:
                        self.re_rolls_left = new_rerolls
                    if new_marked is not None:
                        self.marked = new_marked
                    emb2, view2 = _dice_embed_and_view(self.battle_view, self.dice, self.re_rolls_left, self.marked)
                    await interaction.response.edit_message(embed=emb2, view=view2)
                    view2.message = interaction.message

                async def toggle_die(self, interaction: discord.Interaction, index: int):
                    if interaction.user != self.battle_view._current_player():
                        await interaction.response.send_message("❌ Không phải lượt của bạn!", ephemeral=True)
                        return
                    if index in self.marked:
                        self.marked.discard(index)
                    else:
                        self.marked.add(index)
                    emb2, view2 = _dice_embed_and_view(self.battle_view, self.dice, self.re_rolls_left, self.marked)
                    await interaction.response.edit_message(embed=emb2, view=view2)
                    view2.message = interaction.message

                async def do_reroll(self, interaction: discord.Interaction):
                    if interaction.user != self.battle_view._current_player():
                        await interaction.response.send_message("❌ Không phải lượt của bạn!", ephemeral=True)
                        return
                    if self.re_rolls_left <= 0:
                        await interaction.response.send_message("❌ Đã hết 2 lần đổ lại!", ephemeral=True)
                        return
                    if not self.marked:
                        await interaction.response.send_message("❌ Chọn ít nhất 1 viên để đổ lại (bấm vào số viên đó).", ephemeral=True)
                        return
                    new_dice = list(self.dice)
                    for i in self.marked:
                        new_dice[i] = random.randint(1, 6)
                    await self._refresh(interaction, new_dice=new_dice, new_rerolls=self.re_rolls_left - 1, new_marked=set())

                async def do_damage(self, interaction: discord.Interaction):
                    if interaction.user != self.battle_view._current_player():
                        await interaction.response.send_message("❌ Không phải lượt của bạn!", ephemeral=True)
                        return
                    total = sum(self.dice)
                    opp_attr = self.battle_view._opponent_hp_attr()
                    current = getattr(self.battle_view, opp_attr) - total
                    if current < 0:
                        current = 0
                    setattr(self.battle_view, opp_attr, current)
                    opp_name = self.battle_view.player2_name if self.battle_view.current_turn == 1 else self.battle_view.player1_name
                    await interaction.response.send_message(
                        f"🎲 **{self.battle_view._current_name()}** 6d6 = **{self.dice}** → Tổng **{total}** sát thương! "
                        f"**{opp_name}** còn {current}/30 HP.",
                        ephemeral=False,
                    )
                    if getattr(self.battle_view, opp_attr) <= 0:
                        await self.battle_view.end_battle()
                        return
                    self.battle_view.current_turn = 2 if self.battle_view.current_turn == 1 else 1
                    for item in self.children:
                        item.disabled = True
                    try:
                        await interaction.message.edit(view=self)
                    except Exception:
                        pass
                    await self.battle_view.send_turn()

                async def on_timeout(self):
                    for item in self.children:
                        item.disabled = True
                    try:
                        await self.message.edit(view=self)
                    except Exception:
                        pass
                    await self.battle_view.message.channel.send(
                        f"⏰ **{self.battle_view._current_name()}** hết thời gian, mất lượt!"
                    )
                    self.battle_view.current_turn = 2 if self.battle_view.current_turn == 1 else 1
                    await self.battle_view.send_turn()

            view = DiceActionView(bv, dice, re_rolls_left, marked)
            for i in range(6):
                label = f"🎲 {dice[i]}"
                if i in marked:
                    label += " ✓"
                btn = discord.ui.Button(
                    label=label,
                    style=discord.ButtonStyle.secondary if i in marked else discord.ButtonStyle.primary,
                    custom_id=f"die_{i}",
                )
                idx = i
                btn.callback = lambda inter, i=idx: view.toggle_die(inter, i)
                view.add_item(btn)
            reroll_btn = discord.ui.Button(
                label="🔄 Đổ lại (đã chọn)",
                style=discord.ButtonStyle.primary,
                custom_id="reroll",
            )
            reroll_btn.callback = view.do_reroll
            view.add_item(reroll_btn)
            deal_btn = discord.ui.Button(
                label="⚔️ Gây sát thương",
                style=discord.ButtonStyle.danger,
                custom_id="deal",
            )
            deal_btn.callback = view.do_damage
            view.add_item(deal_btn)
            return emb, view

        roll_view = RollStartView(self)
        roll_view.message = await self.message.channel.send(embed=embed, view=roll_view)

    async def end_battle(self):
        winner_embed = discord.Embed(
            title="🏆 KẾT QUẢ BATTLE 🏆",
            color=discord.Color.gold(),
        )
        if self.player1_hp <= 0 and self.player2_hp <= 0:
            winner_embed.description = "🤝 Hòa! Cả 2 đều hết máu! 🤝"
            winner_embed.color = discord.Color.blue()
        elif self.player1_hp <= 0:
            winner_embed.description = f"🎉 **{self.player2_name}** thắng! 🎉"
            winner_embed.color = discord.Color.green()
        else:
            winner_embed.description = f"🎉 **{self.player1_name}** thắng! 🎉"
            winner_embed.color = discord.Color.green()
        winner_embed.add_field(
            name=f"👤 {self.player1_name}",
            value=f"💚 HP: {self.player1_hp}/30",
            inline=True,
        )
        winner_embed.add_field(
            name=f"👤 {self.player2_name}",
            value=f"💚 HP: {self.player2_hp}/30",
            inline=True,
        )
        await self.message.channel.send(embed=winner_embed)
        self.stop()
