
#property strict

input string TelegramID = "6309977112";  // <-- Byt till ditt riktiga Telegram-ID
input string GoogleAppsScriptURL = "https://script.google.com/macros/s/DITT-ID/exec";  // <-- Byt till din webhook URL

void OnTick() {
   CheckClosedOrders();
}

void CheckClosedOrders() {
   static int lastTicket = -1;

   for (int i = OrdersHistoryTotal() - 1; i >= 0; i--) {
      if (OrderSelect(i, SELECT_BY_POS, MODE_HISTORY)) {
         if (OrderType() <= OP_SELL && OrderSymbol() == Symbol()) {
            if (OrderCloseTime() > 0 && OrderTicket() != lastTicket) {

               double profit = OrderProfit() + OrderSwap() + OrderCommission();
               string symbol = OrderSymbol();
               string action = (OrderType() == OP_BUY) ? "BUY" : "SELL";
               string result = (profit >= 0) ? "Win" : "Loss";

               string url = GoogleAppsScriptURL +
                            "?telegram_id=" + TelegramID +
                            "&symbol=" + symbol +
                            "&action=" + action +
                            "&profit=" + DoubleToString(profit, 2) +
                            "&result=" + result;

               char result_data[2048];
               char headers[] = "";
               char cookies[] = "";
               string result_headers = "";

               ResetLastError();
               int res = WebRequest(
                  "GET",
                  url,
                  headers,
                  cookies,
                  5000,
                  NULL,
                  0,
                  result_data,
                  result_headers
               );

               if (res == -1) {
                  Print("❌ WebRequest misslyckades. Felkod: ", GetLastError());
               } else {
                  Print("✅ Trade skickad till Google Sheets: ", url);
               }

               lastTicket = OrderTicket();
            }
         }
      }
   }
}
