def register_all_handlers(bot):
    from bouijee_core import (
        send_welcome,
        show_menu,
        show_info,
        choose_risk_level,
        handle_risk_selection,
        handle_mitt_konto,
        prompt_mt4_id,
        handle_confirm_signal,
        handle_balance_input,
        handle_unexpected_messages,
        show_main_menu,
        handle_standby,
        show_valutapar_info,
        handle_callback
    )

    # === Kommandon ===
    bot.message_handler(commands=["start"])(send_welcome)
    bot.message_handler(commands=["meny"])(show_menu)

    # === Callback-knappar ===
    bot.callback_query_handler(func=lambda call: call.data == "info")(show_info)
    bot.callback_query_handler(func=lambda call: call.data == "risknivå")(choose_risk_level)
    bot.callback_query_handler(func=lambda call: call.data.startswith("risk_"))(handle_risk_selection)
    bot.callback_query_handler(func=lambda call: call.data == "mitt_konto")(handle_mitt_konto)
    bot.callback_query_handler(func=lambda call: call.data == "koppla_mt4")(prompt_mt4_id)
    bot.callback_query_handler(func=lambda call: call.data == "demo_signal")(show_main_menu)
    bot.callback_query_handler(func=lambda call: call.data == "standby")(handle_standby)
    bot.callback_query_handler(func=lambda call: call.data == "valutapar_info")(show_valutapar_info)
    bot.callback_query_handler(func=lambda call: call.data.startswith("confirm_"))(handle_confirm_signal)
    bot.callback_query_handler(func=lambda call: True)(handle_callback)

    # === Textsvar och saldo ===
    bot.message_handler(func=lambda m: str(m.from_user.id) in awaiting_balance_input)(handle_balance_input)
    bot.message_handler(func=lambda message: True, content_types=['text'])(handle_unexpected_messages)
