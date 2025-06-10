
#property strict

input string TelegramID = "6309977112";
input string GoogleAppsScriptURL = "https://script.google.com/macros/s/AKfycbydTWUvFNNesZ1CWqfsIfatXSpG8DV9TdGd_mI9xXhq7vopMSMHUcc3OKYKHaX4pSU/exec";

void OnTick() {
   static datetime lastCheck = 0;
   if (TimeCurrent() - lastCheck > 60) {
      CheckForSignal();
      lastCheck = TimeCurrent();
   }
}

void CheckForSignal() {
   string url = GoogleAppsScriptURL + "?mode=read_signal&telegram_id=" + TelegramID;

   char post_data[]; // tomt vid GET
   char result_data[2048];
   string result_headers = "";
   int timeout = 5000;

   ResetLastError();
   int res = WebRequest(
      "GET",
      url,
      "",
      timeout,
      post_data,
      result_data,
      result_headers
   );

   if (res == -1) {
      Print("❌ WebRequest misslyckades: ", GetLastError());
      return;
   }

   string response = CharArrayToString(result_data);
   if (StringLen(response) == 0 || StringFind(response, "NO_SIGNAL") != -1) {
      return;
   }

   // Format: EURUSD|BUY
   string symbol, action;
   StringReplace(response, "\n", ""); // Rensa eventuella radbrytningar
   int pos = StringFind(response, "|");
   if (pos > 0) {
      symbol = StringSubstr(response, 0, pos);
      action = StringSubstr(response, pos + 1);
   } else {
      Print("❌ Ogiltigt svar: ", response);
      return;
   }

   bool success = ExecuteTrade(symbol, action);
   if (success) {
      string confirmURL = GoogleAppsScriptURL + "?mode=mark_executed&telegram_id=" + TelegramID + "&symbol=" + symbol + "&action=" + action;
      WebRequest("GET", confirmURL, "", timeout, post_data, result_data, result_headers);
   }
}

bool ExecuteTrade(string symbol, string action) {
   int cmd = (StringFind(action, "BUY") != -1) ? OP_BUY : OP_SELL;
   double lotSize = 0.1;
   double slippage = 3;
   double price = (cmd == OP_BUY) ? MarketInfo(symbol, MODE_ASK) : MarketInfo(symbol, MODE_BID);

   int ticket = OrderSend(symbol, cmd, lotSize, price, slippage, 0, 0, "Telegram Signal", 0, 0, clrGreen);
   if (ticket < 0) {
      Print("❌ Order misslyckades: ", GetLastError());
      return false;
   } else {
      Print("✅ Order utförd: ", action, " ", symbol);
      return true;
   }
}
