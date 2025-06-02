from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters, CallbackQueryHandler
from telegram import ReplyKeyboardMarkup

user_state = {}  # хранит состояние пользователя

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ["➕ Добавить", "📋 Список"],
        ["🗑 Очистить", "✅ Готово"],
        ["#️⃣ Сколько задач"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Привет! Я могу записывать твои задачи.\nВыбери действие:", reply_markup=reply_markup)


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    # Если пользователь в режиме "добавить задачу"
    if user_state.get(user_id) == "adding":
        task_file = f"tasks_{user_id}.txt"
        with open(task_file, "a", encoding="utf-8") as file:
            file.write(text + "\n")
        user_state[user_id] = None  # сбрасываем режим
        await update.message.reply_text(f"Задача добавлена: {text}")
        return
    if user_state.get(user_id) == "deleting":
        task_file = f"tasks_{user_id}.txt"
        try:
            with open(task_file, "r", encoding="utf-8") as file:
                tasks = file.readlines()
        except FileNotFoundError:
            tasks = []
        try:
            num = int(text)
            if num < 1 or num > len(tasks):
                await update.message.reply_text("Неверный номер задачи.")
            else:
                removed_task = tasks.pop(num - 1)
                with open(task_file, "w", encoding="utf-8") as file:
                    file.writelines(tasks)
                await update.message.reply_text(f"Удалена задача №{num}: {removed_task.strip()}")
        except ValueError:
            await update.message.reply_text("Нужно ввести число.")

        user_state[user_id] = None
        return

  

    # Обработка кнопок
    if text == "📋 Список":
        await list_tasks(update, context)
    elif text == "🗑 Очистить":
        await clear(update, context)
    elif text == "✅ Готово":
        user_state[user_id] = "deleting"
        await update.message.reply_text("Напиши номер выполненной задачи (например: 2)")
    elif text == "#️⃣ Сколько задач":
        await count(update, context)
    elif text == "➕ Добавить":
        user_id = update.effective_user.id
        user_state[user_id] = "adding"
        await update.message.reply_text("Напиши свою задачу:")
    else:
        await update.message.reply_text("Я не понял. Используй кнопки или команды.")



async def handle_delete_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    task_file = f"tasks_{user_id}.txt"

    data = query.data  # будет в виде "delete:1"
    if data.startswith("delete:"):
        index = int(data.split(":")[1])

        try:
            with open(task_file, "r", encoding="utf-8") as file:
                tasks = file.readlines()
        except FileNotFoundError:
            tasks = []

        if 0 <= index < len(tasks):
            removed_task = tasks.pop(index)
            with open(task_file, "w", encoding="utf-8") as file:
                file.writelines(tasks)

            await query.edit_message_text(f"❌ Удалено: {removed_task.strip()}")
        else:
            await query.edit_message_text("Задача уже удалена.")


# /add задача
async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    task = ' '.join(context.args)
    if not task:
        await update.message.reply_text("Напиши задачу после команды /add, например:\n/add Помыть посуду")
        return
    
    
    user_id = update.effective_user.id
    task_file = f"tasks_{user_id}.txt"

    with open(task_file, "a", encoding="utf-8") as file:
        file.write(task + "\n")
    await update.message.reply_text(f"Добавил задачу: {task}")

# /list
async def list_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    task_file = f"tasks_{user_id}.txt"
    try:
        with open(task_file, "r", encoding="utf-8") as file:
            tasks = file.readlines()
    except FileNotFoundError:
        tasks = []

    if not tasks:
        await update.message.reply_text("У тебя нет задач.")
    else:
        for i, task in enumerate(tasks):
            keyboard = InlineKeyboardMarkup([[
                InlineKeyboardButton("Удалить ❌", callback_data=f"delete:{i}")
            ]])
            await update.message.reply_text(f"{i+1}. {task.strip()}", reply_markup=keyboard)

# /clear
async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    task_file = f"tasks_{user_id}.txt"
    open(task_file, "w").close()
    await update.message.reply_text("Список задач очищен.")


# /count
async def count(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    task_file = f"tasks_{user_id}.txt"
    try:
        with open(task_file, "r", encoding="utf-8") as file:
            tasks = file.readlines()
        total = len(tasks)
        await update.message.reply_text(f"У тебя {total} задач(и).")
    except FileNotFoundError:
        await update.message.reply_text("Список задач пока пуст.")


# /done
async def done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    task_file = f"tasks_{user_id}.txt"
    try:
        with open(task_file, "r", encoding="utf-8") as file:
            tasks = file.readlines()
    except FileNotFoundError:
        tasks = []

    if not tasks:
        await update.message.reply_text("У тебя нет задач.")
    else:
        if not context.args:
            await update.message.reply_text("Укажи номер задачи, которую хочешь удалить. Например: \n/done 2")
            return
        try:   
            num = int(context.args[0])
            if num < 1 or num > len(tasks):
                await update.message.reply_text("Неверный номер задачи.")
                return
            
            removed_task = tasks.pop(num - 1)

            with open(task_file, "w", encoding="utf-8") as file:
                file.writelines(tasks)

            await update.message.reply_text(f"Удалена задача №{num}: {removed_task.strip()}")
        except ValueError:
            await update.message.reply_text("Номер задачи должен быть числом")


# Запуск
app = ApplicationBuilder().token("439615167:AAFyKrhGGd1BKPEtHUZu_WauDoRpObTyBTo").build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("add", add))
app.add_handler(CommandHandler("list", list_tasks))
app.add_handler(CommandHandler("clear", clear))
app.add_handler(CommandHandler("count", count))
app.add_handler(CommandHandler("done", done))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
app.add_handler(CallbackQueryHandler(handle_delete_callback))

app.run_polling()