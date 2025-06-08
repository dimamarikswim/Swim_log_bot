from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler, MessageHandler, filters
import re

TOKEN = "8095728516:AAGHcobARtBcxkOltJPX91MaX7G_h6Aux0k"

# Временное хранилище состояния опроса
user_data = {}
# Хранилище всех результатов по пользователям
user_results = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("М", callback_data='gender_m'), InlineKeyboardButton("Ж", callback_data='gender_f')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    user_data[update.effective_user.id] = {}
    await update.message.reply_text("Выберите пол:", reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data
    user_state = user_data.get(user_id, {})

    if 'gender' not in user_state and data.startswith('gender_'):
        user_state['gender'] = 'М' if data == 'gender_m' else 'Ж'
        user_data[user_id] = user_state
        await query.edit_message_text("Введите год рождения (например, 1990):")
        return

    if 'birth_year' in user_state and 'activity' not in user_state and data.startswith('activity_'):
        user_state['activity'] = 'Тренировка' if data == 'activity_training' else 'Соревнования'
        user_data[user_id] = user_state
        keyboard = [
            [InlineKeyboardButton("Бат", callback_data='style_butterfly')],
            [InlineKeyboardButton("Кроль", callback_data='style_freestyle')],
            [InlineKeyboardButton("Спина", callback_data='style_backstroke')],
            [InlineKeyboardButton("Комплекс", callback_data='style_medley')],
            [InlineKeyboardButton("Брас", callback_data='style_breaststroke')],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("Выберите стиль плавания:", reply_markup=reply_markup)
        return

    if 'style' not in user_state and data.startswith('style_'):
        styles = {
            'style_butterfly': 'Бат',
            'style_freestyle': 'Кроль',
            'style_backstroke': 'Спина',
            'style_medley': 'Комплекс',
            'style_breaststroke': 'Брас',
        }
        user_state['style'] = styles[data]
        user_data[user_id] = user_state
        keyboard = [
            [InlineKeyboardButton("50", callback_data='pool_50')],
            [InlineKeyboardButton("25", callback_data='pool_25')],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("Выберите длину бассейна (в метрах):", reply_markup=reply_markup)
        return

    if 'pool' not in user_state and data.startswith('pool_'):
        user_state['pool'] = int(data.split('_')[1])
        user_data[user_id] = user_state
        await query.edit_message_text("Введите дистанцию (в метрах), например: 100")
        return

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_state = user_data.get(user_id, {})
    text = update.message.text.strip()

    if 'gender' in user_state and 'birth_year' not in user_state:
        if text.isdigit() and 1900 <= int(text) <= 2025:
            user_state['birth_year'] = int(text)
            user_data[user_id] = user_state
            keyboard = [
                [InlineKeyboardButton("Тренировка", callback_data='activity_training')],
                [InlineKeyboardButton("Соревнования", callback_data='activity_competition')],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text("Выберите тип активности:", reply_markup=reply_markup)
        else:
            await update.message.reply_text("Введите корректный год рождения (например, 1990):")
        return

    if 'pool' in user_state and 'distance' not in user_state:
        if text.isdigit() and int(text) > 0:
            user_state['distance'] = int(text)
            user_data[user_id] = user_state
            await update.message.reply_text("Введите время (например, 1:23.45 или 83.45):")
        else:
            await update.message.reply_text("Введите корректную дистанцию (число в метрах):")
        return

    if 'distance' in user_state and 'time' not in user_state:
        if re.match(r'^(\d{1,2}:\d{2}\.\d{1,2}|\d+\.\d{1,2})$', text):
            user_state['time'] = text
            user_data[user_id] = user_state

            # Сохраняем результат пользователя
            results_list = user_results.get(user_id, [])
            results_list.append(user_state.copy())
            user_results[user_id] = results_list

            summary = (
                f"Данные сохранены:\n"
                f"Пол: {user_state.get('gender')}\n"
                f"Год рождения: {user_state.get('birth_year')}\n"
                f"Активность: {user_state.get('activity')}\n"
                f"Стиль: {user_state.get('style')}\n"
                f"Бассейн: {user_state.get('pool')} м\n"
                f"Дистанция: {user_state.get('distance')} м\n"
                f"Время: {user_state.get('time')}"
            )
            await update.message.reply_text(summary)
            user_data.pop(user_id, None)  # Очистить данные для нового опроса
        else:
            await update.message.reply_text("Введите корректное время (например, 1:23.45 или 83.45):")
        return

    await update.message.reply_text("Пожалуйста, начните с команды /start.")

async def results(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    results_list = user_results.get(user_id)
    if not results_list:
        await update.message.reply_text("У вас нет сохранённых результатов.")
        return

    message = "Ваши результаты:\n\n"
    for i, res in enumerate(results_list, 1):
        message += (
            f"{i}.\n"
            f"Пол: {res.get('gender')}\n"
            f"Год рождения: {res.get('birth_year')}\n"
            f"Активность: {res.get('activity')}\n"
            f"Стиль: {res.get('style')}\n"
            f"Бассейн: {res.get('pool')} м\n"
            f"Дистанция: {res.get('distance')} м\n"
            f"Время: {res.get('time')}\n\n"
        )
    await update.message.reply_text(message)

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("results", results))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), text_handler))
    app.run_polling()

if __name__ == "__main__":
    main()
    