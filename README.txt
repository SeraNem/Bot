# 🚀 Deploying Your Telegram Bot to Fly.io

## Prerequisites
- Install Fly CLI: https://fly.io/docs/hands-on/install-flyctl/
- Run `fly auth login` to log in

## 🔧 Setup & Deployment

1. Extract this folder
2. Run the following in your terminal:
   
   fly launch

3. Set your bot token secret:

   fly secrets set BOT_TOKEN=your_bot_token_here

4. Deploy it:

   fly deploy

Your bot will now run 24/7 using polling.