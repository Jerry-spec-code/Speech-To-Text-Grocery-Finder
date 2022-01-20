import asyncio
import base64
import json

import websockets
from flask import Flask, render_template, request, escape, Response

import aisleRead
from analyze import analyze
from configure import auth_key
from ingredients import getIngredients, getPrice
from stream import *

# the AssemblyAI endpoint we're going to hit
URL = "wss://api.assemblyai.com/v2/realtime/ws?sample_rate=16000"
app = Flask(__name__)


@app.route("/", methods=['GET', 'POST'])
def index():
    async def send_receive(trigger):
        print(f'Connecting websocket to url ${URL}')
        async with websockets.connect(
                URL,
                extra_headers=(("Authorization", auth_key),),
                ping_interval=5,
                ping_timeout=20
        ) as _ws:
            await asyncio.sleep(0.1)
            print("Receiving SessionBegins ...")
            session_begins = await _ws.recv()
            print(session_begins)
            print("Sending messages ...")

            async def send():
                first_run = True
                while True:
                    try:
                        if task.done():
                            return True
                        if first_run:
                            data = wav_header + stream.read(CHUNK)
                            first_run = False
                        else:
                            data = stream.read(CHUNK)
                        data = base64.b64encode(data).decode("utf-8")
                        json_data = json.dumps({"audio_data": str(data)})
                        await _ws.send(json_data)
                    except websockets.exceptions.ConnectionClosedError as e:
                        print(e)
                        assert e.code == 4008
                        break
                    except Exception as e:
                        assert False, "Not a websocket 4008 error"
                    await asyncio.sleep(0.01)

            async def receive():
                while True:
                    try:
                        result_str = await _ws.recv()
                        text = json.loads(result_str)['text']
                        print(text)
                        if trigger in text:
                            substring = analyze(text, trigger)
                            return substring
                    except websockets.exceptions.ConnectionClosedError as e:
                        print(e)
                        assert e.code == 4008
                        break
                    except Exception as e:
                        assert False, "Not a websocket 4008 error"

        task = asyncio.create_task(receive())
        send_result, substring = await asyncio.gather(send(), task)
        return substring

    if request.method == 'GET':
        print("get ingredients pressed")
        if 'get_ingredients' in request.args:
            item = str(escape(request.args.get("item", "")))
            if not item:
                return render_template("index.html", warning="Please enter a search term.")
        else:
            return render_template("index.html")
    else:
        print("voice input pressed")
        item = asyncio.run(send_receive("ingredients"))
    food_info = getIngredients(item)
    ingredients = food_info['ingredients']
    price_info = getPrice(ingredients)
    aisle_info = [aisleRead.find(k) for k in ingredients]

    return (
        render_template(
            "index.html",
            result=[[ingredients[i], price_info[i], aisle_info[i]] for i in range(len(price_info))],
            name="Ingredients for: " + food_info['name'],
            time="Approximate preparation time: " + food_info['time'],
            nutrition="Estimated Calories: " + food_info['nutrition'],
            scroll="info"
        )
    )


if __name__ == "__main__":
    app.run(debug=True)
