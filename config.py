import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Discord Bot Token
DISCORD_TOKEN = 'MTQxNzE0MzYyMjQ5ODc4MzM0Mw.GBol5V.J_Mj5ROmKYX1E7X35WyU_NR2SAvxKAV8p88M18'

# Bot configuration
BOT_PREFIX = '!'
MAX_QUESTIONS_PER_QUIZ = 20
DEFAULT_QUESTIONS = 10
QUESTION_TIMEOUT = 30  # seconds
