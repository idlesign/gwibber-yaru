
"""
Paths to various Gwibber files and resources
SegPhault (Ryan Paul) - 11/22/2008
"""

import os, sys
from const import *

# Try to import * from custom, install custom.py to include packaging 
# customizations like distro API keys, etc
try:
  from custom import *
except:
  pass


PROGRAM_NAME = "gwibber"
UI_DIR_NAME = "ui"
THEME_DIR_NAME = os.path.join(UI_DIR_NAME, "themes")
LAUNCH_DIR = os.path.abspath(sys.path[0])
DATA_DIRS = [LAUNCH_DIR]
THEME_NAME = "default"

# Minimum theme version, this is a serial to ensure themes are compatible
# with current version of the client.  This serial is set in the theme 
# dir in a file named theme.version 
THEME_MIN_VERSION = 2

try:
  import xdg
  DATA_BASE_DIRS = xdg.BaseDirectory.xdg_data_dirs
  CACHE_BASE_DIR = xdg.BaseDirectory.xdg_cache_home
except:
  DATA_BASE_DIRS = [
    os.path.join(os.path.expanduser("~"), ".local", "share"),
    "/usr/local/share", "/usr/share"]
  CACHE_BASE_DIR = os.path.join(os.path.expanduser("~"), ".cache")

DATA_DIRS += [os.path.join(d, PROGRAM_NAME) for d in DATA_BASE_DIRS]

def get_twitter_keys():
  # Distros should register their own keys and not rely on the defaults
  return TWITTER_OAUTH_KEY, TWITTER_OAUTH_SECRET

def get_desktop_file():
  p = os.path.join(LAUNCH_DIR, "gwibber.desktop")
  if os.path.exists(p): return p
  
  for base in DATA_BASE_DIRS:
    p = os.path.join(base, "applications", "gwibber.desktop")
    if os.path.exists(p): return p

def get_theme_paths():
  for base in DATA_DIRS:
    theme_root = os.path.join(base, THEME_DIR_NAME)
    if os.path.exists(theme_root):
      for f in sorted(os.listdir(theme_root)):
        if not f.startswith('.'):
          theme_dir = os.path.join(theme_root, f)
          if os.path.isdir(theme_dir) and \
            os.path.exists(os.path.join(theme_dir, "theme.version")):
            with open(os.path.join(theme_dir, "theme.version")) as f:
              for line in f:
                if "theme_version" in line:
                  theme_version = int(line.split("=")[1])
                  if theme_version >= THEME_MIN_VERSION:
                    yield theme_dir

def get_theme_path(name):
  for path in get_theme_paths():
    if name == os.path.basename(path):
      return path

def get_themes():
  themes = {}
  for path in get_theme_paths():
    if not os.path.basename(path) in themes:
      themes[os.path.basename(path)] = path
  return themes

def get_ui_asset(asset_name):
  for base in DATA_DIRS:
    asset_path = os.path.join(base, UI_DIR_NAME, asset_name)
    if os.path.exists(asset_path):
      return asset_path

def get_template_dirs():
  for base in DATA_DIRS:
    p = os.path.join(base, UI_DIR_NAME, "templates")
    if os.path.exists(p):
      yield p

def get_theme_asset(asset_name):
  theme_path = get_theme_path(THEME_NAME)
  if theme_path:
    fname = os.path.join(theme_path, asset_name)
    if os.path.exists(fname):
      return fname
