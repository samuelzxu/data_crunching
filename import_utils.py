import json
import requests
from tqdm import tqdm
from datetime import datetime
import asyncio
import aiohttp
from tqdm.asyncio import tqdm as atqdm


def parse_import(filename, ver='_1'):
    with open(filename) as f:
        data = json.load(f)
    assert len(set(data['relationsById'].keys()).union(data['nodesById'].keys())) == len(data['relationsById']) + len(data['nodesById'])
    connections = []
    for id, item in data['relationsById'].items():
        connections.append({
            'source': item['fromId']+ver,
            'target': item['toId']+ver,
            'cid': id+ver,
            'label': "" if item["relationTypeId"] == "child" else item["relationTypeId"]
        })

    nodes = []
    for id, item in data['nodesById'].items():
        content = ''.join(map(lambda x: x['value'], item['content']))
        nodes.append({
            'id': id+ver,
            'content': content
        })
    
    return data, nodes, connections

auth = "TOKEN_HERE"

headers = {
    "accept": "application/json",
    "accept-encoding": "gzip, deflate, br, zstd",
    "accept-language": "en-US,en;q=0.9",
    "authorization": auth,
    "content-type": "application/json",
    "origin": "https://v2.ideapad.io",
    "referer": "https://v2.ideapad.io/graph",
    "sec-ch-ua": '"Chromium";v="130", "Google Chrome";v="130", "Not?A_Brand";v="99"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Linux"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
}

def import_data(nodes, connections):
    chunk_size = 300
    url = "https://v2.ideapad.io/api/v1/boards/createIdeasAndConnections"
    now = datetime.now().isoformat()
    indices = list(range(0, len(nodes), chunk_size))
    # Do nodes first, then connections
    for i in tqdm(indices):
        print(f"Sending nodes {i} to {min(len(nodes),i + chunk_size)} of {len(nodes)}")
        r = requests.post(url, headers=headers, json={
        "boardClientId": "4b76beca-ee77-4cb1-b04a-fee057fa7298",
        "ideas": [
            {
            "clientId": n['id'],
            "userId": None,
            "title": n['content'],
            "likeCount": 0,
            "commentCount": 0,
            "colorId": None,
            "isDeleted": False,
            "anonymous": False,
            "status": "not-acknowledged",
            "attachedBoardClientId": None,
            "permissionsExplicitlySet": False,
            "createdAt": now,
            "updatedAt": now
            }
            for n in nodes[i:i+chunk_size]
        ],
        "connections": []})
        print(r.status_code)
    
    indices = list(range(0, len(connections), chunk_size))
    for i in tqdm(indices):
        print(f"Sending connections {i} to {min(len(connections),i + chunk_size)} of {len(connections)}")
        r = requests.post(url, headers=headers, json={
        "boardClientId": "4b76beca-ee77-4cb1-b04a-fee057fa7298",
        "ideas": [],
        "connections": [
            {
            "id": None,
            "clientId": c['cid'],
            "sourceIdeaClientId": c['source'],
            "targetIdeaClientId": c['target'],
            "labelText": c['label'],
            "colorId": None,
            "isDeleted": None,
            }
            for c in connections[i:i+chunk_size]
        ]})
        print(r.status_code)

async def delete_connection(session, cid, headers):
    url = f"https://v2.ideapad.io/api/v1/connections/{cid}"
    async with session.delete(url, headers=headers, json={}) as response:
        return response.status
    
async def delete_data(nodes, connections):
    # Delete ideas (nodes) is synchronous
    url = f"https://v2.ideapad.io/api/v1/ideas/"
    ids = list(map(lambda x: x['id'], nodes))

    chunk_size = 300
    indices = list(range(0, len(ids), chunk_size))
    for i in tqdm(indices):
        print(f"Deleting nodes {i} to {min(len(ids),i + chunk_size)} of {len(ids)}")
        r = requests.post(url, headers=headers, json = {"clientIds":ids[i:i+chunk_size]})
        print(r.status_code)

    # Create a semaphore to limit concurrent requests
    semaphore = asyncio.Semaphore(30)

    async def bounded_delete(session, cid, headers):
        async with semaphore:
            return await delete_connection(session, cid, headers)

    print("Deleting connections...")
    async with aiohttp.ClientSession() as session:
        tasks = [bounded_delete(session, c['cid'], headers) for c in connections]
        statuses = await atqdm.gather(*tasks)
        print(statuses)

