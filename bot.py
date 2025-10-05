# grammarbot.py (bot.py) - Main Bot File
import os
import json
import logging
import asyncio
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import aiohttp
import html

from config import TELEGRAM_TOKEN, OPENROUTER_API_KEY, OPENROUTER_BASE_URL, ADMIN_ID, MAX_USERS, MODEL_NAME, MESSAGE_COMBINE_DELAY, MAX_MESSAGE_LENGTH, GITHUB_REPO_URL
from user_manager import UserManager
from message_handler import combine_messages, split_response

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Message queue for combining consecutive messages
message_queue = {}

def convert_markdown_to_html(text):
    """
    Convert common markdown syntax to HTML tags.
    This is a fallback if the LLM uses markdown despite our instructions.
    Note: Telegram only supports a limited set of HTML tags.
    """
    if text is None:
        return ""
        
    # Convert **text** to <b>text</b>
    text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
    
    # Convert _text_ or *text* to <i>text</i>
    text = re.sub(r'(?<!\\)_(.*?)(?<!\\)_', r'<i>\1</i>', text)
    text = re.sub(r'(?<!\*)\*(.*?)(?!\*)\*', r'<i>\1</i>', text)
    
    # Convert markdown-style line breaks (two spaces followed by newline) to just newline
    # Telegram doesn't support <br> tags, so we use newlines instead
    text = re.sub(r'  \n', r'\n', text)
    
    # Convert double newlines to just newlines (not <br><br> since Telegram doesn't support it)
    text = re.sub(r'\n\n', r'\n', text)
    
    # Remove any existing <br> tags and replace with newlines
    text = re.sub(r'<br\s*/?>', r'\n', text)
    
    return text

