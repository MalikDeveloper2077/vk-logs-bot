from sys import exc_info

from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager as CDM

from fh import ULogAuth


if __name__ == "__main__":
	try:
		ULogClient = ULogAuth()
		ULogClient._auth()
		ULogClient.close_driver()

		CONFIRMATION_URL = input("Введите ссылку на подтверждение ip-адреса, которая пришла к вам на почту: ")
		driver = webdriver.Chrome(CDM().install())
		driver.get(CONFIRMATION_URL)
		driver.close()

		print("Confirmation was successful")

	except:
		print("Confirmation failed: ", exc_info()[1])
		exit()
