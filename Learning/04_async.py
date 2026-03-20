import asyncio
from time import sleep

# create event loop instance
loop = asyncio.get_event_loop()

async def hello():
    for i in range(10):
        print("Hello")
        await asyncio.sleep(3)
        # hello() est suspendu et le CPU cherche 
        # une autre fonction a run sur le thread
        print("Word !")
    

if __name__ == "__main__":
    # run hello function in the event loop
    loop.run_until_complete(hello())