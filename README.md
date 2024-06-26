# Telegram_bot_v2
# Telegram Subscription Bot with Stripe Payment Integration

This project is a Telegram bot that manages group memberships based on subscription expiry dates. The bot uses SQLite for storing subscription data and integrates with Stripe for handling payments. The bot ensures fair management of user subscriptions and automatically removes expired users from the group.

## Features

- **Subscription Management**: Users can subscribe to the group for a specified number of days.
- **Payment Integration**: Uses Stripe to handle payments securely.
- **Automated User Removal**: Automatically removes users whose subscriptions have expired.
- **Database**: Uses SQLite to store user subscription details.

## Requirements

- Python 3.x
- Telegram bot token
- Stripe API keys
- Flask
- python-telegram-bot library
- requests library
- SQLite3

## Installation

1. **Clone the repository**:
    ```bash
    git clone https://github.com/yourusername/telegram-subscription-bot.git
    cd telegram-subscription-bot
    ```

2. **Install dependencies**:
    ```bash
    pip install Flask stripe python-telegram-bot requests
    ```

3. **Set up environment variables**:
    - Replace the following placeholders in the script with actual values:
        - `YOUR_TELEGRAM_BOT_TOKEN`
        - `YOUR_STRIPE_SECRET_KEY`
        - `YOUR_WEBHOOK_SECRET`
        - `YOUR_TELEGRAM_GROUP_ID`

4. **Run the script**:
    ```bash
    python your_script_name.py
    ```

5. **Set up Stripe webhooks**:
    - Configure your Stripe account to send webhook events to `http://yourdomain.com/webhook`.

## Usage

### Bot Commands

- **/subscribe [days]**: Subscribes the user for a specified number of days (default is 30 days). This command will generate a Stripe payment link for the user to complete the payment.
- **/unsubscribe**: Unsubscribes the user from the group.
- **/check_expiry**: Checks the user's subscription expiry date.

### Flask Endpoints

- **POST /create-checkout-session**: Creates a Stripe checkout session for the user.
- **POST /webhook**: Handles webhook events from Stripe to update the subscription status in the database.

## Code Structure

```plaintext
.
├── your_script_name.py     # Main script with bot and Flask app
├── README.md               # This README file
└── subscriptions.db        # SQLite database file (created automatically)
```

### Database Schema

The SQLite database contains a table named `users` with the following columns:

- `id`: Primary key, auto-incremented.
- `user_id`: Telegram user ID, unique.
- `username`: Telegram username.
- `expiry_date`: Subscription expiry date.
- `receipt_url`: URL of the Stripe payment receipt.

## Contributions

Contributions are welcome! Please open an issue or submit a pull request for any improvements or bug fixes.

## License

This project is licensed under the MIT License. See the LICENSE file for details.

## Contact

For any questions or issues, please contact [your-email@example.com].

---

This README provides an overview of the Telegram subscription bot, its features, installation steps, usage instructions, and more. Feel free to modify and expand it based on your specific needs and setup. 