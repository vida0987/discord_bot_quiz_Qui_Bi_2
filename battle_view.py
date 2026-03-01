import discord
import random
from collections import Counter

# Fallback khi không dùng custom emoji
DICE_SYMBOLS = ["⚀", "⚁", "⚂", "⚃", "⚄", "⚅"]

# Custom Discord emoji cho 6 mặt súc sắc (1–6). Format: (tên_emoji, id_số).
# Lấy ID: Server Settings > Emoji > bấm emoji, hoặc gõ \:tên: trong chat để xem ID.
# Để id=None hoặc 0 thì dùng ký hiệu Unicode phía trên.
DICE_EMOJIS = [
    ("emoji_271", None),  # mặt 1
    ("emoji_272", None),  # mặt 2
    ("emoji_273", None),  # mặt 3
    ("emoji_274", None),  # mặt 4
    ("emoji_275", None),  # mặt 5
    ("emoji_276", None),  # mặt 6
]


def _dice_display(d):
    """Chuỗi hiển thị 1 mặt súc sắc (embed / tin nhắn). d = 1..6."""
    if d < 1 or d > 6:
        return DICE_SYMBOLS[0]
    name, eid = DICE_EMOJIS[d - 1]
    if eid:
        return f"<:{name}:{eid}>"
    return DICE_SYMBOLS[d - 1]


def _dice_button_emoji(d):
    """Trả về emoji cho Button (custom hoặc None để dùng label Unicode). d = 1..6."""
    if d < 1 or d > 6:
        return None
    name, eid = DICE_EMOJIS[d - 1]
    if eid:
        return discord.PartialEmoji(name=name, id=int(eid))
    return None


