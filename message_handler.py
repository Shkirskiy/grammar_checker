# message_handler.py - Message handling functions

import re
import logging
from config import MAX_MESSAGE_LENGTH

logger = logging.getLogger(__name__)

def convert_markdown_to_html(text):
    """
    Convert common markdown syntax to HTML tags.
    This is a fallback if the LLM uses markdown despite our instructions.
    """
    # Convert **text** to <b>text</b>
    text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
    
    # Convert _text_ or *text* to <i>text</i>
    text = re.sub(r'(?<!\\)_(.*?)(?<!\\)_', r'<i>\1</i>', text)
    text = re.sub(r'(?<!\*)\*(.*?)(?!\*)\*', r'<i>\1</i>', text)
    
    # Convert markdown-style line breaks (two spaces followed by newline) to <br>
    text = re.sub(r'  \n', r'<br>\n', text)
    
    # Convert double newlines to paragraph breaks
    text = re.sub(r'\n\n', r'<br><br>', text)
    
    return text

def combine_messages(messages):
    """
    Combine consecutive messages if they appear to be parts of the same text.
    
    Args:
        messages: List of tuples (message_text, message_id)
        
    Returns:
        Tuple of (combined_text, list_of_message_ids)
    """
    if not messages:
        return "", []
    
    # If only one message, return it directly
    if len(messages) == 1:
        return messages[0][0], [messages[0][1]]
    
    # Extract message texts and ids
    message_texts = [msg[0] for msg in messages]
    message_ids = [msg[1] for msg in messages]
    
    # Check if messages appear to be parts of the same text
    # (e.g., first message ends without a period, next message starts with lowercase)
    combined_text = message_texts[0]
    
    for i in range(1, len(message_texts)):
        prev_msg = message_texts[i-1]
        curr_msg = message_texts[i]
        
        # Check if previous message ends with sentence-ending punctuation
        ends_with_punct = re.search(r'[.!?]\s*$', prev_msg)
        
        # Check if current message starts with lowercase letter or continuation marks
        starts_with_lowercase = re.search(r'^[a-z,;:]', curr_msg)
        
        # If previous message doesn't end with punctuation or current starts with lowercase,
        # they are likely parts of the same text
        if not ends_with_punct or starts_with_lowercase:
            # Add space only if the previous message doesn't end with a hyphen
            if prev_msg.strip().endswith('-'):
                combined_text = combined_text.rstrip('-') + curr_msg
            else:
                combined_text += ' ' + curr_msg
        else:
            # Otherwise, add a newline between messages
            combined_text += '\n\n' + curr_msg
    
    return combined_text, message_ids

def split_response(text, max_length=None):
    """
    Split a long response into parts, ensuring HTML tags are properly handled.
    
    Args:
        text: HTML-formatted text to split
        max_length: Maximum length for each part (defaults to MAX_MESSAGE_LENGTH from config)
        
    Returns:
        List of text parts
    """
    if max_length is None:
        max_length = MAX_MESSAGE_LENGTH
    
    if len(text) <= max_length:
        return [text]
    
    parts = []
    current_part = ""
    
    # Stack to keep track of open HTML tags
    open_tags = []
    
    # Regular expressions for HTML tags
    open_tag_pattern = re.compile(r'<([a-zA-Z][a-zA-Z0-9]*)(?:\s[^>]*)?>')
    close_tag_pattern = re.compile(r'</([a-zA-Z][a-zA-Z0-9]*)>')
    
    # Process text character by character
    i = 0
    while i < len(text):
        # Check if adding the next character would exceed max_length
        if len(current_part) >= max_length:
            # Try to find a good break point (end of sentence)
            break_pos = max(current_part.rfind('.'), current_part.rfind('!'), current_part.rfind('?'))
            
            if break_pos == -1 or break_pos < max_length - 200:
                # If no sentence break found in reasonable range, look for a space
                break_pos = current_part.rfind(' ')
            
            if break_pos == -1 or break_pos < max_length - 300:
                # If still no good break point, just use max_length
                break_pos = len(current_part) - 1
            
            # Add 1 to include the punctuation or space in the current part
            break_pos += 1
            
            # Get the text for current part
            part_text = current_part[:break_pos]
            
            # Close any open tags
            closing_tags = ''.join(f'</{tag}>' for tag in reversed(open_tags))
            part_text += closing_tags
            
            parts.append(part_text)
            
            # Start new part with opening tags
            opening_tags = ''.join(f'<{tag}>' for tag in open_tags)
            current_part = opening_tags + current_part[break_pos:]
        
        # Process HTML tags to keep track of open/close tags
        if text[i:i+1] == '<':
            # Potential HTML tag
            open_tag_match = open_tag_pattern.match(text[i:])
            close_tag_match = close_tag_pattern.match(text[i:])
            
            if open_tag_match:
                tag_name = open_tag_match.group(1)
                tag_length = open_tag_match.end()
                
                # Add the full tag to current_part
                current_part += text[i:i+tag_length]
                
                # Ignore self-closing tags like <br/>, <img/>
                if not text[i+tag_length-2:i+tag_length] == '/>':
                    open_tags.append(tag_name)
                
                i += tag_length
                continue
                
            elif close_tag_match:
                tag_name = close_tag_match.group(1)
                tag_length = close_tag_match.end()
                
                # Add the closing tag to current_part
                current_part += text[i:i+tag_length]
                
                # Remove the tag from open_tags if it's there
                if open_tags and open_tags[-1] == tag_name:
                    open_tags.pop()
                
                i += tag_length
                continue
        
        # Add the current character to current_part
        current_part += text[i]
        i += 1
    
    # Add the last part
    if current_part:
        parts.append(current_part)
    
    return parts
