import os
import asyncio
import logging
import json
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Получение URL мини-приложения и ID администратора из переменных окружения
WEBAPP_URL = os.getenv("WEBAPP_URL")
ADMIN_ID = os.getenv("ADMIN_ID")

class InsuranceMiniAppBot:
    """Класс для бота, который использует мини-приложение для сбора данных страховки."""
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик команды /start."""
        user = update.effective_user
        
        # Создаем кнопку для открытия мини-приложения
        keyboard = [
            [InlineKeyboardButton(
                "Заполнить форму страховки", 
                web_app=WebAppInfo(url=WEBAPP_URL)
            )]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Отправляем приветственное сообщение с кнопкой
        await update.message.reply_text(
            f"Привет, {user.first_name}! 👋\n\n"
            f"Я бот для сбора информации для медицинской страховки в Германии.\n\n"
            f"Нажмите на кнопку ниже, чтобы открыть форму с необходимыми данными:",
            reply_markup=reply_markup
        )
        
        logger.info(f"Пользователь {user.id} ({user.first_name}) запустил бота")
    
    async def web_app_data(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик данных, полученных из мини-приложения."""
        user = update.effective_user
        data = json.loads(update.effective_message.web_app_data.data)
        
        logger.info(f"Получены данные от пользователя {user.id} ({user.first_name})")
        
        # Формируем сообщение с данными пользователя
        message = f"📋 *Новая заявка на страховку*\n\n"
        message += f"👤 *От пользователя*: {user.first_name} {user.last_name if user.last_name else ''} (@{user.username if user.username else 'без username'})\n\n"
        
        # Добавляем все поля из формы
        for key, value in data.items():
            if key == "photo":
                continue  # Фото обрабатываем отдельно
            field_name = key.replace("_", " ").capitalize()
            message += f"*{field_name}*: {value}\n"
        
        # Отправляем сообщение администратору
        try:
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=message,
                parse_mode="Markdown"
            )
            
            # Если есть фото, отправляем его отдельным сообщением
            if "photo" in data and data["photo"]:
                # Предполагается, что photo - это URL или base64 строка
                # Здесь нужна дополнительная логика для обработки фото
                await context.bot.send_message(
                    chat_id=ADMIN_ID,
                    text="Фото будет отправлено отдельно после реализации обработки изображений."
                )
            
            logger.info(f"Данные пользователя {user.id} отправлены администратору")
            
            # Отправляем подтверждение пользователю
            await update.message.reply_text(
                "Спасибо! Ваши данные успешно отправлены. Мы свяжемся с вами в ближайшее время."
            )
        except Exception as e:
            logger.error(f"Ошибка при отправке данных администратору: {e}")
            await update.message.reply_text(
                "Произошла ошибка при отправке данных. Пожалуйста, попробуйте позже."
            )

async def main() -> None:
    """Основная функция для запуска бота."""
    # Получаем токен бота из переменных окружения
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.error("Токен бота не найден. Убедитесь, что переменная TELEGRAM_BOT_TOKEN установлена в файле .env")
        return
    
    # Создаем экземпляр бота
    bot = InsuranceMiniAppBot()
    
    # Создаем и настраиваем приложение
    application = Application.builder().token(token).build()
    
    # Регистрируем обработчики команд
    application.add_handler(CommandHandler("start", bot.start_command))
    
    # Регистрируем обработчик данных из мини-приложения
    application.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, bot.web_app_data))
    
    # Запускаем бота
    await application.initialize()
    await application.start()
    
    logger.info("Бот запущен. Нажмите Ctrl+C для остановки.")
    
    # Держим бота запущенным
    try:
        while True:
            await asyncio.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        logger.info("Бот остановлен.")
    finally:
        await application.stop()

if __name__ == "__main__":
    asyncio.run(main()) 