# 6 mặt: 1=gây 1, 2=gây 2, 3=nhận 1 tinh thần, 4=hồi 1 máu, 5=mất 1 máu+khóa, 6=bỏ 1 tinh thần→gây 3
# Combo: 5 khác nhau → hồi 2 tinh thần. 3 giống nhau → gây thêm 3. Hết tinh thần → nhận 3 sát thương + mất lượt.
class BattleView(discord.ui.View):
    MAX_HP = 30
    MAX_SPIRIT = 5

    def __init__(self, player1, player2, player1_name, player2_name):
        super().__init__(timeout=90)
        self.player1 = player1
        self.player2 = player2
        self.player1_name = player1_name
        self.player2_name = player2_name
        self.player1_hp = self.MAX_HP
        self.player2_hp = self.MAX_HP
        self.player1_spirit = self.MAX_SPIRIT
        self.player2_spirit = self.MAX_SPIRIT
        self.player1_skip_turn = False
        self.player2_skip_turn = False
        self.current_turn = 1
        self.message = None

    def _current_player(self):
        return self.player1 if self.current_turn == 1 else self.player2

    def _current_name(self):
        return self.player1_name if self.current_turn == 1 else self.player2_name

    def _opponent_hp_attr(self):
        return "player2_hp" if self.current_turn == 1 else "player1_hp"

    def _current_hp_attr(self):
        return "player1_hp" if self.current_turn == 1 else "player2_hp"

    def _current_spirit_attr(self):
        return "player1_spirit" if self.current_turn == 1 else "player2_spirit"

    def _current_skip_attr(self):
        return "player1_skip_turn" if self.current_turn == 1 else "player2_skip_turn"

    async def send_turn(self):
        # Battle đã kết thúc (một bên hết máu) → không gửi thêm gì (tránh timeout/view cũ gọi send_turn)
        if self.player1_hp <= 0 or self.player2_hp <= 0:
            return
        # Nếu đang bị mất lượt (hết tinh thần trước đó)
        skip_attr = self._current_skip_attr()
        if getattr(self, skip_attr):
            setattr(self, skip_attr, False)
            hp_attr = self._current_hp_attr()
            cur_hp = getattr(self, hp_attr) - 3
            if cur_hp < 0:
                cur_hp = 0
            setattr(self, hp_attr, cur_hp)
            await self.message.channel.send(
                f"💀 **{self._current_name()}** hết tinh thần! Nhận **3** sát thương và mất lượt. "
                f"({self._current_name()} còn {cur_hp}/{self.MAX_HP} HP)"
            )
            if cur_hp <= 0:
                await self.end_battle()
                return
            self.current_turn = 2 if self.current_turn == 1 else 1
            await self.send_turn()
            return

        def _hp_spirit_text():
            return (
                f"💚 **{self.player1_name}:** {self.player1_hp}/{self.MAX_HP} HP | 🧠 {self.player1_spirit}/{self.MAX_SPIRIT} tinh thần\n"
                f"💚 **{self.player2_name}:** {self.player2_hp}/{self.MAX_HP} HP | 🧠 {self.player2_spirit}/{self.MAX_SPIRIT} tinh thần"
            )
        rules = (
            "**6 mặt:** 1=gây 1 | 2=gây 2 | 3=nhận 1 tinh thần | 4=hồi 1 máu | 5=mất 1 máu (khóa) | 6=bỏ 1 tinh thần→gây 3\n"
            "**Combo:** 5 khác nhau → hồi 2 tinh thần | 3 giống nhau → gây thêm 3. **Hết tinh thần** → nhận 3 sát thương + mất lượt."
        )
        embed = discord.Embed(
            title=f"⚔️ Lượt của **{self._current_name()}**",
            description=f"{_hp_spirit_text()}\n\n🎲 **Roll 5d6** → đổ lại tối đa 2 lần → bấm **Áp dụng**.\n\n{rules}",
            color=discord.Color.orange(),
        )
        embed.set_footer(text="⏰ 90 giây để thực hiện lượt")

        class RollStartView(discord.ui.View):
            def __init__(self, battle_view):
                super().__init__(timeout=90)
                self.battle_view = battle_view

            @discord.ui.button(label="🎲 Roll 5d6", style=discord.ButtonStyle.primary)
            async def roll_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
                if interaction.user != self.battle_view._current_player():
                    await interaction.response.send_message("❌ Không phải lượt của bạn!", ephemeral=True)
                    return
                dice = [random.randint(1, 6) for _ in range(5)]
                locked = {i for i in range(5) if dice[i] == 5}
                emb, view = _dice_embed_and_view(self.battle_view, dice, re_rolls_left=2, marked=set(), locked=locked)
                await interaction.response.edit_message(embed=emb, view=view)
                view.message = interaction.message

            async def on_timeout(self):
                if self.battle_view.player1_hp <= 0 or self.battle_view.player2_hp <= 0:
                    return
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

        def _hp_spirit_desc(bv):
            return (
                f"💚 **{bv.player1_name}:** {bv.player1_hp}/{bv.MAX_HP} HP | 🧠 {bv.player1_spirit}/{bv.MAX_SPIRIT} tinh thần\n"
                f"💚 **{bv.player2_name}:** {bv.player2_hp}/{bv.MAX_HP} HP | 🧠 {bv.player2_spirit}/{bv.MAX_SPIRIT} tinh thần"
            )

        def _dice_embed_and_view(bv, dice, re_rolls_left, marked, locked):
            dice_display = " ".join(_dice_display(d) for d in dice)
            desc = (
                f"{_hp_spirit_desc(bv)}\n\n"
                f"🎲 **5 súc sắc:** {dice_display}\n"
                f"🔄 Đổ lại còn: **{re_rolls_left}** lần. Mặt 5 (mất máu) bị khóa không đổ lại."
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
                def __init__(self, battle_view, dice_list, rerolls, marked_set, locked_set):
                    super().__init__(timeout=90)
                    self.battle_view = battle_view
                    self.dice = list(dice_list)
                    self.re_rolls_left = rerolls
                    self.marked = set(marked_set)
                    self.locked = set(locked_set)

                async def _refresh(self, interaction: discord.Interaction, new_dice=None, new_rerolls=None, new_marked=None, new_locked=None):
                    if new_dice is not None:
                        self.dice = new_dice
                    if new_rerolls is not None:
                        self.re_rolls_left = new_rerolls
                    if new_marked is not None:
                        self.marked = new_marked
                    if new_locked is not None:
                        self.locked = new_locked
                    emb2, view2 = _dice_embed_and_view(self.battle_view, self.dice, self.re_rolls_left, self.marked, self.locked)
                    await interaction.response.edit_message(embed=emb2, view=view2)
                    view2.message = interaction.message

                async def toggle_die(self, interaction: discord.Interaction, index: int):
                    if interaction.user != self.battle_view._current_player():
                        await interaction.response.send_message("❌ Không phải lượt của bạn!", ephemeral=True)
                        return
                    if index in self.locked:
                        await interaction.response.send_message("❌ Viên này (mặt 5) không thể đổ lại!", ephemeral=True)
                        return
                    if index in self.marked:
                        self.marked.discard(index)
                    else:
                        self.marked.add(index)
                    emb2, view2 = _dice_embed_and_view(self.battle_view, self.dice, self.re_rolls_left, self.marked, self.locked)
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
                        await interaction.response.send_message("❌ Chọn ít nhất 1 viên để đổ lại (bấm vào viên đó).", ephemeral=True)
                        return
                    new_dice = list(self.dice)
                    for i in self.marked:
                        new_dice[i] = random.randint(1, 6)
                    new_locked = self.locked | {i for i in self.marked if new_dice[i] == 5}
                    await self._refresh(interaction, new_dice=new_dice, new_rerolls=self.re_rolls_left - 1, new_marked=set(), new_locked=new_locked)

                async def apply_effects(self, interaction: discord.Interaction):
                    if interaction.user != self.battle_view._current_player():
                        await interaction.response.send_message("❌ Không phải lượt của bạn!", ephemeral=True)
                        return
                    bv = self.battle_view
                    dice = self.dice
                    cur_hp_attr = bv._current_hp_attr()
                    cur_spirit_attr = bv._current_spirit_attr()
                    opp_hp_attr = bv._opponent_hp_attr()
                    cur_skip_attr = bv._current_skip_attr()
                    cur_hp = getattr(bv, cur_hp_attr)
                    cur_spirit = getattr(bv, cur_spirit_attr)
                    opp_hp = getattr(bv, opp_hp_attr)
                    lines = []
                    for d in dice:
                        if d == 1:
                            opp_hp -= 1
                            lines.append("Mặt 1: gây 1 sát thương.")
                        elif d == 2:
                            opp_hp -= 2
                            lines.append("Mặt 2: gây 2 sát thương.")
                        elif d == 3:
                            cur_spirit -= 1
                            lines.append("Mặt 3: nhận 1 sát thương tinh thần.")
                        elif d == 4:
                            cur_hp = min(bv.MAX_HP, cur_hp + 1)
                            lines.append("Mặt 4: hồi 1 máu.")
                        elif d == 5:
                            cur_hp -= 1
                            lines.append("Mặt 5: mất 1 máu.")
                        elif d == 6:
                            if cur_spirit >= 1:
                                cur_spirit -= 1
                                opp_hp -= 3
                                lines.append("Mặt 6: bỏ 1 tinh thần → gây 3 sát thương.")
                            else:
                                lines.append("Mặt 6: không đủ tinh thần, không hiệu ứng.")
                    if cur_hp < 0:
                        cur_hp = 0
                    if cur_spirit < 0:
                        cur_spirit = 0
                    if opp_hp < 0:
                        opp_hp = 0
                    # Combo: 5 khác nhau → hồi 2 tinh thần
                    if len(set(dice)) == 5:
                        cur_spirit = min(bv.MAX_SPIRIT, cur_spirit + 2)
                        lines.append("**Combo 5 khác nhau:** hồi 2 tinh thần.")
                    # Combo: 3 giống nhau → gây thêm 3
                    counts = Counter(dice)
                    if max(counts.values()) >= 3:
                        opp_hp -= 3
                        lines.append("**Combo 3 giống nhau:** gây thêm 3 sát thương.")
                    if opp_hp < 0:
                        opp_hp = 0
                    setattr(bv, cur_hp_attr, cur_hp)
                    setattr(bv, cur_spirit_attr, cur_spirit)
                    setattr(bv, opp_hp_attr, opp_hp)
                    # Hết tinh thần → nhận 3 sát thương và mất lượt tiếp theo
                    if cur_spirit <= 0:
                        cur_hp = getattr(bv, cur_hp_attr) - 3
                        if cur_hp < 0:
                            cur_hp = 0
                        setattr(bv, cur_hp_attr, cur_hp)
                        setattr(bv, cur_skip_attr, True)
                        lines.append("**Hết tinh thần!** Nhận 3 sát thương và mất lượt tiếp theo.")
                    dice_display = " ".join(_dice_display(d) for d in dice)
                    result = "\n".join(lines)
                    await interaction.response.send_message(
                        f"🎲 **{bv._current_name()}** {dice_display}\n{result}\n\n"
                        f"💚 {bv.player1_name}: {bv.player1_hp}/{bv.MAX_HP} HP | 🧠 {bv.player1_spirit} tinh thần\n"
                        f"💚 {bv.player2_name}: {bv.player2_hp}/{bv.MAX_HP} HP | 🧠 {bv.player2_spirit} tinh thần",
                        ephemeral=False,
                    )
                    if getattr(bv, opp_hp_attr) <= 0 or getattr(bv, cur_hp_attr) <= 0:
                        await bv.end_battle()
                        return
                    bv.current_turn = 2 if bv.current_turn == 1 else 1
                    for item in self.children:
                        item.disabled = True
                    try:
                        await interaction.message.edit(view=self)
                    except Exception:
                        pass
                    await bv.send_turn()

                async def on_timeout(self):
                    if self.battle_view.player1_hp <= 0 or self.battle_view.player2_hp <= 0:
                        return
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

            view = DiceActionView(bv, dice, re_rolls_left, marked, locked)
            for i in range(5):
                d = dice[i]
                em = _dice_button_emoji(d)
                if em:
                    label = " ✓" if i in marked else "\u200b"
                else:
                    label = _dice_display(d) + (" ✓" if i in marked else "")
                btn = discord.ui.Button(
                    emoji=em if em else None,
                    label=label,
                    style=discord.ButtonStyle.secondary if i in marked else discord.ButtonStyle.primary,
                    custom_id=f"die_{i}",
                    disabled=(i in locked),
                )
                if i not in locked:
                    idx = i
                    btn.callback = lambda inter, i=idx: view.toggle_die(inter, i)
                view.add_item(btn)
            if re_rolls_left > 0:
                reroll_btn = discord.ui.Button(
                    label="🔄 Đổ lại (đã chọn)",
                    style=discord.ButtonStyle.primary,
                    custom_id="reroll",
                )
                reroll_btn.callback = view.do_reroll
                view.add_item(reroll_btn)
            apply_btn = discord.ui.Button(
                label="⚔️ Áp dụng",
                style=discord.ButtonStyle.danger,
                custom_id="deal",
            )
            apply_btn.callback = view.apply_effects
            view.add_item(apply_btn)
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
            value=f"💚 HP: {self.player1_hp}/{self.MAX_HP} | 🧠 Tinh thần: {self.player1_spirit}/{self.MAX_SPIRIT}",
            inline=True,
        )
        winner_embed.add_field(
            name=f"👤 {self.player2_name}",
            value=f"💚 HP: {self.player2_hp}/{self.MAX_HP} | 🧠 Tinh thần: {self.player2_spirit}/{self.MAX_SPIRIT}",
            inline=True,
        )
        await self.message.channel.send(embed=winner_embed)
        self.stop()
