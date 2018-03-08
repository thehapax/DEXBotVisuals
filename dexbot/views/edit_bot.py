from .ui.edit_bot_window_ui import Ui_Dialog
from .confirmation import ConfirmationDialog
from .notice import NoticeDialog

from PyQt5 import QtWidgets


class EditBotView(QtWidgets.QDialog, Ui_Dialog):
    def __init__(self, controller, botname, config):
        super().__init__()
        self.controller = controller

        self.setupUi(self)
        bot_data = config['bots'][botname]
        self.strategy_input.addItems(self.controller.get_bot_current_strategy(bot_data))
        self.bot_name = botname
        self.bot_name_input.setText(botname)
        self.base_asset_input.addItem(self.controller.get_base_asset(bot_data))
        self.base_asset_input.addItems(self.controller.base_assets)
        self.quote_asset_input.setText(self.controller.get_quote_asset(bot_data))
        self.account_name.setText(self.controller.get_account(bot_data))
        self.amount_input.setValue(self.controller.get_target_amount(bot_data))
        self.center_price_input.setValue(self.controller.get_target_center_price(bot_data))

        center_price_automatic = self.controller.get_target_center_price_automatic(bot_data)
        if center_price_automatic:
            self.center_price_input.setEnabled(False)
            self.center_price_automatic_checkbox.setChecked(True)
        else:
            self.center_price_input.setEnabled(True)
            self.center_price_automatic_checkbox.setChecked(False)

        self.spread_input.setValue(self.controller.get_target_spread(bot_data))
        self.save_button.clicked.connect(self.handle_save)
        self.cancel_button.clicked.connect(self.reject)
        self.center_price_automatic_checkbox.stateChanged.connect(self.onchange_center_price_automatic_checkbox)

    def onchange_center_price_automatic_checkbox(self):
        checkbox = self.center_price_automatic_checkbox
        if checkbox.isChecked():
            self.center_price_input.setDisabled(True)
        else:
            self.center_price_input.setDisabled(False)

    def validate_bot_name(self):
        old_bot_name = self.bot_name
        bot_name = self.bot_name_input.text()
        return self.controller.is_bot_name_valid(bot_name, old_bot_name)

    def validate_asset(self, asset):
        return self.controller.is_asset_valid(asset)

    def validate_market(self):
        base_asset = self.base_asset_input.currentText()
        quote_asset = self.quote_asset_input.text()
        return base_asset.lower() != quote_asset.lower()

    def validate_form(self):
        error_text = ''
        base_asset = self.base_asset_input.currentText()
        quote_asset = self.quote_asset_input.text()

        if not self.validate_bot_name():
            bot_name = self.bot_name_input.text()
            error_text += 'Bot name needs to be unique. "{}" is already in use.\n'.format(bot_name)
        if not self.validate_asset(base_asset):
            error_text += 'Field "Base Asset" does not have a valid asset.\n'
        if not self.validate_asset(quote_asset):
            error_text += 'Field "Quote Asset" does not have a valid asset.\n'
        if not self.validate_market():
            error_text += "Market {}/{} doesn't exist.\n".format(base_asset, quote_asset)

        if error_text:
            dialog = NoticeDialog(error_text)
            dialog.exec_()
            return False
        else:
            return True

    @staticmethod
    def handle_save_dialog():
        dialog = ConfirmationDialog('Saving the bot will cancel all the current orders.\n'
                                    'Are you sure you want to save the bot?')
        return dialog.exec_()

    def handle_save(self):
        if not self.validate_form():
            return

        if not self.handle_save_dialog():
            return

        spread = float(self.spread_input.text()[:-1])  # Remove the percentage character from the end
        target = {
            'amount': float(self.amount_input.text()),
            'center_price': float(self.center_price_input.text()),
            'center_price_automatic': bool(self.center_price_automatic_checkbox.isChecked()),
            'spread': spread
        }

        base_asset = self.base_asset_input.currentText()
        quote_asset = self.quote_asset_input.text()
        strategy = self.strategy_input.currentText()
        bot_module = self.controller.get_strategy_module(strategy)
        bot_data = {
            'account': self.account_name.text(),
            'market': '{}/{}'.format(quote_asset, base_asset),
            'module': bot_module,
            'strategy': strategy,
            'target': target
        }
        self.bot_name = self.bot_name_input.text()
        self.controller.add_bot_config(self.bot_name, bot_data)
        self.accept()