class GrammarBot:
    def __init__(self):
        # Initialize user manager with admin ID and max users from config
        self.user_manager = UserManager(ADMIN_ID, MAX_USERS)
        self.load_system_prompts()
        # Storage for conversation data
        self.conversation_data = {}
        
    def load_system_prompts(self):
        """Load all system prompts from files"""
        self.prompts = {}
        prompts_dir = 'system_prompts'
        
        for file_name in os.listdir(prompts_dir):
            if file_name.endswith('.txt'):
                prompt_name = os.path.splitext(file_name)[0]
                with open(os.path.join(prompts_dir, file_name), 'r', encoding='utf-8') as file:
                    self.prompts[prompt_name] = file.read().strip()
    
    async def send_to_llm(self, message, system_prompt):
        """Send message to LLM via OpenRouter API and return content with token usage"""
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": MODEL_NAME,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message}
            ]
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(OPENROUTER_BASE_URL, 
                                  headers=headers, json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    content = result["choices"][0]["message"]["content"]
                    tokens_used = result.get("usage", {}).get("total_tokens", 0)
                    return content, tokens_used
                else:
                    error_text = await response.text()
                    logger.error(f"LLM API error: {error_text}")
                    return f"Error: Unable to process request. Status code: {response.status}", 0
    
    # Command handlers
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user_id = update.effective_user.id
        
        # Check if user is authorized
        if self.user_manager.is_authorized(user_id):
            self.user_manager.update_last_activity(user_id)
        elif self.user_manager.can_accept_new_user():
            # Add new user
            self.user_manager.add_user(
                user_id=user_id,
                username=update.effective_user.username,
                first_name=update.effective_user.first_name
            )
        else:
            # User limit reached
            await update.message.reply_html(
                "⚠️ <b>User limit exceeded</b>\n\n"
                "This bot has reached its maximum capacity. "
                "Please wait until the administrator extends the user limit."
            )
            return
        
        await update.message.reply_html(
            f"👋 <b>Welcome, {update.effective_user.first_name}!</b>\n\n"
            "📝 I'm your Grammar Correction Bot - here to help you perfect your writing!\n\n"
            "<b>✨ What I can do:</b>\n"
            "• ✅ Check and correct grammar\n"
            "• 🎨 Improve fluency with multiple styles\n"
            "• 🔍 Explain what was changed\n"
            "• 🔄 Generate alternative phrasings\n\n"
            "Just send me any text and I'll take care of the rest!\n\n"
            "💡 Type /help for detailed instructions\n"
            f"🔗 <a href='{GITHUB_REPO_URL}'>GitHub Repository</a>"
        )
    
    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        user_id = update.effective_user.id
        
        # Check if user is authorized
        if self.user_manager.is_authorized(user_id):
            self.user_manager.update_last_activity(user_id)
        elif self.user_manager.can_accept_new_user():
            # Add new user
            self.user_manager.add_user(
                user_id=user_id,
                username=update.effective_user.username,
                first_name=update.effective_user.first_name
            )
        else:
            # User limit reached
            await update.message.reply_html(
                "⚠️ <b>User limit exceeded</b>\n\n"
                "This bot has reached its maximum capacity. "
                "Please wait until the administrator extends the user limit."
            )
            return
        
        help_text = (
            "📖 <b>Grammar Correction Bot - Help</b>\n\n"
            "⚙️ <b>Commands:</b>\n"
            "/start - Welcome message\n"
            "/help - Show this help message\n\n"
            "📝 <b>How to use:</b>\n"
            "1️⃣ Send any text message to check grammar\n"
            "2️⃣ After correction, you can:\n"
            "   • 🔍 <b>Explain Changes</b> - See what was modified\n"
            "   • ✨ <b>Improve Fluency</b> - Choose a style:\n"
            "      - 🔄 Current Style - Maintain original style\n"
            "      - 🎩 Formal Style - Professional tone\n"
            "      - 😊 Friendly Style - Casual and warm\n"
            "      - 🔬 Scientific Style - Academic tone\n"
            "   • 🔄 <b>Reformulate</b> - Generate alternatives\n\n"
            "💡 <b>Tips:</b>\n"
            "• Corrected text is copyable (tap and hold)\n"
            "• Navigate between reformulations with ◄ ►\n"
            f"• View source code: <a href='{GITHUB_REPO_URL}'>GitHub</a>"
        )
        
        if self.user_manager.is_admin(user_id):
            help_text += "\n\n🔐 <b>Admin Commands:</b>\n"
            help_text += "/admin_stats - View bot usage statistics"
        
        await update.message.reply_html(help_text)
    
    async def admin_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /admin_stats command - only for admin"""
        user_id = update.effective_user.id
        
        # Check if user is admin
        if not self.user_manager.is_admin(user_id):
            await update.message.reply_html(
                "⚠️ This command is only available to the bot administrator."
            )
            return
        
        # Get all users and statistics
        all_users = self.user_manager.get_all_users()
        user_count = self.user_manager.get_user_count()
        available_slots = MAX_USERS - user_count
        
        # Build statistics message
        stats_message = f"📊 <b>Bot Statistics</b>\n\n"
        stats_message += f"<b>Total Users:</b> {user_count}/{MAX_USERS}\n"
        stats_message += f"<b>Available Slots:</b> {available_slots}\n\n"
        
        if not all_users:
            stats_message += "<i>No registered users yet.</i>"
        else:
            stats_message += "👥 <b>Registered Users:</b>\n\n"
            
            # Sort users by join date (most recent first)
            sorted_users = sorted(
                all_users.items(),
                key=lambda x: x[1].get('joined_at', ''),
                reverse=True
            )
            
            for idx, (uid, user_data) in enumerate(sorted_users, 1):
                first_name = user_data.get('first_name', 'Unknown')
                username = user_data.get('username', None)
                joined_at = user_data.get('joined_at', 'Unknown')
                total_tokens = user_data.get('total_tokens', 0)
                last_activity = user_data.get('last_activity', 'Unknown')
                
                # Format dates for readability
                try:
                    from datetime import datetime
                    joined_dt = datetime.fromisoformat(joined_at)
                    joined_str = joined_dt.strftime('%b %d, %Y %H:%M')
                    
                    last_activity_dt = datetime.fromisoformat(last_activity)
                    last_activity_str = last_activity_dt.strftime('%b %d, %Y %H:%M')
                except:
                    joined_str = joined_at
                    last_activity_str = last_activity
                
                # Format username
                username_str = f"@{username}" if username else "No username"
                
                # Format token count with commas
                tokens_str = f"{total_tokens:,}"
                
                stats_message += f"<b>{idx}. {first_name}</b> ({username_str})\n"
                stats_message += f"   ID: <code>{uid}</code>\n"
                stats_message += f"   Joined: {joined_str}\n"
                stats_message += f"   Tokens: {tokens_str}\n"
                stats_message += f"   Last Activity: {last_activity_str}\n\n"
        
        # Send statistics (split if too long)
        if len(stats_message) > MAX_MESSAGE_LENGTH:
            parts = split_response(stats_message, MAX_MESSAGE_LENGTH)
            for part in parts:
                await update.message.reply_html(part)
        else:
            await update.message.reply_html(stats_message)
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle user messages for grammar checking"""
        user_id = update.effective_user.id
        
        # Check if user is authorized
        if self.user_manager.is_authorized(user_id):
            self.user_manager.update_last_activity(user_id)
        elif self.user_manager.can_accept_new_user():
            # Add new user
            self.user_manager.add_user(
                user_id=user_id,
                username=update.effective_user.username,
                first_name=update.effective_user.first_name
            )
        else:
            # User limit reached
            await update.message.reply_html(
                "⚠️ <b>User limit exceeded</b>\n\n"
                "This bot has reached its maximum capacity. "
                "Please wait until the administrator extends the user limit."
            )
            return
        
        message_text = update.message.text
        
        # Add message to queue for potential combining
        if user_id not in message_queue:
            message_queue[user_id] = []
        
        message_queue[user_id].append((message_text, update.message.message_id))
        
        # Set a delay to check for consecutive messages
        context.job_queue.run_once(
            self.process_message_queue, MESSAGE_COMBINE_DELAY, 
            data={"user_id": user_id, "chat_id": update.effective_chat.id}
        )
    
    async def process_message_queue(self, context: ContextTypes.DEFAULT_TYPE):
        """Process queued messages after delay"""
        data = context.job.data
        user_id = data["user_id"]
        chat_id = data["chat_id"]
        
        if user_id not in message_queue or not message_queue[user_id]:
            return
        
        # Get messages from queue
        messages = message_queue[user_id]
        message_queue[user_id] = []  # Clear queue
        
        # Combine messages if needed
        combined_text, original_ids = combine_messages(messages)
        
        if len(combined_text) > MAX_MESSAGE_LENGTH:
            # Message too long
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"The message is too long. Please send a shorter text (maximum {MAX_MESSAGE_LENGTH} characters).",
                reply_to_message_id=original_ids[0]
            )
            return
        
        # Send typing action
        await context.bot.send_chat_action(chat_id=chat_id, action="typing")
        
        try:
            # Process with LLM
            corrected_text, tokens_used = await self.send_to_llm(
                combined_text, 
                self.prompts['grammar_correction']
            )
            
            # Update user's token count
            self.user_manager.update_tokens(user_id, tokens_used)
            
            # Convert any markdown to HTML as a fallback
            corrected_text = convert_markdown_to_html(corrected_text)
            
            # Check if corrected text is too long
            plain_text = re.sub(r'<[^<]+?>', '', corrected_text)
            if len(plain_text) > MAX_MESSAGE_LENGTH:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text="The generated corrected message is too long. Telegram doesn't support messages of this length. Please try with shorter text.",
                    reply_to_message_id=original_ids[0]
                )
                return
            
            # Create inline keyboard
            keyboard = [
                [
                    InlineKeyboardButton("🔍 Explain Changes", callback_data=f"explain_{original_ids[0]}"),
                    InlineKeyboardButton("✨ Improve Fluency", callback_data=f"fluency_{original_ids[0]}")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Store original and corrected text in class-level storage
            data_key = f"message_{original_ids[0]}"
            self.conversation_data[data_key] = {
                "original": combined_text,
                "corrected": corrected_text,
                "selected_style": None,
                "fluency_versions": [],
                "current_version_index": 0
            }
            
            # Send copiable message with buttons
            copiable_text = f"<pre>{html.escape(plain_text)}</pre>"
            
            await context.bot.send_message(
                chat_id=chat_id,
                text=copiable_text,
                parse_mode='HTML',
                reply_markup=reply_markup,
                reply_to_message_id=original_ids[0]
            )
        except Exception as e:
            logger.error(f"Error in process_message_queue: {e}")
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"Sorry, an error occurred while processing your message: {str(e)}",
                reply_to_message_id=original_ids[0]
            )
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle callback queries from inline buttons"""
        query = update.callback_query
        await query.answer()
        
        data = query.data.split('_')
        action = data[0]
        message_id = data[1]
        
        if action == "explain":
            # Get original and corrected text from class storage
            data_key = f"message_{message_id}"
            original_text = self.conversation_data.get(data_key, {}).get("original", "")
            corrected_text = self.conversation_data.get(data_key, {}).get("corrected", "")
            
            if not original_text or not corrected_text:
                await query.edit_message_text(
                    text="Sorry, I couldn't find the original message. Please try again.",
                    parse_mode='HTML'
                )
                return
            
            # Send typing action
            await context.bot.send_chat_action(
                chat_id=update.effective_chat.id, 
                action="typing"
            )
            
            try:
                # Generate explanation
                explanation_prompt = self.prompts['change_explanation']
                explanation, tokens_used = await self.send_to_llm(
                    f"Original: {original_text}\nCorrected: {corrected_text}",
                    explanation_prompt
                )
                
                # Update user's token count
                user_id = update.effective_user.id
                self.user_manager.update_tokens(user_id, tokens_used)
                
                # Convert any markdown to HTML as a fallback
                explanation = convert_markdown_to_html(explanation)
                
                # Send explanation - NOT copiable, just the formatted version
                if len(explanation) > MAX_MESSAGE_LENGTH:
                    parts = split_response(explanation, MAX_MESSAGE_LENGTH)
                    for part in parts:
                        await context.bot.send_message(
                            chat_id=update.effective_chat.id,
                            text=part,
                            parse_mode='HTML',
                            reply_to_message_id=query.message.message_id
                        )
                else:
                    await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text=explanation,
                        parse_mode='HTML',
                        reply_to_message_id=query.message.message_id
                    )
            except Exception as e:
                logger.error(f"Error in explain callback: {e}")
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=f"Sorry, an error occurred while generating the explanation: {str(e)}",
                    reply_to_message_id=query.message.message_id
                )
                
        elif action == "fluency":
            # Show style options in a 2x2 grid with emojis
            keyboard = [
                [
                    InlineKeyboardButton("🔄 Current Style", callback_data=f"style_current_{message_id}"),
                    InlineKeyboardButton("🎩 Formal Style", callback_data=f"style_formal_{message_id}")
                ],
                [
                    InlineKeyboardButton("😊 Friendly Style", callback_data=f"style_friendly_{message_id}"),
                    InlineKeyboardButton("🔬 Scientific Style", callback_data=f"style_scientific_{message_id}")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_reply_markup(reply_markup=reply_markup)
            
        elif action == "copy":
            # Get corrected text from class storage
            data_key = f"message_{message_id}"
            corrected_text = self.conversation_data.get(data_key, {}).get("corrected", "")
            
            if not corrected_text:
                await query.edit_message_text(
                    text="Sorry, I couldn't find the original message. Please try again.",
                    parse_mode='HTML'
                )
                return
            
            # Remove any HTML tags to make it plain text for copying
            plain_text = re.sub(r'<[^<]+?>', '', corrected_text)
            
            # Send the text in a pre tag for easy copying
            copiable_text = f"<pre>{html.escape(plain_text)}</pre>"
            
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=copiable_text,
                parse_mode='HTML',
                reply_to_message_id=query.message.message_id
            )
            
        elif action == "style":
            style = data[1]
            message_id = data[2]
            
            # Get corrected text from class storage
            data_key = f"message_{message_id}"
            corrected_text = self.conversation_data.get(data_key, {}).get("corrected", "")
            
            if not corrected_text:
                await query.edit_message_text(
                    text="Sorry, I couldn't find the original message. Please try again.",
                    parse_mode='HTML'
                )
                return
            
            # Send typing action
            await context.bot.send_chat_action(
                chat_id=update.effective_chat.id, 
                action="typing"
            )
            
            try:
                # Select appropriate prompt based on style
                if style == "current":
                    fluency_prompt = self.prompts['fluency_current']
                elif style == "formal":
                    fluency_prompt = self.prompts['fluency_formal']
                elif style == "friendly":
                    fluency_prompt = self.prompts['fluency_friendly']
                else:  # scientific
                    fluency_prompt = self.prompts['fluency_scientific']
                
                # Generate improved text
                improved_text, tokens_used = await self.send_to_llm(corrected_text, fluency_prompt)
                
                # Update user's token count
                user_id = update.effective_user.id
                self.user_manager.update_tokens(user_id, tokens_used)
                
                # Convert any markdown to HTML as a fallback
                improved_text = convert_markdown_to_html(improved_text)
                
                # Check if improved text is too long
                plain_text = re.sub(r'<[^<]+?>', '', improved_text)
                if len(plain_text) > MAX_MESSAGE_LENGTH:
                    await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text="The generated improved message is too long. Telegram doesn't support messages of this length. Please try with shorter text.",
                        reply_to_message_id=query.message.message_id
                    )
                    return
                
                # Store the style and first version
                self.conversation_data[data_key]["selected_style"] = style
                self.conversation_data[data_key]["fluency_versions"] = [improved_text]
                self.conversation_data[data_key]["current_version_index"] = 0
                
                # Create keyboard with Reformulate button
                keyboard = [
                    [InlineKeyboardButton("🔄 Reformulate", callback_data=f"reformulate_{message_id}")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                # Send copiable message with Reformulate button
                copiable_text = f"<pre>{html.escape(plain_text)}</pre>"
                
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=copiable_text,
                    parse_mode='HTML',
                    reply_markup=reply_markup,
                    reply_to_message_id=query.message.message_id
                )
            except Exception as e:
                logger.error(f"Error in style callback: {e}")
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=f"Sorry, an error occurred while improving fluency: {str(e)}",
                    reply_to_message_id=query.message.message_id
                )
                
        elif action == "reformulate":
            # Get data from storage
            data_key = f"message_{message_id}"
            conv_data = self.conversation_data.get(data_key, {})
            original_text = conv_data.get("original", "")
            selected_style = conv_data.get("selected_style", "")
            fluency_versions = conv_data.get("fluency_versions", [])
            
            if not original_text or not fluency_versions:
                await query.edit_message_text(
                    text="Sorry, I couldn't find the original message. Please try again.",
                    parse_mode='HTML'
                )
                return
            
            # Send typing action
            await context.bot.send_chat_action(
                chat_id=update.effective_chat.id, 
                action="typing"
            )
            
            try:
                # Select appropriate prompt based on style
                if selected_style == "current":
                    fluency_prompt = self.prompts['fluency_current']
                elif selected_style == "formal":
                    fluency_prompt = self.prompts['fluency_formal']
                elif selected_style == "friendly":
                    fluency_prompt = self.prompts['fluency_friendly']
                else:  # scientific
                    fluency_prompt = self.prompts['fluency_scientific']
                
                # Build reformulation prompt with all previous versions
                reformulation_context = f"Original text: {original_text}\n\n"
                reformulation_context += "Previous formulations:\n"
                for i, version in enumerate(fluency_versions, 1):
                    reformulation_context += f"Version {i}: {version}\n\n"
                reformulation_context += "Please provide a NEW formulation that maintains the same style and tone but uses different wording. Do not repeat any of the previous versions."
                
                # Generate new reformulation
                new_version, tokens_used = await self.send_to_llm(reformulation_context, fluency_prompt)
                
                # Update user's token count
                user_id = update.effective_user.id
                self.user_manager.update_tokens(user_id, tokens_used)
                
                # Convert any markdown to HTML as a fallback
                new_version = convert_markdown_to_html(new_version)
                
                # Check if reformulated text is too long
                plain_text = re.sub(r'<[^<]+?>', '', new_version)
                if len(plain_text) > MAX_MESSAGE_LENGTH:
                    await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text="The generated reformulated message is too long. Telegram doesn't support messages of this length. Please try with shorter text.",
                        reply_to_message_id=query.message.message_id
                    )
                    return
                
                # Add new version to storage
                fluency_versions.append(new_version)
                self.conversation_data[data_key]["fluency_versions"] = fluency_versions
                self.conversation_data[data_key]["current_version_index"] = len(fluency_versions) - 1
                
                # Create keyboard with Reformulate and navigation buttons
                keyboard = [
                    [InlineKeyboardButton("🔄 Reformulate", callback_data=f"reformulate_{message_id}")],
                    [
                        InlineKeyboardButton("◄", callback_data=f"nav_prev_{message_id}"),
                        InlineKeyboardButton(f"{len(fluency_versions)}/{len(fluency_versions)}", callback_data="noop"),
                        InlineKeyboardButton("►", callback_data=f"nav_next_{message_id}")
                    ]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                # Edit the existing message with the new version
                copiable_text = f"<pre>{html.escape(plain_text)}</pre>"
                
                await query.edit_message_text(
                    text=copiable_text,
                    parse_mode='HTML',
                    reply_markup=reply_markup
                )
            except Exception as e:
                logger.error(f"Error in reformulate callback: {e}")
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=f"Sorry, an error occurred while reformulating: {str(e)}",
                    reply_to_message_id=query.message.message_id
                )
                
        elif action == "nav":
            direction = data[1]
            message_id = data[2]
            
            # Get data from storage
            data_key = f"message_{message_id}"
            conv_data = self.conversation_data.get(data_key, {})
            fluency_versions = conv_data.get("fluency_versions", [])
            current_index = conv_data.get("current_version_index", 0)
            
            if not fluency_versions:
                await query.answer("No versions available!")
                return
            
            # Update index based on direction
            if direction == "prev":
                new_index = max(0, current_index - 1)
            else:  # next
                new_index = min(len(fluency_versions) - 1, current_index + 1)
            
            # If index didn't change, just answer the callback
            if new_index == current_index:
                await query.answer()
                return
            
            # Update stored index
            self.conversation_data[data_key]["current_version_index"] = new_index
            
            # Get the version to display
            version_text = fluency_versions[new_index]
            
            # Create keyboard with Reformulate and navigation buttons
            keyboard = [
                [InlineKeyboardButton("🔄 Reformulate", callback_data=f"reformulate_{message_id}")],
                [
                    InlineKeyboardButton("◄", callback_data=f"nav_prev_{message_id}"),
                    InlineKeyboardButton(f"{new_index + 1}/{len(fluency_versions)}", callback_data="noop"),
                    InlineKeyboardButton("►", callback_data=f"nav_next_{message_id}")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Update the message with the new version
            try:
                plain_text = re.sub(r'<[^<]+?>', '', version_text)
                copiable_text = f"<pre>{html.escape(plain_text)}</pre>"
                
                await query.edit_message_text(
                    text=copiable_text,
                    parse_mode='HTML',
                    reply_markup=reply_markup
                )
            except Exception as e:
                logger.error(f"Error in navigation callback: {e}")
                await query.answer("Failed to navigate to version")

async def error_handler(update, context):
    """Log the error and send a message to the user."""
    logger.error(f"Exception while handling an update: {context.error}")
    
    # Send message to the user if possible
    if update and update.effective_chat:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Sorry, something went wrong. The error has been logged and will be addressed soon."
        )

def main():
    """Start the bot"""
    # Create the Application
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    bot = GrammarBot()
    
    # Add command handlers
    application.add_handler(CommandHandler("start", bot.start))
    application.add_handler(CommandHandler("help", bot.help))
    application.add_handler(CommandHandler("admin_stats", bot.admin_stats))
    
    # Add message handler
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_message))
    
    # Add callback query handler
    application.add_handler(CallbackQueryHandler(bot.handle_callback))
    
    # Add error handler
    application.add_error_handler(error_handler)
    
    # Start the Bot
    application.run_polling()

if __name__ == '__main__':
    main()
