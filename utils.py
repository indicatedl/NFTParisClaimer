from time import sleep
from sys import stderr

import tls_client
import ua_generator
from web3 import Web3
from loguru import logger
from eth_account.messages import encode_defunct

from config import *


# LOGGER SETTINGS
logger.remove()
logger.add(stderr, format="<white>{time:HH:mm:ss}</white> |<level>{level: <7}</level>| <white>{message}</white>")
logger.add(file_log, format="<white>{time:HH:mm:ss}</white> | <level>{level: <8}</level> | <white>{message}</white>")

web3 = Web3(Web3.HTTPProvider('https://rpc.ankr.com/polygon'))


def create_session(i):
    try:
        ua = ua_generator.generate(device='desktop', browser='chrome')
        headers = {
            'authority': 'nftparis.nftstudios.services',
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'ru,tr;q=0.9,ru-RU;q=0.8,en-US;q=0.7,en;q=0.6,zh-CN;q=0.5,zh;q=0.4',
            'cache-control': 'no-cache',
            'content-type': 'application/json',
            'origin': 'https://airdrop.nftparis.xyz',
            'pragma': 'no-cache',
            'referer': 'https://airdrop.nftparis.xyz/',
            'sec-ch-ua': f'"Google Chrome";v="112", "Not;A=Brand";v="8", "Chromium";v="112"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': f'"{ua.platform.title()}"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'cross-site',
            'user-agent': ua.text,
        }
        session = tls_client.Session(
                client_identifier="chrome112",
                random_tls_extension_order=True
            )
        session.headers = headers
        return session
    except Exception as error:
        logger.error(f"{i}) Unexcepted error in get_session_token: {error}")
        return


def get_session_token(proxy, session, private_key, i):
    while True:
        try:
            message = "Sign this message to login with your wallet"
            signature = web3.eth.account.sign_message(encode_defunct(text=message), private_key=private_key).signature.hex()

            data = {
                "signature": signature
            }

            resp = session.post('https://nft-paris-worker.nftstudios.workers.dev/sign-up', json=data, proxy=f'http://{proxy}')
            if resp.status_code != 200:
                if resp.status_code != 503:
                    if 'Wallet already used' in resp.text:
                        while True:
                            resp = session.post('https://nft-paris-worker.nftstudios.workers.dev/login', json=data, proxy=f'http://{proxy}')
                            if resp.status_code != 200:
                                if 'no balance' in resp.text:
                                    logger.error(f"{i}) No ETH mainnet TX/balance. Wallet rejected!")
                                    return False
                                sleep(3)
                                continue
                            break
                    elif 'no balance' in resp.text:
                        logger.error(f"{i}) No ETH mainnet TX/balance. Wallet rejected!")
                        return False
                    else:
                        logger.error(f"{i}) Error get_session_token request: {resp.status_code, resp.text}")
                        sleep(3)
                        continue
                else:
                    sleep(3)
                    continue
            if 'token' in resp.text:
                logger.success(f"{i}) Got session token")
                return resp.json()['token']
            else:
                logger.error(f"{i}) Error get_session_token: {resp.text}")
                return
        except Exception as error:
            logger.error(f"{i}) Unexcepted error in get_session_token: {error}")
            sleep(15)
            continue



def check_name(proxy, session, name, i):
    while True:
        try:
            resp = session.get(f'https://nftparis.nftstudios.services/check-name?name={name}', proxy=f'http://{proxy}')
            if resp.status_code != 200:
                if resp.status_code != 503:
                    logger.error(f"{i}) Error check_name request: {resp.status_code, resp.text}")
                sleep(3)
                continue
            if 'exists' in resp.text:
                exists = resp.json()['exists']
                if not exists:
                    logger.success(f"{i}) Name {name} is free")
                    return True
                else:
                    logger.error(f"{i}) Name {name} already taken")
                    return False
            else:
                logger.error(f"{i}) Error check_name: {resp.text}")
                return
        except Exception as error:
            logger.error(f"{i}) Unexcepted error in check_name: {error}")
            sleep(15)
            continue


def check_referral(proxy, session, referral, i):
    while True:
        try:
            resp = session.get(f'https://nftparis.nftstudios.services/check-referral?referral={referral}', proxy=f'http://{proxy}')
            if resp.status_code != 200:
                if resp.status_code != 503:
                    logger.error(f"{i}) Error check_referral request: {resp.status_code, resp.text}")
                sleep(3)
                continue
            if 'exists' in resp.text:
                exists = resp.json()['exists']
                if exists:
                    logger.success(f"{i}) Referral {referral} added")
                    return True
                else:
                    logger.error(f"{i}) Referral {referral} error")
                    return False
            else:
                logger.error(f"{i}) Error check_referral: {resp.text}")
                return
        except Exception as error:
            logger.error(f"{i}) Unexcepted error in check_referral: {error}")
            sleep(15)
            continue


def mint(proxy, session, referral, name, i):
    while True:
        try:
            data = {
                "referral": referral,
                "name": name
            }
            resp = session.post(f'https://nftparis.nftstudios.services/mint', json=data, proxy=f'http://{proxy}')
            if resp.status_code not in (200,201):
                if resp.status_code == 400 and 'already' in resp.text:
                    logger.success(f"{i}) Mint request has already send")
                    return
                elif resp.status_code != 503:
                    logger.error(f"{i}) Error mint request: {resp.status_code, resp.text}")
                sleep(3)
                continue
            logger.success(f"{i}) Mint request send")
            return
        except Exception as error:
            logger.error(f"{i}) Unexcepted error in mint: {error}")
            sleep(15)
            continue


def get_mint_status(proxy, session, i):
    while True:
        try:
            resp = session.get(f'https://nftparis.nftstudios.services/mint-status', proxy=f'http://{proxy}')
            if resp.status_code != 200:
                if resp.status_code != 503:
                    logger.error(f"{i}) Error get_mint_status request: {resp.status_code, resp.text}")
                sleep(3)
                continue
            if 'address' in resp.text:
                txHash = resp.json()['txHash'] if 'txHash' in resp.text else None
                logger.success(f"{i}) Mint info: {resp.json()['address']}, name {resp.json()['name']}, ref {resp.json()['referral']}, processed - {resp.json()['processed']}, confirmed - {resp.json()['confirmed']}, TX: {txHash} (need wait)")
                return True
            else:
                logger.error(f"{i}) Error get_mint_status: {resp.text}")
                return False
        except Exception as error:
            logger.error(f"{i}) Unexcepted error in get_mint_status: {error}")
            sleep(15)
            continue
