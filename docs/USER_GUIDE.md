# User guide

How to use Bazarche, for customers and for the shop owner. The button names below are from the English interface; the Persian interface has the same buttons in the same places.

## For customers

1. Open the bot in Telegram and press **Start** (or send `/start`). The main menu appears at the bottom of the chat.
2. **🛍 Products**: choose a category, then a product, to see its photo, description, price and whether it is in stock. Press **➕ Add to cart**.
3. **🛒 Cart**: change the quantity of each product with **+** and **−**, or press **🗑 Empty cart**. You cannot add more than the shop has in stock.
4. Press **✅ Place order** and answer three questions: your full name, your phone number (type it, or tap **📱 Share my phone number**) and your delivery address. Check the summary and press **✅ Confirm and place order**.
5. **📦 My orders** lists all your orders with their status. While an order is still new, you can open it and press **❌ Cancel this order**. The bot sends you a message every time the shop changes the status of your order.
6. **🌐 Language** switches between Persian and English.

## For the shop owner

The shop owner and any helpers are the admins: the Telegram users whose ids are in `ADMIN_IDS`. Send `/admin` to open the admin panel. Send `/cancel` at any time to stop a form you are filling in.

### Products

1. **🗂 Add category**: send the name of a category, for example "Kitchen". Every product belongs to a category.
2. **➕ Add product**: choose the category, then send the name, a short description (or `/skip`), the price in toman, the number in stock and a photo (or `/skip`). Check the summary and press **✅ Save**.
3. **📋 Manage products**: choose a category and a product to change its name, description, price, stock or photo, or press **🚫 Hide** to remove it from the shop without deleting it. Hidden products can be shown again with **👁 Show**.

### Orders

- Every new order arrives as a message with a button to open it.
- **📦 Orders** lists the open orders, newest first. Open an order to move it forward: **Received** → **Confirmed** → **Shipped** → **Delivered**, or cancel it. The customer gets a message at every step.
- Cancelling an order, by you or by the customer, puts its products back in stock. You also get a message when a customer cancels.

### Sales report

**📊 Sales report** → **Last 7 days** or **Last 30 days** shows the number of orders, revenue, the average order, cancelled orders, the five best sellers and a chart of daily sales. Cancelled orders are not counted as sales.

## Running the bot

To run the bot on your own server, follow the [deployment guide](DEPLOY.md).
