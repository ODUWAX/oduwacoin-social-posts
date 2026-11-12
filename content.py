"""Content bank for OduwaCoin Instagram autopost.

Each entry: theme, kicker, headline, body, cta, url, caption.
Captions get the shared hashtag + disclaimer footer appended in make_caption().
Price posts are generated from live CoinGecko data (see generate.py).
"""

THEMES = ["staking", "oduwapay", "education", "price"]

HASHTAGS = {
    "staking": "#OduwaCoin #OWC #Staking #PassiveIncome #Crypto #Blockchain #AfricaTech",
    "oduwapay": "#OduwaPay #OduwaCoin #OWC #CryptoWallet #GiftCard #Crypto #USDT",
    "education": "#OduwaCoin #OWC #Blockchain #Layer1 #AfricanBlockchain #Web3 #CryptoEducation",
    "price": "#OduwaCoin #OWC #CryptoPrice #Crypto #Blockchain #AfricaTech",
}

DISCLAIMER = "Crypto involves risk. Nothing here is financial advice."

POSTS = {
    "staking": [
        dict(kicker="ODUWA STAKING POOL", headline="Put your OWC\nto work", body="Stake OduwaCoin in the Oduwa Staking Pool and earn rewards on the coins you already hold.",
             cta="Start staking", url="oduwastakingpool.com",
             caption="Your OWC can do more than sit in a wallet. Stake it in the Oduwa Staking Pool and earn rewards on what you already hold.\n\nSign up at oduwastakingpool.com (link in bio)."),
        dict(kicker="HOLD. STAKE. GROW.", headline="Holding OWC?\nStake it.", body="Join the Oduwa Staking Pool in minutes. Deposit OWC, track rewards from your dashboard.",
             cta="Join the pool", url="oduwastakingpool.com",
             caption="Holding OduwaCoin? Make it work for you. Deposit OWC into the Oduwa Staking Pool and track your rewards right from your member dashboard.\n\nJoin at oduwastakingpool.com"),
        dict(kicker="SECURE BY DESIGN", headline="Staking with\nlogin protection", body="Every login is verified with an authenticator or emailed code to keep your account safe.",
             cta="Create your account", url="oduwastakingpool.com",
             caption="Security first. Oduwa Staking Pool verifies every login with Google Authenticator or a one-time code sent to your email.\n\nCreate your account at oduwastakingpool.com"),
        dict(kicker="NEW TO STAKING?", headline="3 steps to\nstart earning", body="1. Create an account\n2. Deposit OWC\n3. Watch your rewards grow",
             cta="Get started", url="oduwastakingpool.com",
             caption="New to staking? It takes three steps:\n1. Create your Oduwa Staking Pool account\n2. Deposit OWC\n3. Track your rewards from the dashboard\n\nStart at oduwastakingpool.com"),
        dict(kicker="NO OWC YET?", headline="Buy OWC with USDT,\nthen stake it", body="Buy OduwaCoin with USDT on oduwacoin.io and move it straight into the staking pool.",
             cta="Buy OWC with USDT", url="oduwacoin.io/gift#buy",
             caption="Don't have OWC yet? Buy OduwaCoin with USDT at oduwacoin.io, then stake it in the Oduwa Staking Pool to start earning rewards.\n\nBuy: oduwacoin.io/gift#buy\nStake: oduwastakingpool.com"),
        dict(kicker="REFER A FRIEND", headline="Stake together,\ngrow together", body="Invite friends to the Oduwa Staking Pool with your referral link from the member area.",
             cta="Share your link", url="oduwastakingpool.com",
             caption="Growth is better together. Share your referral link from the Oduwa Staking Pool member area and bring your friends into the OWC community.\n\noduwastakingpool.com"),
    ],
    "oduwapay": [
        dict(kicker="ODUWAPAY", headline="The official\nOWC wallet", body="Send, receive and hold OduwaCoin with OduwaPay. Just Oduwa It.",
             cta="Open OduwaPay", url="oduwapay.com",
             caption="OduwaPay is the official wallet for OduwaCoin. Send, receive and hold OWC in one place.\n\nJust Oduwa It. oduwapay.com"),
        dict(kicker="OWC GIFT VOUCHERS", headline="Give the gift\nof OduwaCoin", body="Create a printable OWC gift voucher in your browser. Fund it, print it, gift it.",
             cta="Create a gift", url="oduwacoin.io/gift",
             caption="Looking for a gift that stands out? Create a printable OduwaCoin gift voucher right in your browser. Fund it with OWC or USDT, print it and hand it over.\n\noduwacoin.io/gift"),
        dict(kicker="BUY OWC", headline="Buy OWC\nwith USDT", body="Pay with USDT on oduwacoin.io. OWC is sent automatically once your payment confirms.",
             cta="Buy now", url="oduwacoin.io/gift#buy",
             caption="Buying OduwaCoin is simple: pay with USDT at oduwacoin.io and your OWC is delivered automatically once the payment confirms.\n\nPrices come from CoinGecko. oduwacoin.io/gift#buy"),
        dict(kicker="FOR EVERY OCCASION", headline="Birthdays. Holidays.\nThank-yous.", body="OWC gift vouchers include a balance QR code and simple claim instructions.",
             cta="Make a voucher", url="oduwacoin.io/gift",
             caption="Birthdays, holidays, thank-yous. An OWC gift voucher comes with a balance QR code and clear claim instructions, so anyone can receive crypto.\n\nCreate yours at oduwacoin.io/gift"),
        dict(kicker="GOT A VOUCHER?", headline="Check your\ngift balance", body="Scan the QR on your voucher or check the balance on oduwacoin.io/gift.",
             cta="Check balance", url="oduwacoin.io/gift",
             caption="Received an OduwaCoin gift voucher? Scan its QR code or check the balance at oduwacoin.io/gift. Never share the private key printed inside.\n\noduwacoin.io/gift"),
        dict(kicker="JUST ODUWA IT", headline="Your OWC,\nalways with you", body="OduwaPay on web and mobile keeps your OduwaCoin within reach.",
             cta="Get OduwaPay", url="oduwapay.com",
             caption="Keep your OduwaCoin within reach on web and mobile with OduwaPay, the official OWC wallet.\n\nJust Oduwa It. oduwapay.com"),
    ],
    "education": [
        dict(kicker="WHAT IS ODUWACOIN?", headline="A Pan-African\nLayer 1 blockchain", body="OduwaCoin runs its own blockchain network, not a token on someone else's chain.",
             cta="Learn more", url="oduwacoin.io",
             caption="What is OduwaCoin? OWC is a Pan-African Layer 1 blockchain. It runs its own network and its own coin, not a token borrowed from another chain.\n\nLearn more at oduwacoin.io"),
        dict(kicker="LAYER 1 EXPLAINED", headline="What does\n\"Layer 1\" mean?", body="A Layer 1 is a base blockchain with its own nodes, consensus and native coin.",
             cta="Explore OWC", url="oduwacoin.io",
             caption="Layer 1 explained: a base blockchain that has its own nodes, its own consensus rules and its own native coin. OduwaCoin is one of them, built with Africa in mind.\n\noduwacoin.io"),
        dict(kicker="OPEN SOURCE", headline="Built in\nthe open", body="OduwaCoin Core's code is public on GitHub for anyone to review.",
             cta="View the code", url="github.com/ODUWAX/oduwacoin",
             caption="Transparency matters. OduwaCoin Core, the network's reference wallet and node software, is open source on GitHub for anyone to review.\n\ngithub.com/ODUWAX/oduwacoin"),
        dict(kicker="LATEST RELEASE", headline="OduwaCoin Core\nETINOSA v2.0.0.3", body="A cross-platform update that modernizes the wallet while keeping the network's protocol intact.",
             cta="Download", url="oduwacoin.io",
             caption="OduwaCoin Core ETINOSA v2.0.0.3 is a cross-platform modernization of the OWC wallet and node, keeping the network's consensus and protocol unchanged.\n\nGet it via oduwacoin.io"),
        dict(kicker="SEE IT ON CHAIN", headline="Every OWC transaction\nis public", body="Look up blocks, addresses and transactions on the OduwaCoin explorer.",
             cta="Open the explorer", url="oduwaexplorer.com",
             caption="Blockchains are transparent. Look up any OWC block, address or transaction on the OduwaCoin explorer.\n\noduwaexplorer.com"),
        dict(kicker="SECURITY TIP", headline="Never share your\nprivate key", body="Your private key controls your coins. No real support team will ever ask for it.",
             cta="Stay safe", url="oduwacoin.io",
             caption="Security tip: your private key controls your coins. No legitimate OduwaCoin support team will ever ask for it. If someone does, it's a scam.\n\noduwacoin.io"),
        dict(kicker="WHY AFRICA?", headline="Blockchain built\nfor Africa", body="OduwaCoin aims to bring fast, borderless value transfer to African communities and the diaspora.",
             cta="Join the community", url="oduwacoin.io",
             caption="Why a Pan-African blockchain? OduwaCoin aims to make value transfer fast and borderless for African communities and the diaspora worldwide.\n\noduwacoin.io"),
    ],
}

PRICE_CAPTIONS = [
    "OduwaCoin price update: 1 OWC = {usd} (CoinGecko, {date}).\n\nBuy OWC with USDT at oduwacoin.io/gift#buy or stake it at oduwastakingpool.com",
    "Today's OWC price: {usd} per coin, sourced from CoinGecko on {date}.\n\nReady to hold some? oduwacoin.io/gift#buy",
    "OWC market check for {date}: {usd} per OduwaCoin (CoinGecko).\n\nGrow your OWC in the Oduwa Staking Pool: oduwastakingpool.com",
]


def make_caption(theme, body):
    return f"{body}\n\n{DISCLAIMER}\n\n{HASHTAGS[theme]}"
