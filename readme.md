<img src="logo.png" alt="Grammar Correction Bot Logo" width="250">

# 📝 Grammar Correction Telegram Bot

A Telegram bot that checks and corrects grammar with AI-powered fluency improvements.

## ✨ Features

- **✅ Grammar Correction** - Automatic grammar checking and correction
- **🎨 Multiple Fluency Styles** - Current, Formal, Friendly, and Scientific styles
- **🔍 Change Explanation** - Detailed explanations of corrections made
- **🔄 Reformulation** - Generate multiple variations of improved text
- **✉️ Email Subject Suggestions** - Generate subject lines in 3 styles (Short, Formal, Catchy)
- **🔒 User Authorization** - Controlled access with user limit management
- **📊 Admin Dashboard** - Usage statistics and user management

## 🚀 Quick Start

### Prerequisites

- Python 3.7+
- Telegram Bot Token from [@BotFather](https://t.me/botfather)
- OpenRouter API Key
- Your Telegram User ID from [@userinfobot](https://t.me/userinfobot)

### Installation

1. Clone and navigate to the repository:
   ```bash
   git clone https://github.com/Shkirskiy/grammar_checker.git
   cd grammar_checker
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure environment variables:
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and update:
   - `TELEGRAM_TOKEN` - Your bot token
   - `OPENROUTER_API_KEY` - Your API key
   - `MODEL_NAME` - LLM model (default: openai/chatgpt-4o-latest)
   - `ADMIN_ID` - Your Telegram user ID
   - `MAX_USERS` - Maximum allowed users (default: 10)
   - `GITHUB_REPO_URL` - Your repository URL

4. Run the bot:
   ```bash
   python bot.py
   ```

## 💬 Usage

Send any text message to the bot for grammar checking. After correction:
- **🔍 Explain Changes** - See what was modified
- **✨ Improve Fluency** - Choose a style:
  - 🔄 Current Style
  - 🎩 Formal Style
  - 😊 Friendly Style
  - 🔬 Scientific Style
- **🔄 Reformulate** - Generate alternative phrasings
- **✉️ Email Subjects** - Use `/subject` to generate 3 subject line options

### Commands

- `/start` - Start the bot
- `/help` - Show help message
- `/subject` - Generate email subject suggestions (Short, Formal, Catchy)
- `/admin_stats` - View statistics (admin only)

## 📁 Project Structure

```
grammar_checker/
├── bot.py                      # Main bot application
├── config.py                   # Configuration loader
├── message_handler.py          # Message processing & splitting
├── user_manager.py             # User authorization
├── requirements.txt            # Python dependencies
├── .env                        # Environment variables (not in git)
├── .env.example                # Environment template
├── .gitignore                  # Git exclusions
├── logo.png                    # Bot logo
├── users_data.json             # User data storage (auto-generated)
└── system_prompts/             # LLM prompts
    ├── grammar_correction.txt
    ├── change_explanation.txt
    ├── fluency_current.txt
    ├── fluency_formal.txt
    ├── fluency_friendly.txt
    ├── fluency_scientific.txt
    ├── email_subject_short.txt
    ├── email_subject_formal.txt
    └── email_subject_catchy.txt
```

**Note:** Auto-launch setup files (`.sh`, `.scpt`, `.app`) are excluded from git as they are machine-specific.

## 🔒 Security & Privacy

- API keys stored securely in `.env` (git-ignored)
- User authorization required for all interactions
- No conversation data persistence
- Memory-only session storage

## 🛠️ Customization

- **System Prompts**: Modify files in `system_prompts/` directory
- **Bot Settings**: Adjust values in `.env` file
- **Model Selection**: Change `MODEL_NAME` to use different LLM
- **User Limits**: Update `MAX_USERS` in `.env`

---

## 📄 License

This project is licensed under the **Creative Commons Attribution 4.0 International License (CC-BY 4.0)**.

You are free to:
- **Share** — copy and redistribute the material in any medium or format
- **Adapt** — remix, transform, and build upon the material for any purpose, even commercially

Under the following terms:
- **Attribution** — You must give appropriate credit, provide a link to the license, and indicate if changes were made.

For more details, see the [CC-BY 4.0 License](https://creativecommons.org/licenses/by/4.0/).
