import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Discord Bot Token
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')

# Bot configuration
BOT_PREFIX = '!'
MAX_QUESTIONS_PER_QUIZ = 20
DEFAULT_QUESTIONS = 10
QUESTION_TIMEOUT = 30  # seconds
