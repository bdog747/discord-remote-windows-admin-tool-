# Discord Remote Admin Bot

## Overview

A Discord bot that provides remote administration capabilities for Windows systems through Discord commands.

## Features

### System Control
- System information retrieval
- Shutdown, restart, and logoff commands
- Admin privilege checking
- Process management

### File Operations
- File upload/download
- Directory navigation
- File operations (delete, hide, unhide)

### Monitoring
- Screenshot capture
- Clipboard monitoring
- Idle time tracking

### Utilities
- Message box display
- Website opening
- Geolocation via IP
- Text-to-speech (if dependencies available)

## Installation

### Requirements
- Python 3.6+
- Windows operating system
- Discord bot token

### Setup

1. **Create a Discord Bot:**
   - Go to [Discord Developer Portal](https://discord.com/developers/applications)
   - Create a new application
   - Go to "Bot" section and create a bot
   - Copy the bot token
   - Enable "Message Content Intent" in bot settings

2. **Configuration:**
   Edit the configuration section in the script:
   ```python
   DISCORD_TOKEN = "your_bot_token_here"
   ADMIN_USER_ID = 123456789012345678  # Your actual Discord user ID
   REQUIRE_ADMIN_PRIVILEGES = False
   ```

3. **Run the bot:**
   ```bash
   python bot.py
   ```

## Basic Commands

### System Information
- `!sysinfo` - Get system information
- `!admincheck` - Check admin privileges
- `!idletime` - Get user idle time

### File Operations
- `!cd <path>` - Change directory
- `!currentdir` - Show current directory
- `!displaydir` - List directory contents
- `!upload` - Upload attached file
- `!download <path>` - Download file
- `!delete <path>` - Delete file

### System Control
- `!shutdown <seconds>` - Shutdown computer (default: 60s)
- `!restart <seconds>` - Restart computer (default: 60s)
- `!logoff` - Log off user
- `!prockill <name>` - Kill process by name

### Utilities
- `!message <text>` - Show message box
- `!website <url>` - Open website
- `!geolocate` - Get approximate location from IP
- `!clipboard` - Get clipboard content
- `!screenshot` - Take screenshot

### Help
- `!help_admin` - Show all available commands
### Note
- `some commands not listed shows up with discord help command`
## Security Features

- **User Restriction:** Only responds to specified ADMIN_USER_ID
- **Command Validation:** Input validation and error handling
- **Permission Checks:** Some commands verify admin privileges

## Important Notes

- Some advanced features require additional Python packages
- Basic functionality works with standard Python libraries
- Screenshot feature requires `pyautogui` for full functionality
- Webcam features require `opencv-python`
- Audio features require `pyaudio`

## Troubleshooting

### Common Issues

1. **Bot won't start:**
   - Check Discord token is correct
   - Verify ADMIN_USER_ID is set to your actual user ID
   - Ensure Python version is 3.6+

2. **Commands not working:**
   - Verify bot has message content intent enabled in Discord developer portal
   - Check user ID matches ADMIN_USER_ID
   - Some commands require admin privileges on the system

3. **Features not available:**
   - Some commands require additional Python packages
   - Basic file and system operations work without extra dependencies
