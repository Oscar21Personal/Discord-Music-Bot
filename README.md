# Discord-Music-Bot

## How to setup Python virtual environment

- First create a virtual environment
```
python -m venv .venv
```
- Then activate this virtual environment
```
.venv\Scripts\activate
```
- After that, install all packages
```
pip install -r requirements.txt
```
- Now you have successful set up Python virtual environment
- To start the discord music bot, run
```
python src/main.py
```
- When you’re done, deactivate the virtual environment. Type
```
deactivate
```

## How to setup Discord Bot token

- First, create a `.env` file in the python project directory.
- Then add these lines. You need to enter your Discord Bot token and your Discord user id.
```
DISCORD_BOT_TOKEN="your_token"
ADMINISTRATOR_ID="123456789012345678"
```
- Noted that `.env` file is in `.gitignore` so it will never be pushed onto github.