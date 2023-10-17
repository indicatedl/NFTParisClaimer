import random
import os
import concurrent.futures

from faker import Faker

from modules.mobileproxy import mobileProxy

from utils import *


def main(private_key, i):
    try:
        address = web3.eth.account.from_key(private_key).address
        if address in claimed_wallets:
            logger.info(f'{i}) Already claimed')
            return
        
        if MOBILE_PROXY != 'login:pass@ip:port':
            mobile = mobileProxy(MOBILE_PROXY, MOBILE_CHANGE_IP_LINK)
            while True:
                try:
                    mobile.change_ip()
                    logger.info(f'------- Successfully changed IP. Current IP - {mobile.get_ip_address()} ----------')
                    break
                except Exception as e:
                    print(e)
                    continue
            proxy = MOBILE_PROXY
        else:
            proxy = proxies[i]
            logger.info(f'------- Current IP - {proxy} ----------')

        logger.info(f'{i}) ---- Account: {address} ----')

        session = create_session(i)

        session.headers['authorization'] = get_session_token(proxy, session, private_key, i)
        if not session.headers['authorization']:
            return

        while True:
            fake = Faker()
            random_nickname = fake.user_name()
            if check_name(proxy, session, random_nickname, i):
                break

        if not check_referral(proxy, session, ref, i):
            return

        mint(proxy, session, ref, random_nickname, i)

        if not get_mint_status(proxy, session, i):
            return

        with open(file_claimed, 'a') as file:
            file.write(f'{address}\n')

        sleep(random.randint(MIN_SLEEP, MAX_SLEEP))

    except Exception as error:
        logger.error(f"{i}) Unexcepted error in main: {error}")



if (__name__ == '__main__'):

    with open(file_wallets, 'r') as file:
        wallets = [row.strip().split(':')[1] if ':' in row else row.strip() for row in file]

    if not os.path.isfile(file_claimed):
        open(file_claimed, 'w').close()
    with open(file_claimed, 'r') as file:
        claimed_wallets = [row.strip() for row in file]

    if MOBILE_PROXY == 'login:pass@ip:port':
        with open(file_proxies, 'r') as file:
            proxies = [row.strip() for row in file]
        while len(proxies) <= len(wallets):
            proxies.extend(proxies)
        
    with concurrent.futures.ThreadPoolExecutor(THREADS) as executor:
        for i, wallet in enumerate(wallets):
            executor.submit(
                main, wallet, i
            )

