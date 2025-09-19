# 🤖 Discord Quiz Bot

Bot Discord để tổ chức quiz với 100 câu hỏi tiếng Việt về truyện "Lord of the Mysteries".

## ✨ Tính năng

- 🎯 Quiz với số câu hỏi tùy chọn (1-20 câu, mặc định 10 câu)
- ⏰ Thời gian 30 giây cho mỗi câu hỏi
- 🎨 Giao diện đẹp với Discord Embed
- 📊 Thống kê kết quả chi tiết
- 🎮 Tương tác bằng emoji reactions
- 🔄 Random câu hỏi mỗi lần chơi

## 🚀 Cài đặt

### 1. Yêu cầu hệ thống
- Python 3.8 trở lên
- Discord Bot Token

### 2. Cài đặt dependencies
```bash
pip install -r requirements.txt
```

### 3. Tạo Discord Bot

1. Truy cập [Discord Developer Portal](https://discord.com/developers/applications)
2. Tạo New Application
3. Vào tab "Bot" và tạo bot
4. Copy Bot Token
5. Vào tab "OAuth2" > "URL Generator"
6. Chọn scopes: `bot`, `applications.commands`
7. Chọn permissions: `Send Messages`, `Add Reactions`, `Use Slash Commands`
8. Copy URL và mời bot vào server

### 4. Cấu hình Bot Token

**Cách 1: Sử dụng file .env (Khuyến nghị)**
```bash
# Tạo file .env (copy từ env.example)
copy env.example .env

# Sau đó chỉnh sửa file .env và thay thế your_discord_bot_token_here bằng token thực
```

**Cách 2: Sử dụng biến môi trường**
```bash
# Windows
set DISCORD_TOKEN=your_discord_bot_token_here

# Linux/Mac
export DISCORD_TOKEN=your_discord_bot_token_here
```

**⚠️ QUAN TRỌNG:**
- **KHÔNG** commit file `.env` lên GitHub
- File `.env` đã được thêm vào `.gitignore` để bảo vệ
- Chỉ sử dụng `env.example` làm template

### 5. Chạy bot
```bash
python main.py
```

## 📋 Lệnh

| Lệnh | Mô tả | Ví dụ |
|------|-------|-------|
| `!quiz [số]` | Bắt đầu quiz với số câu hỏi tùy chọn | `!quiz 15` |
| `!ping` | Kiểm tra độ trễ của bot | `!ping` |
| `!help_quiz` | Hiển thị hướng dẫn sử dụng | `!help_quiz` |

## 🎮 Cách chơi

1. Sử dụng lệnh `!quiz` để bắt đầu
2. Click vào emoji 🇦 🇧 🇨 🇩 để chọn đáp án
3. Bạn có 30 giây cho mỗi câu hỏi
4. Xem kết quả cuối quiz!

## ⚙️ Cấu hình

Chỉnh sửa file `config.py` để thay đổi:

```python
BOT_PREFIX = '!'                    # Prefix lệnh
MAX_QUESTIONS_PER_QUIZ = 20         # Số câu hỏi tối đa
DEFAULT_QUESTIONS = 10              # Số câu hỏi mặc định
QUESTION_TIMEOUT = 30               # Thời gian mỗi câu (giây)
```

## 📁 Cấu trúc thư mục

```
bot_discord/
├── main.py              # File chính của bot
├── questions.json       # Database câu hỏi
├── config.py           # Cấu hình bot
├── keep_alive.py       # Giữ bot online
├── requirements.txt    # Dependencies
├── .env               # Token Discord (tạo thủ công)
└── README.md          # Hướng dẫn này
```

## 🔧 Troubleshooting

### Bot không khởi động
- Kiểm tra Discord Token có đúng không
- Đảm bảo đã cài đặt đầy đủ dependencies
- Kiểm tra file `questions.json` có tồn tại không

### Bot không phản hồi
- Kiểm tra bot có quyền gửi tin nhắn không
- Kiểm tra bot có online không
- Kiểm tra prefix lệnh có đúng không

### Lỗi import
```bash
pip install --upgrade discord.py python-dotenv
```

## 📝 Chỉnh sửa câu hỏi

Chỉnh sửa file `questions.json` để thêm/sửa/xóa câu hỏi:

```json
{
  "questions": [
    {
      "question": "Câu hỏi của bạn?",
      "options": {
        "A": "Đáp án A",
        "B": "Đáp án B", 
        "C": "Đáp án C",
        "D": "Đáp án D"
      },
      "correct_answer": "A"
    }
  ]
}
```

## 🤝 Đóng góp

Mọi đóng góp đều được chào đón! Hãy tạo issue hoặc pull request.

## 📄 License

MIT License - Xem file LICENSE để biết thêm chi tiết.
