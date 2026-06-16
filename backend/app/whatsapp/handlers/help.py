from app.services.whatsapp_service import whatsapp_service

async def handle_help(to_number: str, db=None, dietitian_id=None):
    msg = (
        "🤖 *NutriPlan Bot - How can I help?*\n\n"
        "Here are the commands you can use:\n"
        "• *TODAY* - See today's meal plan\n"
        "• *DONE* - Log your current meal as completed\n"
        "• *SWAP [food]* - Ask for an alternative (e.g., 'Swap paneer')\n"
        "• *GROCERY* - Get this week's grocery list\n"
        "• Ask a nutrition question (e.g., 'What helps with thyroid?')\n"
        "• *HELP* - Show this message again"
    )
    await whatsapp_service.send_text_message(
        to_number, msg, db=db, dietitian_id=dietitian_id
    )
