import requests
import discord
import asyncio
import json
import redis

r = redis.Redis(host='localhost', port=6379, db=0)

stored_ads = json.loads(r.get("ads")) if r.get("ads") is not None else []
trades = json.loads(r.get("trades")) if r.get("trades") is not None else []

def get_asset_name_rarity(assets_id):
    '''This func gets assets name and rarity from AtomicHub using assets_id as parameter'''
    url = 'https://wax.api.atomicassets.io/atomicassets/v1/assets/'
    params = {
        'asset_id': assets_id
    }
    ah_response = requests.get(url, params=params).json()
    data = ah_response.get('data')
    asset_name = ''
    asset_rarity = ''
    for item in data:
        asset_name = item.get('data').get('name')
        asset_rarity = item.get('data').get('rarity')
    return {'asset': asset_name, 'rarity': asset_rarity}


intents = discord.Intents.default()
client = discord.Client(intents=intents)

async def check_nfts():
    '''This func runs discord bot, checks API every 60 sec and if there is new NFT marstrader ad, sending message to Discord channel'''
    CHANNEL_ID = 'CHANNEL_ID'
    params = {
        'account_name': 'marstradergo',
        'offset': -20,
        'pos': -1
    }
    response = requests.get('https://wax.greymass.com/v1/history/get_actions', params=params).json()
    new_ads = response.get('actions')
    for new_ad in new_ads:
        name = new_ad.get('action_trace').get('act').get('name')
        to = new_ad.get('action_trace').get('act').get('data').get('to')
        memo = new_ad.get('action_trace').get('act').get('data').get('memo')
        if new_ad not in stored_ads and (name == 'transfer' and to == 'marstradergo' and memo == ''):
            stored_ads.append(new_ad)
            r.set("ads", json.dumps(stored_ads))
            channel = client.get_channel(CHANNEL_ID)
            asset_id = new_ad.get('action_trace').get('act').get('data').get('asset_ids')
            seller = new_ad.get('action_trace').get('act').get('data').get('from')
            trade_offer_msg = '{asset} rarity {rarity}\n'
            link = 'https://marstrader.io/#/nfts'
            msg = f':bangbang: **NEW LISTING** :bangbang:\n' \
                  f'\n' \
                  f':pushpin: **Wallet: {seller}**\n' \
                  f':pushpin: **Link** {link}'
            nfts = ''.join([f'{trade_offer_msg.format(asset=get_asset_name_rarity(id).get("asset"), rarity=get_asset_name_rarity(id).get("rarity"))}' for id in asset_id])
            text = f'{msg}\n```fix\n{nfts}for unknown NFT```\n' \
                   f'\n'
            await channel.send(text)


async def check_trades():
    '''This func runs discord bot, checks API every 60 sec and if there is new Resourse marstrader ad, sending message to Discord channel'''
    CHANNEL_ID = 'CHANNEL_ID'
    params = {
        'account_name': 'marstradergo',
        'offset': -20,
        'pos': -1
    }
    response = requests.get('https://wax.greymass.com/v1/history/get_actions', params=params).json()
    new_ads = response.get('actions')
    for new_ad in new_ads:
        name = new_ad.get('action_trace').get('act').get('name')
        account_action_seq = new_ad.get('account_action_seq')
        if account_action_seq not in trades and name == 'newtrade':
            trades.append(account_action_seq)
            r.set("trades", json.dumps(trades))
            supply_asset = new_ad.get('action_trace').get('act').get('data').get('asset1').get('asset')
            demand_asset = new_ad.get('action_trace').get('act').get('data').get('asset2').get('asset')
            seller = new_ad.get('action_trace').get('act').get('data').get('seller')
            link = 'https://marstrader.io/#/tokens'
            channel = client.get_channel(CHANNEL_ID)
            await channel.send(f":bangbang: **NEW LISTING** :bangbang:\n"
                               f"\n"
                               f':pushpin: **Link** {link}\n'
                               f'```fix\nWallet *{seller}* trades {supply_asset} for {demand_asset}```\n'
                               f'\n')


async def scheduled_task():
    while True:
        await check_nfts()
        await check_trades()
        await asyncio.sleep(60)

@client.event
async def on_ready():
    print('Bot is ready.')
    client.loop.create_task(scheduled_task())

client.run('YOUR_BOT_TOKEN')


