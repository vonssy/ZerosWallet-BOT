from aiohttp import (
    ClientResponseError,
    ClientSession,
    ClientTimeout,
    FormData
)
from aiohttp_socks import ProxyConnector
from fake_useragent import FakeUserAgent
from datetime import datetime
from colorama import *
import asyncio, os, pytz

wib = pytz.timezone('Asia/Jakarta')

class ZerosWallet:
    def __init__(self) -> None:
        self.headers = {
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
            "Origin": "https://app.zeroswallet.com",
            "Referer": "https://app.zeroswallet.com/",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
            "User-Agent": FakeUserAgent().random
        }
        self.BASE_API = "https://api.zeroswallet.com"
        self.code = "ee1364ef82" # U can change it with yours.
        self.proxies = []
        self.proxy_index = 0
        self.account_proxies = {}

    def clear_terminal(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def log(self, message):
        print(
            f"{Fore.CYAN + Style.BRIGHT}[ {datetime.now().astimezone(wib).strftime('%x %X %Z')} ]{Style.RESET_ALL}"
            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}{message}",
            flush=True
        )

    def welcome(self):
        print(
            f"""
        {Fore.GREEN + Style.BRIGHT}Auto Claim {Fore.BLUE + Style.BRIGHT}Zeros Wallet - BOT
            """
            f"""
        {Fore.GREEN + Style.BRIGHT}Rey? {Fore.YELLOW + Style.BRIGHT}<INI WATERMARK>
            """
        )

    def format_seconds(self, seconds):
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"
    
    async def load_proxies(self, use_proxy_choice: int):
        filename = "proxy.txt"
        try:
            if use_proxy_choice == 1:
                async with ClientSession(timeout=ClientTimeout(total=30)) as session:
                    async with session.get("https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/all.txt") as response:
                        response.raise_for_status()
                        content = await response.text()
                        with open(filename, 'w') as f:
                            f.write(content)
                        self.proxies = content.splitlines()
            else:
                if not os.path.exists(filename):
                    self.log(f"{Fore.RED + Style.BRIGHT}File {filename} Not Found.{Style.RESET_ALL}")
                    return
                with open(filename, 'r') as f:
                    self.proxies = f.read().splitlines()
            
            if not self.proxies:
                self.log(f"{Fore.RED + Style.BRIGHT}No Proxies Found.{Style.RESET_ALL}")
                return

            self.log(
                f"{Fore.GREEN + Style.BRIGHT}Proxies Total  : {Style.RESET_ALL}"
                f"{Fore.WHITE + Style.BRIGHT}{len(self.proxies)}{Style.RESET_ALL}"
            )
        
        except Exception as e:
            self.log(f"{Fore.RED + Style.BRIGHT}Failed To Load Proxies: {e}{Style.RESET_ALL}")
            self.proxies = []

    def check_proxy_schemes(self, proxies):
        schemes = ["http://", "https://", "socks4://", "socks5://"]
        if any(proxies.startswith(scheme) for scheme in schemes):
            return proxies
        return f"http://{proxies}"

    def get_next_proxy_for_account(self, token):
        if token not in self.account_proxies:
            if not self.proxies:
                return None
            proxy = self.check_proxy_schemes(self.proxies[self.proxy_index])
            self.account_proxies[token] = proxy
            self.proxy_index = (self.proxy_index + 1) % len(self.proxies)
        return self.account_proxies[token]

    def rotate_proxy_for_account(self, token):
        if not self.proxies:
            return None
        proxy = self.check_proxy_schemes(self.proxies[self.proxy_index])
        self.account_proxies[token] = proxy
        self.proxy_index = (self.proxy_index + 1) % len(self.proxies)
        return proxy
    
    def mask_account(self, account):
        mask_account = account[:6] + '*' * 6 + account[-6:]
        return mask_account
        
    def print_question(self):
        while True:
            try:
                print(f"{Fore.WHITE + Style.BRIGHT}1. Run With Monosans Proxy{Style.RESET_ALL}")
                print(f"{Fore.WHITE + Style.BRIGHT}2. Run With Private Proxy{Style.RESET_ALL}")
                print(f"{Fore.WHITE + Style.BRIGHT}3. Run Without Proxy{Style.RESET_ALL}")
                choose = int(input(f"{Fore.BLUE + Style.BRIGHT}Choose [1/2/3] -> {Style.RESET_ALL}").strip())

                if choose in [1, 2, 3]:
                    proxy_type = (
                        "Run With Monosans Proxy" if choose == 1 else 
                        "Run With Private Proxy" if choose == 2 else 
                        "Run Without Proxy"
                    )
                    print(f"{Fore.GREEN + Style.BRIGHT}{proxy_type} Selected.{Style.RESET_ALL}")
                    break
                else:
                    print(f"{Fore.RED + Style.BRIGHT}Please enter either 1, 2 or 3.{Style.RESET_ALL}")
            except ValueError:
                print(f"{Fore.RED + Style.BRIGHT}Invalid input. Enter a number (1, 2 or 3).{Style.RESET_ALL}")

        rotate = False
        if choose in [1, 2]:
            while True:
                rotate = input(f"{Fore.BLUE + Style.BRIGHT}Rotate Invalid Proxy? [y/n] -> {Style.RESET_ALL}").strip()

                if rotate in ["y", "n"]:
                    rotate = rotate == "y"
                    break
                else:
                    print(f"{Fore.RED + Style.BRIGHT}Invalid input. Enter 'y' or 'n'.{Style.RESET_ALL}")

        return choose, rotate
    
    async def check_connection(self, proxy=None):
        connector = ProxyConnector.from_url(proxy) if proxy else None
        try:
            async with ClientSession(connector=connector, timeout=ClientTimeout(total=30)) as session:
                async with session.get(url=self.BASE_API, headers={}) as response:
                    response.raise_for_status()
                    return True
        except (Exception, ClientResponseError) as e:
            return None
            
    async def user_login(self, account: str, proxy=None, retries=5):
        url = f"{self.BASE_API}/login"
        data = FormData()
        data.add_field("uid", account)
        for attempt in range(retries):
            connector = ProxyConnector.from_url(proxy) if proxy else None
            try:
                async with ClientSession(connector=connector, timeout=ClientTimeout(total=60)) as session:
                    async with session.post(url=url, headers=self.headers, data=data) as response:
                        response.raise_for_status()
                        result = await response.json()
                        return result["token"]
            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                return None
            
    async def user_confirm(self, token: str, proxy=None, retries=5):
        url = f"{self.BASE_API}/addreferral"
        data = FormData()
        data.add_field("token", token)
        data.add_field("refcode", self.code)
        for attempt in range(retries):
            connector = ProxyConnector.from_url(proxy) if proxy else None
            try:
                async with ClientSession(connector=connector, timeout=ClientTimeout(total=60)) as session:
                    async with session.post(url=url, headers=self.headers, data=data) as response:
                        response.raise_for_status()
                        return await response.json()
            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                return None
            
    async def user_wallet(self, token: str, proxy=None, retries=5):
        url = f"{self.BASE_API}/auth/mywallet"
        data = FormData()
        data.add_field("token", token)
        for attempt in range(retries):
            connector = ProxyConnector.from_url(proxy) if proxy else None
            try:
                async with ClientSession(connector=connector, timeout=ClientTimeout(total=60)) as session:
                    async with session.post(url=url, headers=self.headers, data=data) as response:
                        response.raise_for_status()
                        return await response.json()
            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                return None
            
    async def task_pay(self, token: str, proxy=None, retries=5):
        url = f"{self.BASE_API}/taskpay"
        data = FormData()
        data.add_field("token", token)
        for attempt in range(retries):
            connector = ProxyConnector.from_url(proxy) if proxy else None
            try:
                async with ClientSession(connector=connector, timeout=ClientTimeout(total=60)) as session:
                    async with session.post(url=url, headers=self.headers, data=data) as response:
                        response.raise_for_status()
                        return await response.json()
            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                return None
            
    async def perform_checkin(self, token: str, proxy=None, retries=5):
        url = f"{self.BASE_API}/task"
        data = FormData()
        data.add_field("token", token)
        for attempt in range(retries):
            connector = ProxyConnector.from_url(proxy) if proxy else None
            try:
                async with ClientSession(connector=connector, timeout=ClientTimeout(total=60)) as session:
                    async with session.post(url=url, headers=self.headers, data=data) as response:
                        response.raise_for_status()
                        return await response.json()
            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                return None
            
    async def get_quiz(self, proxy=None, retries=5):
        url = f"{self.BASE_API}/quiz/get"
        for attempt in range(retries):
            connector = ProxyConnector.from_url(proxy) if proxy else None
            try:
                async with ClientSession(connector=connector, timeout=ClientTimeout(total=60)) as session:
                    async with session.post(url=url, headers=self.headers) as response:
                        response.raise_for_status()
                        return await response.json()
            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                return None
            
    async def check_quiz(self, token: str, answer: str, proxy=None, retries=5):
        url = f"{self.BASE_API}/quiz/check"
        data = FormData()
        data.add_field("token", token)
        data.add_field("answer", answer)
        for attempt in range(retries):
            connector = ProxyConnector.from_url(proxy) if proxy else None
            try:
                async with ClientSession(connector=connector, timeout=ClientTimeout(total=60)) as session:
                    async with session.post(url=url, headers=self.headers, data=data) as response:
                        response.raise_for_status()
                        return await response.json()
            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                return None
            
    async def process_check_connection(self, account: str, use_proxy: bool, rotate_proxy: bool):
        message = "Checking Connection, Wait..."
        if use_proxy:
            message = "Checking Proxy Connection, Wait..."

        print(
            f"{Fore.CYAN + Style.BRIGHT}[ {datetime.now().astimezone(wib).strftime('%x %X %Z')} ]{Style.RESET_ALL}"
            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
            f"{Fore.YELLOW + Style.BRIGHT}{message}{Style.RESET_ALL}",
            end="\r",
            flush=True
        )

        proxy = self.get_next_proxy_for_account(account) if use_proxy else None

        if rotate_proxy:
            is_valid = None
            while is_valid is None:
                is_valid = await self.check_connection(proxy)
                if not is_valid:
                    self.log(
                        f"{Fore.CYAN+Style.BRIGHT}Proxy   :{Style.RESET_ALL}"
                        f"{Fore.WHITE+Style.BRIGHT} {proxy} {Style.RESET_ALL}"
                        f"{Fore.MAGENTA+Style.BRIGHT}-{Style.RESET_ALL}"
                        f"{Fore.RED+Style.BRIGHT} Not 200 OK, {Style.RESET_ALL}"
                        f"{Fore.YELLOW+Style.BRIGHT}Rotating Proxy...{Style.RESET_ALL}"
                    )
                    proxy = self.rotate_proxy_for_account(account) if use_proxy else None
                    await asyncio.sleep(5)
                    continue

                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}Proxy   :{Style.RESET_ALL}"
                    f"{Fore.WHITE+Style.BRIGHT} {proxy} {Style.RESET_ALL}"
                    f"{Fore.MAGENTA+Style.BRIGHT}-{Style.RESET_ALL}"
                    f"{Fore.GREEN+Style.BRIGHT} 200 OK {Style.RESET_ALL}                  "
                )

                return True

        is_valid = await self.check_connection(proxy)
        if not is_valid:
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}Proxy   :{Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT} {proxy} {Style.RESET_ALL}"
                f"{Fore.MAGENTA+Style.BRIGHT}-{Style.RESET_ALL}"
                f"{Fore.RED+Style.BRIGHT} Not 200 OK {Style.RESET_ALL}          "
            )
            return False
        
        self.log(
            f"{Fore.CYAN+Style.BRIGHT}Proxy   :{Style.RESET_ALL}"
            f"{Fore.WHITE+Style.BRIGHT} {proxy} {Style.RESET_ALL}"
            f"{Fore.MAGENTA+Style.BRIGHT}-{Style.RESET_ALL}"
            f"{Fore.GREEN+Style.BRIGHT} 200 OK {Style.RESET_ALL}                  "
        )

        return True
        
    async def process_accounts(self, account: str, use_proxy: bool, rotate_proxy: bool):
        is_valid = await self.process_check_connection(account, use_proxy, rotate_proxy)
        if is_valid:
            proxy = self.get_next_proxy_for_account(account) if use_proxy else None
            
            token = await self.user_login(account, proxy)
            if not token:
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}Status  :{Style.RESET_ALL}"
                    f"{Fore.RED+Style.BRIGHT} Login Failed {Style.RESET_ALL}"
                )
                return

            self.log(
                f"{Fore.CYAN+Style.BRIGHT}Status  :{Style.RESET_ALL}"
                f"{Fore.GREEN+Style.BRIGHT} Login Success {Style.RESET_ALL}"
            )

            await self.user_confirm(token, proxy)

            wallet = await self.user_wallet(token, proxy)
            if wallet:
                coins = wallet.get("data", [])

                if coins:
                    self.log(f"{Fore.CYAN+Style.BRIGHT}Balance :{Style.RESET_ALL}")

                    for coin in coins:
                        balance = coin.get("balance")
                        coin_symbol = coin.get("coin_symbol")

                        self.log(
                            f"{Fore.MAGENTA+Style.BRIGHT}     ●{Style.RESET_ALL}"
                            f"{Fore.WHITE+Style.BRIGHT} {balance} {coin_symbol} {Style.RESET_ALL}"
                        )

                else:
                    self.log(
                        f"{Fore.CYAN+Style.BRIGHT}Balance :{Style.RESET_ALL}"
                        f"{Fore.YELLOW+Style.BRIGHT} Data Is None {Style.RESET_ALL}"
                    )
                
            else:
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}Balance :{Style.RESET_ALL}"
                    f"{Fore.RED+Style.BRIGHT} Data Is None {Style.RESET_ALL}"
                )

            task_pay = await self.task_pay(token, proxy)
            if task_pay:
                check_in = await self.perform_checkin(token, proxy)
                if check_in and check_in.get("success"):
                    self.log(
                        f"{Fore.CYAN+Style.BRIGHT}Check-In:{Style.RESET_ALL}"
                        f"{Fore.GREEN+Style.BRIGHT} Is Claimed {Style.RESET_ALL}"
                    )
                else:
                    self.log(
                        f"{Fore.CYAN+Style.BRIGHT}Check-In:{Style.RESET_ALL}"
                        f"{Fore.YELLOW+Style.BRIGHT} Already Claimed {Style.RESET_ALL}"
                    )
            else:
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}Check-In:{Style.RESET_ALL}"
                    f"{Fore.YELLOW+Style.BRIGHT} Claim Failed {Style.RESET_ALL}"
                )

            quiz = await self.get_quiz(proxy)
            if quiz:
                question = quiz.get("title", "N/A")
                answer = quiz.get("answer", "N/A")
                reward = quiz.get("reward", "N/A")

                self.log(f"{Fore.CYAN+Style.BRIGHT}Quiz    :{Style.RESET_ALL}")
                self.log(
                    f"{Fore.MAGENTA+Style.BRIGHT}     >{Style.RESET_ALL}"
                    f"{Fore.CYAN+Style.BRIGHT} Question: {Style.RESET_ALL}"
                    f"{Fore.WHITE+Style.BRIGHT}{question}{Style.RESET_ALL}"
                )
                self.log(
                    f"{Fore.MAGENTA+Style.BRIGHT}     >{Style.RESET_ALL}"
                    f"{Fore.CYAN+Style.BRIGHT} Answer  : {Style.RESET_ALL}"
                    f"{Fore.BLUE+Style.BRIGHT}{answer}{Style.RESET_ALL}"
                )
                
                check = await self.check_quiz(token, answer, proxy)
                if check:
                    is_success = check.get("success")
                    if is_success:
                        self.log(
                            f"{Fore.MAGENTA+Style.BRIGHT}     >{Style.RESET_ALL}"
                            f"{Fore.CYAN+Style.BRIGHT} Status  : {Style.RESET_ALL}"
                            f"{Fore.GREEN+Style.BRIGHT}Successfully Answered{Style.RESET_ALL}"
                            f"{Fore.MAGENTA+Style.BRIGHT} - {Style.RESET_ALL}"
                            f"{Fore.CYAN+Style.BRIGHT}Reward{Style.RESET_ALL}"
                            f"{Fore.WHITE+Style.BRIGHT} {reward} ZEROS Token {Style.RESET_ALL}"
                        )

                    else:
                        self.log(
                            f"{Fore.MAGENTA+Style.BRIGHT}     >{Style.RESET_ALL}"
                            f"{Fore.CYAN+Style.BRIGHT} Status  : {Style.RESET_ALL}"
                            f"{Fore.YELLOW+Style.BRIGHT}Already Answered{Style.RESET_ALL}"
                        )
                else:
                    self.log(
                        f"{Fore.MAGENTA+Style.BRIGHT}     >{Style.RESET_ALL}"
                        f"{Fore.CYAN+Style.BRIGHT} Status  : {Style.RESET_ALL}"
                        f"{Fore.RED+Style.BRIGHT}Failed To Send Answer{Style.RESET_ALL}"
                    )
            else:
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}Quiz    :{Style.RESET_ALL}"
                    f"{Fore.RED+Style.BRIGHT} GET Data Failed {Style.RESET_ALL}"
                )
        
    async def main(self):
        try:
            with open('accounts.txt', 'r') as file:
                accounts = [line.strip() for line in file if line.strip()]
            
            use_proxy_choice, rotate_proxy = self.print_question()

            while True:
                use_proxy = False
                if use_proxy_choice in [1, 2]:
                    use_proxy = True

                self.clear_terminal()
                self.welcome()
                self.log(
                    f"{Fore.GREEN + Style.BRIGHT}Account's Total: {Style.RESET_ALL}"
                    f"{Fore.WHITE + Style.BRIGHT}{len(accounts)}{Style.RESET_ALL}"
                )

                if use_proxy:
                    await self.load_proxies(use_proxy_choice)
                
                separator = "=" * 23
                for account in accounts:
                    if account:
                        self.log(
                            f"{Fore.CYAN + Style.BRIGHT}{separator}[{Style.RESET_ALL}"
                            f"{Fore.WHITE + Style.BRIGHT} {self.mask_account(account)} {Style.RESET_ALL}"
                            f"{Fore.CYAN + Style.BRIGHT}]{separator}{Style.RESET_ALL}"
                        )
                        await self.process_accounts(account, use_proxy, rotate_proxy)
                        await asyncio.sleep(3)

                self.log(f"{Fore.CYAN + Style.BRIGHT}={Style.RESET_ALL}"*68)
                seconds = 12 * 60 * 60
                while seconds > 0:
                    formatted_time = self.format_seconds(seconds)
                    print(
                        f"{Fore.CYAN+Style.BRIGHT}[ Wait for{Style.RESET_ALL}"
                        f"{Fore.WHITE+Style.BRIGHT} {formatted_time} {Style.RESET_ALL}"
                        f"{Fore.CYAN+Style.BRIGHT}... ]{Style.RESET_ALL}"
                        f"{Fore.WHITE+Style.BRIGHT} | {Style.RESET_ALL}"
                        f"{Fore.BLUE+Style.BRIGHT}All Accounts Have Been Processed.{Style.RESET_ALL}",
                        end="\r"
                    )
                    await asyncio.sleep(1)
                    seconds -= 1

        except FileNotFoundError:
            self.log(f"{Fore.RED}File 'accounts.txt' Not Found.{Style.RESET_ALL}")
            return
        except Exception as e:
            self.log(f"{Fore.RED+Style.BRIGHT}Error: {e}{Style.RESET_ALL}")
            raise e

if __name__ == "__main__":
    try:
        bot = ZerosWallet()
        asyncio.run(bot.main())
    except KeyboardInterrupt:
        print(
            f"{Fore.CYAN + Style.BRIGHT}[ {datetime.now().astimezone(wib).strftime('%x %X %Z')} ]{Style.RESET_ALL}"
            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
            f"{Fore.RED + Style.BRIGHT}[ EXIT ] Zeros Wallet - BOT{Style.RESET_ALL}                                       "                              
        )