"""Skupni uvozi za module Arhivskega pomočnika.

Ta datoteka je namenoma ločena, da so sistemske odvisnosti zbrane na enem mestu.
"""
import sys
import traceback
import os
import errno
import shutil
import re
import base64
import json
import sqlite3
import csv
from collections import deque
import tkinter as tk
from tkinter import messagebox, filedialog, scrolledtext, ttk
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import openpyxl
import threading
import urllib.request
import urllib.parse
import urllib.error
import time
import random
import ctypes
import ctypes.wintypes

try:
    import pymysql
    MYSQL_AVAILABLE = True
except ImportError:
    pymysql = None
    MYSQL_AVAILABLE = False
