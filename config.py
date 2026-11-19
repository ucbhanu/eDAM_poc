# Databricks notebook source
import os

from dotenv import load_dotenv

load_dotenv()

AUTH_URL = os.environ["AUTH_URL"]
CLIENT_ID = os.environ["CLIENT_ID"]
CLIENT_SECRET = os.environ["CLIENT_SECRET"]
PROXY = os.getenv("PROXY")
DAM_UI_URL = os.environ["URL"].strip().rstrip("/") + "/"
API_BASE = os.getenv("API_BASE") or DAM_UI_URL.replace("/dam/", "/api/core/")
