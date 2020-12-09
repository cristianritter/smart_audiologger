import requests

stream_url = 'http://177809y.ha.azioncdn.net/primary/atl_cri.sdp/playlist.m3u8'

r = requests.get(stream_url, stream=True)

with open('stream.mp3', 'wb') as f:
    try:
        for block in r.iter_content(1024):
            f.write(block)
    except Exception as err:
        print(err)