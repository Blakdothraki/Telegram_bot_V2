import sqlite3
from telegram import Update, Bot,  InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackContext, JobQueue, MessageHandler, filters, ContextTypes
import logging
from datetime import datetime, timedelta, time
from flask import Flask, request, jsonify
import stripe
import requests
import threading

# Initialize the database
def initialize_db():
    conn = sqlite3.connect('subscriptions.db')
    cursor = conn.cursor()
    
    # Create table if it doesn't exist
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL UNIQUE,
        username TEXT,
        expiry_date TEXT NOT NULL,
        receipt_url TEXT
    )
    ''')
    
    conn.commit()
    conn.close()

initialize_db() 

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Telegram bot token
TOKEN =  'your token'
BOT_USERNAME = '@*****_bot'

# Initialize bot
app = Application.builder().token(TOKEN).build()

# Admin Telegram ID
ADMIN_ID = 'your telegram id'
ADMIN_USERNAME = '@username'

# Command handler for start
async def start(update: Update, context: CallbackContext):
    await update.message.reply_text(
        'Greetings! I can assist you with your subscription management.\n' +
        'To subscribe, press /subscribe.\n' +
        'To unsubscribe press /unsubscribe.\n' +
        'To check expiry date, press /expiry.\n' +
        'To get help press /help.'
    )

# Command handler for help
async def get_help(update: Update, context: CallbackContext):
    keyboard = [
        [InlineKeyboardButton("Contact the admin", url=f"tg://user?id={ADMIN_ID}" )]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text('Greetings! if you need help, you can contact the admin: ', reply_markup=reply_markup)

# Command handler for subscribing users
async def subscribe(update: Update, context: CallbackContext):
    user = update.message.from_user
    user_id = user.id
    username = user.username
    amount = 500  # Amount in cents (e.g., $5.00)

    # Create checkout session
    response = requests.post('http://localhost:4242/create-checkout-session', json={
        'user_id': user_id,
        'username': username,
        'amount': amount
    })
    session_id = response.json()['id']

    await update.message.reply_text(f'Please complete your payment: https://checkout.stripe.com/pay/{session_id}')

# Command handler for unsubscribing users
async def unsubscribe(update: Update, context: CallbackContext):
    user = update.message.from_user
    user_id = user.id

    conn = sqlite3.connect('subscriptions.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM users WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()

    await update.message.reply_text(f'Unsubscribed {user.username}.')

# Command handler for checking subscription expiry date
async def expiry(update: Update, context: CallbackContext):
    user = update.message.from_user
    user_id = user.id
    conn = sqlite3.connect('subscriptions.db')
    cursor = conn.cursor()
    cursor.execute('SELECT expiry_date FROM users WHERE user_id = ?', (user_id,))
    row = cursor.fetchone()
    conn.close()

    if row:
        expiry_date = row[0]
        await update.message.reply_text(f'{user.username}Your subscription expires on {expiry_date}.')
    else:
        await update.message.reply_text(f'{user.username} You are not subscribed.')

# Handling response
def handle_response(text: str) -> str:
    processed: str = text.lower()
    return 'Please enter /start to command me...'

# Handling messages 
async def handle_message(update: Update, context: CallbackContext):
    message_type: str = update.message.chat.type
    text: str = update.message.text 

    print(f'User ({update.message.chat.id}) in {message_type}: "{text}" ')

    if 'group' in message_type:
        if BOT_USERNAME in text:
            new_text: str = text.replace(BOT_USERNAME, ' ').strip()
            response: str = handle_response(new_text)
            await update.message.reply_text(response)

        else:
            return 
    
    else: 
        response: str = handle_response(text)
        # print('Bot: ', response)
        # await update.message.reply_text(response)

app.add_handler(CommandHandler('start', start))
app.add_handler(CommandHandler('subscribe', subscribe))
app.add_handler(CommandHandler('unsubscribe', unsubscribe))
app.add_handler(CommandHandler('expiry', expiry))
app.add_handler(CommandHandler('help', get_help))

app.add_handler(MessageHandler(filters.TEXT, handle_message))

# Function to remove expired users from the group
async def remove_expired_users(context: CallbackContext):
    bot: Bot = context.bot
    conn = sqlite3.connect('subscriptions.db')
    cursor = conn.cursor()
    cursor.execute('SELECT user_id FROM users WHERE expiry_date < ?', (datetime.now().strftime('%Y-%m-%d'),))
    expired_users = cursor.fetchall()
    
    for (user_id,) in expired_users:
        try:
            await bot.kick_chat_member(chat_id=context.job.data['chat_id'], user_id=user_id)
            cursor.execute('DELETE FROM users WHERE user_id = ?', (user_id,))
        except Exception as e:
            logging.error(f'Failed to remove user {user_id}: {e}')

    conn.commit()
    conn.close()

# Schedule daily job to remove expired users
def schedule_jobs(job_queue: JobQueue, chat_id: int):
    job_queue.run_daily(
        remove_expired_users,
        time=time(hour=0, minute=0, second=0),  # Run daily at midnight
        data={'chat_id': chat_id}
    )

schedule_jobs(app.job_queue, '1002170206409')

# Flask app for payment integration
flask_app = Flask(__name__)

# Stripe API key
stripe.api_key = 'YOUR_STRIPE_SECRET_KEY'

# Endpoint to create a checkout session
@flask_app.route('/create-checkout-session', methods=['POST'])
def create_checkout_session():
    data = request.json
    user_id = data['user_id']
    username = data['username']
    amount = data['amount']  # Amount in cents

    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[{
            'price_data': {
                'currency': 'usd',
                'product_data': {
                    'name': 'Subscription',
                },
                'unit_amount': amount,
            },
            'quantity': 1,
        }],
        mode='payment',
        success_url='https://your-success-url.com',
        cancel_url='https://your-cancel-url.com',
        metadata={
            'user_id': user_id,
            'username': username
        }
    )

    return jsonify(id=session.id)

# Endpoint to handle webhook events from Stripe
@flask_app.route('/webhook', methods=['POST'])
def webhook():
    payload = request.get_data(as_text=True)
    sig_header = request.headers.get('Stripe-Signature')
    endpoint_secret = 'YOUR_WEBHOOK_SECRET'
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError as e:
        return 'Invalid payload', 400
    except stripe.error.SignatureVerificationError as e:
        return 'Invalid signature', 400

    # Handle the event
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        handle_successful_payment(session)

    return '', 200

# Function to handle successful payments
def handle_successful_payment(session):
    user_id = session['metadata']['user_id']
    username = session['metadata']['username']
    receipt_url = session['receipt_url']
    
    conn = sqlite3.connect('subscriptions.db')
    cursor = conn.cursor()
    expiry_date = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
    
    cursor.execute('''
    INSERT OR REPLACE INTO users (user_id, username, expiry_date, receipt_url) VALUES (?, ?, ?, ?)
    ''', (user_id, username, expiry_date, receipt_url))
    
    conn.commit()
    conn.close()

# Function to run the Flask app
def run_flask():
    flask_app.run(host='0.0.0.0', port=4242)

# Run the Flask app and the Telegram bot concurrently
if __name__ == '__main__':
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()
    
    print("Starting bot...")
    app.run_polling()
    app.idle()
