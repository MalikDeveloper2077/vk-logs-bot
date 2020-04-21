import random
from sys import exc_info

import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager as CDM

import config


class ULogAuth:
    """ULOG authorization class"""

    def __init__(self):
        self._login = config._ULOG_LOGIN
        self._passwd = config._ULOG_PASSWD

        self.driver = webdriver.Chrome(CDM().install())
        self.driver.get(config._ULOG_AUTH_URL)

        self.userInfoURL = config._ULOG_USER_INFO_URL

    def _auth(self) -> None:
        """Authorization method"""
        inputs = self.driver.find_elements_by_tag_name("input")

        mail_input = inputs[0]
        passwd_input = inputs[1]
        submit_button = inputs[2]

        mail_input.send_keys(self._login)
        passwd_input.send_keys(self._passwd)

        submit_button.click()

    def get_name(self):
        """Return the author username of logs"""
        name = self.driver.find_element_by_tag_name('h1')
        return name.text

    def get_logs(self, user_id) -> list:
        """Method that returns logs"""
        self.driver.get(self.userInfoURL.format(usr_id=user_id))

        logs = self.driver.find_elements_by_tag_name("li")
        last_seven_days_logs = []

        for log in logs:
            if "-" in log.text:
                last_seven_days_logs.append(log.text)

        return last_seven_days_logs[:7]

    def close_driver(self):
        self.driver.close()


class VkBot:
    """VK API class"""

    def __init__(self):
        self.ULogClient = ULogAuth()
        self.ULogClient._auth()

        self.vk = vk_api.VkApi(token=config._VK_BOT_TOKEN)
        self.longpoll = VkBotLongPoll(self.vk, config.VK_GROUP_ID)

    def send_user_message(self, user_id, message) -> bool:
        """Method that sends message for the user"""
        try:
            self.vk.method('messages.send', {
                'user_id': user_id,
                'message': message,
                'random_id': random.randint(545454, 999999)
            })
            return True
        except Exception:
            return False

    def send_chat_message(self, chat_id, message) -> bool:
        """Method that sends message to the chat"""
        try:
            self.vk.method('messages.send', {
                'chat_id': chat_id,
                'message': message,
                'random_id': random.randint(545454, 999999)
            })
            return True
        except Exception:
            return False

    def online_command(self, input_message, chat_id=None, user_id=None):
        """Handler for !online command.

        Send a message to a chat or a user.
        Define the method for send messages.
        If you want to use it for a chat you need to give chat_id argument
        Otherwise you need to give user_id arg.

        """
        if chat_id is not None:
            sending_id = chat_id
            send_method = self.send_chat_message
        elif user_id is not None:
            sending_id = user_id
            send_method = self.send_user_message
        else:
            raise ValueError('Please give the valid user or chat id')

        if input_message[:7].lower() == '!online':
            logs = self.ULogClient.get_logs(input_message[7:])
            name = self.ULogClient.get_name()

            if len(logs) > 0:
                message_to_client = f'Ник: {name}\n\n'
                message_to_client += '\n'.join(logs)
                send_method(sending_id, message_to_client)
            else:
                send_method(sending_id, config.USER_NOT_FOUND)
        else:
            if user_id is not None:
                self.send_user_message(user_id, config.INVALID_INPUT_MESSAGE)

    @staticmethod
    def check_for_kicking(action) -> bool:
        """Check if the action is leaving from a chat"""
        if action:
            return action['type'] == 'chat_kick_user'
        return False

    def kick(self, chat_id, user_id) -> None:
        """Kick an user from a chat"""
        print(chat_id, user_id)
        try:
            self.vk.method('messages.removeChatUser', {
                'chat_id': chat_id,
                'user_id': user_id
            })
        except:
            self.vk.method('messages.send', {
                'chat_id': chat_id,
                'message': 'У меня нет прав доступа для исключения участника.\nЧтобы исключить человека вам необходимо \
                выдать мне права администратора 🙃',
                'random_id': random.randint(545454, 999999)
            })

    def main_loop(self) -> None:
        """Main thread method"""
        for event in self.longpoll.listen():

            if event.type == VkBotEventType.MESSAGE_NEW:
                if event.object['message']['from_id'] != event.object['message']['peer_id']:
                    # The message is from a chat

                    # If a user left from a chat - kick him
                    action = event.obj['message'].get('action')
                    if self.check_for_kicking(action):
                        self.kick(event.chat_id, action['member_id'])

                    # !online command handler
                    print(event)
                    self.online_command(
                        input_message=event.object['message']['text'],
                        chat_id=event.chat_id
                    )
                else:
                    # The message is from a user
                    self.online_command(
                        input_message=event.object['message']['text'],
                        user_id=event.object['message'].get('from_id')
                    )


bot = VkBot()
bot.main_loop()
